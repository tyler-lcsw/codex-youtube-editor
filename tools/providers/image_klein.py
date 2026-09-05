"""Offline FLUX.2 Klein 4B generation/reference editing at qualified M4 dimensions."""
import argparse
import json
import os
import time
from pathlib import Path
from PIL import Image
from .asr_mlx import model_path
from ..jobs import file_hash
from ..run_state import atomic_json


def validate_request(prompt: str, width: int, height: int, refs: list[Path]):
    if not prompt.strip() or len(prompt.encode())>4096:raise ValueError('Prompt must contain 1–4096 bytes')
    if any(type(n) is not int or n<256 or n%16 for n in (width,height)) or width*height>768*512:
        raise ValueError('Qualified M4 image profile: dimensions >=256, multiples of 16, at most 393216 pixels')
    if len(refs)>1:raise ValueError('Multi-reference memory qualification is deferred; this profile accepts one reference')
    for ref in refs:
        with Image.open(ref) as im:
            if im.width*im.height>768*512:raise ValueError('Prepare an explicit reference copy <=393216 pixels; originals are not resized silently')
            im.verify()


def generate(prompt: str, output: Path, width=768, height=512, refs=None, seed=42):
    refs=refs or [];validate_request(prompt,width,height,refs)
    os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    import mlx.core as mx
    from mflux.models.flux2.variants import Flux2Klein, Flux2KleinEdit
    mx.set_memory_limit(12*1024**3);mx.set_cache_limit(512*1024**2)
    t=time.monotonic();model=(Flux2KleinEdit if refs else Flux2Klein)(quantize=4,model_path=str(model_path('image_klein')))
    kwargs={'image_paths':[str(p) for p in refs]} if refs else {}
    result=model.generate_image(seed=seed,prompt=prompt,width=width,height=height,num_inference_steps=4,**kwargs)
    output.parent.mkdir(parents=True,exist_ok=True)
    temporary=output.with_name(output.stem+'.partial.png')
    try:
        result.save(str(temporary))
        with Image.open(temporary) as im:
            if im.size!=(width,height):raise RuntimeError('Generated dimensions do not match request')
            im.verify()
        os.replace(temporary,output)
    finally:temporary.unlink(missing_ok=True)
    receipt={'provider':'flux2_klein_mflux','model_key':'image_klein','seed':seed,'steps':4,'prompt':prompt,
        'references':[{'path':str(p.resolve()),'sha256':file_hash(p)} for p in refs],
        'artifact':{'path':str(output.resolve()),'sha256':file_hash(output),'native_width':width,'native_height':height},
        'metrics':{'elapsed_s':time.monotonic()-t,'peak_mlx_bytes':mx.get_peak_memory()}}
    model_spec=json.loads((Path(__file__).resolve().parents[2]/'config/models.lock.json').read_text())['models']['image_klein']
    receipt['model']={k:model_spec[k] for k in ('repo','revision','license')}
    atomic_json(output.with_suffix('.provenance.json'),receipt);return receipt


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prompt-file',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--width',type=int,default=768);p.add_argument('--height',type=int,default=512)
    p.add_argument('--ref',type=Path,action='append',default=[]);p.add_argument('--seed',type=int,default=42)
    a=p.parse_args();print(json.dumps(generate(a.prompt_file.read_text(),a.out,a.width,a.height,a.ref,a.seed)['metrics']))
