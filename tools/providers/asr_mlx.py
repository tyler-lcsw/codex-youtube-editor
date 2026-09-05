"""Offline Qwen recognition and forced alignment in the isolated MLX environment."""
import argparse
import dataclasses
import json
import os
import time
from pathlib import Path
from ..jobs import file_hash
from ..run_state import atomic_json
from ..transcripts import attach_alignment

ROOT=Path(__file__).resolve().parents[2]

def model_path(key: str) -> Path:
    lock=json.loads((ROOT/'config/models.lock.json').read_text())['models'][key]
    path=(ROOT/lock['path']).resolve()
    for name,digest in lock['files'].items():
        p=path/name
        if not p.is_file() or file_hash(p)!=digest:
            raise RuntimeError(f'Model {key} missing or changed: {name}; restore the pinned model before inference')
    return path

def transcribe_and_align(audio: Path, language: str | None, keyterms: list[str], out: Path) -> dict:
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
    import mlx.core as mx
    import numpy as np
    from mlx_audio.stt.utils import load_model, load_audio
    t=time.monotonic(); samples=np.asarray(load_audio(str(audio)))
    sr=16000; step=20*sr; margin=2*sr
    asr=load_model(str(model_path('asr')))
    recognized=[]
    for start in range(0,len(samples),step):
        left=max(0,start-margin);right=min(len(samples),start+step+margin)
        r=asr.generate(samples[left:right],language=language,max_tokens=1024,hotwords=keyterms,verbose=False)
        recognized.append({'start':start,'left':left,'right':right,'result':dataclasses.asdict(r)})
    del asr;mx.clear_cache()
    aligner=load_model(str(model_path('aligner')))
    words=[];raw=[]
    for chunk in recognized:
        text=chunk['result']['text']; lang=language or chunk['result'].get('language') or 'English'
        if isinstance(lang,list):lang=lang[0] if lang else 'English'
        if not text.strip(): continue
        alignment=aligner.generate(samples[chunk['left']:chunk['right']],text=text,language=lang)
        aligned=[{'text':w.text,'start':w.start_time,'end':w.end_time} for w in alignment.items]
        normalized=attach_alignment(text,aligned)
        for w in normalized:
            if w['start'] is not None:
                w['start']+=round(chunk['left']/sr*1000);w['end']+=round(chunk['left']/sr*1000)
                middle=(w['start']+w['end'])/2
                if not chunk['start']/sr*1000<=middle<min(len(samples),chunk['start']+step)/sr*1000:continue
                if w['end']==w['start']:w['needs_review']=True
            w.update(id=f'{audio.stem}:{len(words)}',clip_id=audio.stem)
            words.append(w)
        raw.append({'chunk':chunk,'alignment':dataclasses.asdict(alignment)})
    result={'schema_version':1,'status':'completed','words':words,'text':' '.join(w['text'] for w in words),
            'language':language,'provider':'qwen_mlx','input_sha256':file_hash(audio),
            'metrics':{'elapsed_s':time.monotonic()-t,'peak_memory_bytes':mx.get_peak_memory(),'audio_duration_s':len(samples)/sr},
            'models':{k:{x:v[x] for x in ('repo','revision')} for k,v in json.loads((ROOT/'config/models.lock.json').read_text())['models'].items() if k in {'asr','aligner'}}}
    atomic_json(out.with_suffix('.provider.json'),{'chunks':raw})
    atomic_json(out,result)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--audio',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--language');p.add_argument('--keyterms',type=Path);a=p.parse_args()
    terms=a.keyterms.read_text().splitlines() if a.keyterms and a.keyterms.exists() else []
    r=transcribe_and_align(a.audio,a.language,[t for t in terms if t and not t.startswith('#')],a.out)
    print(json.dumps({'words':len(r['words']),'metrics':r['metrics']}))
