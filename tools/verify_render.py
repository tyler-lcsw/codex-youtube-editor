"""Extract and independently transcribe the exact manifest master, then verify it."""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from .jobs import file_hash
from .run_state import atomic_json
ROOT=Path(__file__).resolve().parents[1]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('project');p.add_argument('--style',required=True);a=p.parse_args()
    project=(ROOT/a.project).resolve();manifest=json.loads((project/'work/render-manifest.json').read_text())
    master=Path(manifest['master']);digest=file_hash(master)
    if digest!=manifest['master_sha256']:raise ValueError('Master changed since render; regenerate mapping')
    audio=project/'work/audio/render-verification.wav';out=project/'work/transcripts/render-verification.json'
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(master),'-vn','-ar','16000','-ac','1',str(audio)],check=True)
    subprocess.run([sys.executable,'-m','tools.media','asr','--audio',str(audio),'--out',str(out),'--language','English'],cwd=ROOT,check=True)
    if file_hash(master)!=digest:raise ValueError('Master changed during verification; retry')
    result=json.loads(out.read_text());result['source_media_sha256']=digest;atomic_json(out,result)
    subprocess.run([sys.executable,str(ROOT/'tools/verify_cut.py'),str(project),'--rendered','render-verification','--style',a.style],check=True)

if __name__=='__main__':main()
