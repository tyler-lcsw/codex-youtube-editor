"""Offline short-beat Qwen TTS with explicit reference and sample-counted pauses."""
import argparse
import json
import os
import time
from pathlib import Path
from .asr_mlx import model_path
from ..jobs import file_hash
from ..run_state import atomic_json
from ..voice_script import parse_voice_script


def validate_voice_request(text, reference, reference_text):
    if reference is None or not Path(reference).is_file() or not reference_text.strip():
        raise ValueError('Explicit voice reference audio and its transcript are required')
    if not text.strip() or len(text)>1000:raise ValueError('Use short voice beats of 1–1000 characters')
    return parse_voice_script(text)


def generate(text, reference: Path, reference_text, output: Path, language='english', seed=42):
    parts=validate_voice_request(text,reference,reference_text)
    import mlx.core as mx
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load_model
    info=sf.info(reference)
    if not 1<=info.duration<=30:raise ValueError('Use a clear voice reference between 1 and 30 seconds')
    mx.set_memory_limit(12*1024**3);mx.set_cache_limit(512*1024**2);mx.random.seed(seed)
    t=time.monotonic();model=load_model(str(model_path('tts')));sr=model.sample_rate
    chunks=[];segments=[];offset=0
    for part in parts:
        if 'silence_ms' in part:
            data=np.zeros(round(part['silence_ms']*sr/1000),dtype=np.float32)
        else:
            generated=list(model.generate(text=part['text'],ref_audio=str(reference),ref_text=reference_text,
                lang_code=language,max_tokens=1024))
            if not generated:raise RuntimeError('TTS returned no audio')
            if any(c.token_count>=1024 for c in generated):raise RuntimeError('TTS reached its token limit; split the beat')
            data=np.concatenate([np.asarray(c.audio).reshape(-1) for c in generated])
        if not np.isfinite(data).all():raise RuntimeError('TTS generated non-finite samples')
        segments.append({**part,'start_sample':offset,'end_sample':offset+len(data)});offset+=len(data);chunks.append(data)
    if not chunks:raise ValueError('Script contains no speech or pause')
    audio=np.concatenate(chunks)
    output.parent.mkdir(parents=True,exist_ok=True);tmp=output.with_name(output.stem+'.partial.wav')
    try:
        sf.write(tmp,audio,sr,subtype='PCM_16');os.replace(tmp,output)
    finally:tmp.unlink(missing_ok=True)
    receipt={'provider':'qwen_tts_mlx','model_key':'tts','seed':seed,'language':language,
        'reference':{'path':str(reference.resolve()),'sha256':file_hash(reference),'transcript':reference_text},
        'artifact':{'path':str(output.resolve()),'sha256':file_hash(output),'sample_rate':sr,'samples':len(audio)},
        'segments':segments,'metrics':{'elapsed_s':time.monotonic()-t,'peak_mlx_bytes':mx.get_peak_memory()}}
    model_spec=json.loads((Path(__file__).resolve().parents[2]/'config/models.lock.json').read_text())['models']['tts']
    receipt['model']={k:model_spec[k] for k in ('repo','revision','license')}
    atomic_json(output.with_suffix('.provenance.json'),receipt);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--text-file',type=Path,required=True);p.add_argument('--ref-audio',type=Path,required=True)
    p.add_argument('--ref-text',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--language',default='english');p.add_argument('--seed',type=int,default=42)
    a=p.parse_args();print(json.dumps(generate(a.text_file.read_text(),a.ref_audio,a.ref_text.read_text(),a.out,a.language,a.seed)['metrics']))
