"""Explicit PAIR engine load, serialized with the project's media jobs."""
import argparse
import json
import subprocess
from pathlib import Path
import requests
from .run_state import file_lock, atomic_json
from .providers.local_llm import require_loaded
ROOT=Path(__file__).resolve().parents[1]

def inventory():
    r=requests.get('http://127.0.0.1:1235/api/v1/models',timeout=5);r.raise_for_status();return r.json()

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('model',choices=['qwen3.5-4b','qwen3.5-9b']);a=p.parse_args()
    lms=Path.home()/'.lmstudio/bin/lms'
    with file_lock(ROOT/'work/local-inference.lock'):
        if any(m.get('loaded_instances') for m in inventory()['models']):p.error('Unload existing models first')
        subprocess.run([str(lms),'load',a.model,'--identifier',a.model,'--context-length','4096','--parallel','1','--ttl','600','--yes'],check=True,timeout=120)
        data=inventory()
        try:require_loaded(data,a.model)
        except Exception:
            subprocess.run([str(lms),'unload',a.model],check=False);raise
        instance=next(i for m in data['models'] for i in m.get('loaded_instances',[]) if i['id']==a.model)
        atomic_json(ROOT/f'work/benchmarks/{a.model}-load.json',{'model':a.model,'requested_context':4096,'actual':instance})
        print(json.dumps(instance,indent=2))
        if instance['config']['context_length']!=4096:print('Context override ignored: use bounded requests; this is not a 4K engine cap.')

if __name__=='__main__':main()
