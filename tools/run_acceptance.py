"""Run bounded Codex acceptance prompts with durable attempt/failure receipts."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid
from .jobs import file_hash
from .run_state import atomic_json
from .runtime.worker import terminate_group

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'tests/acceptance/manifest.json'


def find_codex():
    for candidate in ('/Applications/ChatGPT.app/Contents/Resources/codex','/Applications/Codex.app/Contents/Resources/codex',shutil.which('codex')):
        if candidate and Path(candidate).is_file():return Path(candidate)
    raise FileNotFoundError('Codex CLI is unavailable; provide --codex explicitly')


def stop_group(process):
    if process is not None:terminate_group(process)


def run_acceptance(profile,model,fixture,output_dir,codex=None,timeout=360):
    manifest=json.loads(MANIFEST.read_text())
    if profile!=manifest['profile'] or model not in manifest['models'] or fixture not in manifest['fixtures']:
        raise ValueError('Unsupported acceptance profile, model or fixture')
    if not 0<timeout<=900:raise ValueError('Timeout must be in (0,900] seconds')
    cli=Path(codex) if codex else find_codex()
    prompt=MANIFEST.parent/manifest['fixtures'][fixture]['prompt']
    folder=Path(output_dir).resolve()/(fixture+'-'+model+'-'+uuid.uuid4().hex[:12]);folder.mkdir(parents=True)
    report=folder/'report.md';receipt_path=folder/'receipt.json'
    started=time.monotonic()
    receipt={'schema_version':1,'profile':profile,'model':model,'fixture':fixture,'status':'running','quality_approved':False,
        'started_at':datetime.now(timezone.utc).isoformat(),'prompt_sha256':file_hash(prompt),
        'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'dirty_checkout':bool(subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True)),
        'codex':str(cli),'report':str(report),'receipt':str(receipt_path),'stdout':str(folder/'events.jsonl'),'stderr':str(folder/'stderr.log'),
        'review_criteria':manifest['fixtures'][fixture]['review']}
    atomic_json(receipt_path,receipt)
    process=None
    with open(receipt['stdout'],'w') as stdout,open(receipt['stderr'],'w') as stderr:
        try:
            version=subprocess.run([str(cli),'--version'],capture_output=True,text=True,timeout=5,check=True)
            receipt['cli_version']=version.stdout.strip()
            command=[str(cli),'exec','--ephemeral','--sandbox','read-only','-m',model,'--json','-o',str(report),'-']
            process=subprocess.Popen(command,cwd=ROOT,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,text=True,start_new_session=True)
            process.communicate(prompt.read_text(),timeout=timeout)
            receipt['exit_code']=process.returncode
            receipt['status']='completed_unreviewed' if process.returncode==0 and report.is_file() and report.stat().st_size else 'failed'
            if report.is_file():receipt['report_sha256']=file_hash(report)
        except subprocess.TimeoutExpired:
            stop_group(process);receipt['status']='timed_out'
        except KeyboardInterrupt:
            stop_group(process);receipt['status']='cancelled'
        except Exception as error:
            stop_group(process);receipt.update(status='failed',error_type=type(error).__name__)
            stderr.write(str(error)+'\n')
        finally:
            receipt['elapsed_s']=time.monotonic()-started
            receipt['completed_at']=datetime.now(timezone.utc).isoformat()
            atomic_json(receipt_path,receipt)
    return receipt


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile',default='codex');p.add_argument('--model',required=True)
    p.add_argument('--fixture',default='discovery');p.add_argument('--output-dir',type=Path,default=ROOT/'work/acceptance')
    p.add_argument('--codex',type=Path);p.add_argument('--timeout',type=float,default=360)
    a=p.parse_args();receipt=run_acceptance(a.profile,a.model,a.fixture,a.output_dir,a.codex,a.timeout)
    print(json.dumps(receipt,indent=2))
    if receipt['status']!='completed_unreviewed':raise SystemExit(1)


if __name__=='__main__':main()
