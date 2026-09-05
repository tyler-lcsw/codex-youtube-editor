"""Run a qualified local media provider in a locked, network-denied worker.

Example: python -m tools.media image --prompt-file prompt.txt --out image.png
"""
import argparse
from pathlib import Path
import requests
from .run_state import file_lock
from .runtime.worker import run_worker

ROOT=Path(__file__).resolve().parents[1]
PROVIDERS={
    'image':('image','tools.providers.image_klein'),
    'tts':('audio','tools.providers.tts_qwen'),
    'asr':('audio','tools.providers.asr_mlx'),
    'denoise':('denoise','tools.providers.denoise_deepfilter'),
}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('provider',choices=PROVIDERS);p.add_argument('args',nargs=argparse.REMAINDER)
    a=p.parse_args();env,module=PROVIDERS[a.provider];python=ROOT/'.envs'/env/'bin/python'
    if not python.is_file():p.error(f'Local {env} environment is absent; see docs/setup-macos.md')
    with file_lock(ROOT/'work/local-inference.lock'):
        try:
            r=requests.get('http://127.0.0.1:1235/api/v1/models',timeout=3);r.raise_for_status()
            if any(m.get('loaded_instances') for m in r.json().get('models',[])):
                p.error('Unload LM Studio models before a heavy media job; use lms unload <identifier>')
        except requests.ConnectionError:pass
        run_worker([str(python),'-m',module,*a.args],timeout=600,cwd=ROOT)


if __name__=='__main__':main()
