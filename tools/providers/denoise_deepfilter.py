"""Pinned DeepFilterNet inference; invoke through the offline worker sandbox."""
import argparse
import os
from pathlib import Path
from .asr_mlx import model_path


def denoise(source: Path, output: Path):
    from df.enhance import init_df, enhance, load_audio, save_audio
    model, state, _ = init_df(model_base_dir=str(model_path('denoise')), log_level='ERROR')
    audio, _ = load_audio(str(source), sr=state.sr())
    cleaned = enhance(model, state, audio, pad=True)
    if cleaned.shape != audio.shape:
        raise RuntimeError('Denoiser changed sample count or channel count')
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.stem + '.partial.wav')
    try:
        save_audio(str(temporary), cleaned, state.sr())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--audio', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    denoise(args.audio, args.out)
