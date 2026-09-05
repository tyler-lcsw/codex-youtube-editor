"""Explicit procedural UI effects; no approximation of arbitrary prompted sounds."""
import math
import random
import wave
from array import array
from pathlib import Path

def synthesize(kind: str, out: Path, duration_s: float, seed: int=0) -> Path:
    if kind not in {'click','pop','tone'}:raise ValueError('Procedural provider supports click, pop and tone only; select a generative provider for this sound')
    if not 0<duration_s<=10:raise ValueError('Duration must be in (0,10] seconds')
    rng=random.Random(seed);sr=48000;count=round(sr*duration_s)
    samples=array('h')
    for i in range(count):
        t=i/sr
        if kind=='click':v=rng.uniform(-1,1)*math.exp(-t*100)
        elif kind=='pop':v=math.sin(2*math.pi*(500*t-700*t*t))*math.exp(-t*35)
        else:v=math.sin(2*math.pi*880*t)*min(1,t/.005,(duration_s-t)/.02)
        samples.append(round(16000*v))
    out=Path(out);out.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(out),'wb') as f:f.setparams((1,2,sr,0,'NONE','not compressed'));f.writeframes(samples.tobytes())
    return out
