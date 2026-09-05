import json
import subprocess
from fractions import Fraction
from pathlib import Path

def test_fractional_clock_fixture(tmp_path):
    from tools.fixture_media import make_clock_clip
    path = make_clock_clip(tmp_path / 'space ü' / 'clock.mp4', '30000/1001', 2)
    raw = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(path)])
    streams = json.loads(raw)['streams']
    video = next(s for s in streams if s['codec_type'] == 'video')
    assert Fraction(video['avg_frame_rate']) == Fraction(30000, 1001)
    assert int(video['nb_frames']) == 60
    assert any(s['codec_type'] == 'audio' for s in streams)
    receipt = json.loads(path.with_suffix('.json').read_text())
    assert receipt['pulse_samples'] == [0, 48000]
