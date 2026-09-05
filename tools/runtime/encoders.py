"""Select only encoders proven to run on this host; no CUDA decode assumption."""
import functools
import re
import subprocess
import tempfile
from pathlib import Path

CHOICES = {8: ('h264_videotoolbox', 'h264_nvenc', 'libx264'),
           10: ('hevc_videotoolbox', 'hevc_nvenc', 'libx265')}

def choose_encoder(available: set[str], prefer: str = 'auto', bit_depth: int = 8) -> str:
    candidates = CHOICES.get(bit_depth, ())
    if prefer != 'auto':
        if prefer not in available or prefer not in candidates:
            raise ValueError(f'Encoder {prefer} unavailable for {bit_depth}-bit output')
        return prefer
    for encoder in candidates:
        if encoder in available:
            return encoder
    raise ValueError(f'No working {bit_depth}-bit encoder; tested {sorted(available)}')

def encoder_args(encoder: str, mode: str) -> list[str]:
    depth = 10 if mode == 'final' else 8
    if encoder not in CHOICES[depth]:
        raise ValueError(f'{encoder} cannot deliver {mode}')
    args = ['-c:v', encoder]
    if mode == 'preview':
        args += ['-vf', 'scale=1280:-2,format=yuv420p']
    if 'videotoolbox' in encoder:
        args += ['-b:v', '4M' if depth == 8 else '25M', '-allow_sw', '0']
    elif 'nvenc' in encoder:
        args += ['-preset', 'p4' if depth == 8 else 'p5', '-rc', 'vbr', '-cq', '30' if depth == 8 else '19', '-b:v', '0']
    else:
        args += ['-preset', 'fast', '-crf', '25' if depth == 8 else '19']
    args += ['-pix_fmt', ('p010le' if 'videotoolbox' in encoder or 'nvenc' in encoder else 'yuv420p10le') if depth == 10 else 'yuv420p']
    if depth == 10:
        args += ['-tag:v', 'hvc1']
    return args

@functools.lru_cache(maxsize=1)
def probe_encoders() -> dict:
    raw = subprocess.run(['ffmpeg', '-hide_banner', '-encoders'], capture_output=True, text=True, check=True).stdout
    result = {}
    with tempfile.TemporaryDirectory(prefix='codex-encoder-') as tmp:
        for depth, choices in CHOICES.items():
            for name in choices:
                if not re.search(r'\b' + re.escape(name) + r'\b', raw):
                    result[name] = {'available': False, 'reason': 'not compiled'}
                    continue
                try:
                    r = subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'lavfi', '-i', 'color=s=320x180:r=30', '-frames:v', '3',
                                        *encoder_args(name, 'final' if depth == 10 else 'preview'), str(Path(tmp) / 'probe.mp4')],
                                       capture_output=True, text=True, timeout=30)
                    result[name] = {'available': r.returncode == 0, 'reason': r.stderr[-500:]}
                except subprocess.TimeoutExpired:
                    result[name] = {'available': False, 'reason': 'encode probe timed out'}
    return result

def runtime_encoder(mode: str, prefer: str = 'auto') -> list[str]:
    usable = {name for name, state in probe_encoders().items() if state['available']}
    return encoder_args(choose_encoder(usable, prefer, 10 if mode == 'final' else 8), mode)
