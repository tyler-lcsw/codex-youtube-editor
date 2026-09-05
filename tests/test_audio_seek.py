"""A seek at zero must retain AAC's presentation-time priming behavior."""
from array import array
import shutil
import subprocess
import wave

import pytest
from tools.render_cuts import render_audio_segment


@pytest.mark.parametrize('start', [0.0, 0.1])
def test_seek_preserves_aac_pulse_position(tmp_path, start):
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg required')
    wav = tmp_path / 'pulse.wav'
    samples = array('h', [0] * 48000)
    for i in range(12000, 12480):
        samples[i] = 18000 if i % 24 < 12 else -18000
    with wave.open(str(wav), 'wb') as audio:
        audio.setparams((1, 2, 48000, 0, 'NONE', ''))
        audio.writeframes(samples.tobytes())
    source = tmp_path / 'source.m4a'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(wav), '-c:a', 'aac', str(source)], check=True)
    reference = tmp_path / 'reference.wav'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', str(source), '-c:a', 'pcm_s16le', str(reference)], check=True)
    result = tmp_path / 'cut.wav'
    render_audio_segment(source, start, 1 - start, result)
    def pulse_start(path):
        with wave.open(str(path)) as audio:
            values = array('h', audio.readframes(audio.getnframes()))
        return next(i for i, value in enumerate(values) if abs(value) > 5000)
    assert abs(pulse_start(result) - (pulse_start(reference) - round(start * 48000))) <= 1
