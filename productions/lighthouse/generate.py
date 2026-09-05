"""Explicit local production recipe. Run from repository root; no hosted fallback."""
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tools.jobs import file_hash
from tools.voice_script import parse_voice_script
P=ROOT/'videos/lighthouse';A=ROOT/'media/projects/lighthouse';S=Path(__file__).parent

def run(*args):
    subprocess.run([str(x) for x in args],cwd=ROOT,check=True)

def main():
    mode=sys.argv[1]
    models=json.loads((ROOT/'config/models.lock.json').read_text())['models']
    if mode=='images':
        for image in json.loads((S/'images.json').read_text()):
            out=A/(image['id']+'.png');prompt=A/(image['id']+'.txt');prompt.write_text(image['prompt'])
            receipt=out.with_suffix('.provenance.json')
            if out.exists() and receipt.exists() and json.loads(receipt.read_text())['artifact']['sha256']==file_hash(out):
                prior=json.loads(receipt.read_text())
                expected_refs=[file_hash(A/(image['ref']+'.png'))] if image.get('ref') else []
                if prior['model']['revision']!=models['image_klein']['revision'] or prior['prompt']!=image['prompt'] or prior['seed']!=image['seed'] or [r['sha256'] for r in prior['references']]!=expected_refs:
                    raise RuntimeError('Changed image request needs a new output name; preserve the successful take')
                continue
            cmd=[ROOT/'.venv/bin/python','-m','tools.media','image','--prompt-file',prompt,'--out',out,'--seed',str(image['seed'])]
            if image.get('ref'):cmd+=['--ref',A/(image['ref']+'.png')]
            run(*cmd)
    elif mode=='voice':
        for beat in json.loads((S/'spec.json').read_text())['beats']:
            out=A/(beat.get('audio_asset',beat['id'])+'.wav');receipt=out.with_suffix('.provenance.json')
            if out.exists() and receipt.exists() and json.loads(receipt.read_text())['artifact']['sha256']==file_hash(out):
                prior=json.loads(receipt.read_text())
                parts=[{k:v for k,v in part.items() if k not in {'start_sample','end_sample'}} for part in prior['segments']]
                if prior['model']['revision']!=models['tts']['revision'] or prior['reference']['transcript']!=(S/'reference.txt').read_text() or parts!=parse_voice_script((S/(beat['id']+'.txt')).read_text()) or prior['seed']!=beat.get('seed',42) or prior['reference']['sha256']!=file_hash(ROOT/'work/benchmarks/speech.wav'):
                    raise RuntimeError('Changed voice request needs a new output name; preserve the successful take')
                continue
            run(ROOT/'.venv/bin/python','-m','tools.media','tts','--text-file',S/(beat['id']+'.txt'),'--ref-audio',ROOT/'work/benchmarks/speech.wav','--ref-text',S/'reference.txt','--out',out,'--seed',str(beat.get('seed',42)))
    else:raise SystemExit('Use images or voice')
if __name__=='__main__':main()
