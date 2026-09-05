"""Exercise the file-backed filter graph on the installed FFmpeg runtime."""
import json
import shutil
import subprocess

import pytest

from tools import make_stems
from tools.providers.sfx_procedural import synthesize


def test_sfx_stem_uses_supported_file_graph_and_preserves_duration(tmp_path, monkeypatch):
    if not shutil.which('ffmpeg'):
        pytest.skip('FFmpeg required for stem integration')
    monkeypatch.setattr(make_stems, 'SCRATCH', str(tmp_path / 'scratch'))
    click = synthesize('click', tmp_path / 'click.wav', .12, seed=4)
    catalog = tmp_path / 'catalog.json'
    catalog.write_text(json.dumps({'clips': [{'id': 'click', 'file': str(click)}]}))
    output = tmp_path / 'stem.wav'
    plan = tmp_path / 'plan.json'
    plan.write_text(json.dumps({
        'catalog': str(catalog),
        'stem': {'out': str(output), 'duration_s': 1.0, 'sample_rate': 48000, 'channels': 2},
        'events': [{'sfx_id': 'click', 'at_s': .4, 'gain_db': -6}],
    }))
    assert make_stems.build_sfx(str(plan)) == str(output)
    probe = subprocess.run(['ffprobe', '-v', 'error', '-show_streams', '-of', 'json', str(output)], capture_output=True, text=True, check=True)
    stream = json.loads(probe.stdout)['streams'][0]
    assert stream['duration_ts'] == 48000
    assert stream['sample_rate'] == '48000'
    assert stream['channels'] == 2
    assert stream['codec_name'] == 'pcm_s24le'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(output), '-f', 's24le', '-c:a', 'pcm_s24le', '-'], capture_output=True, check=True).stdout
    assert not any(raw[:int(.35 * 48000) * 6])
    assert any(raw[int(.4 * 48000) * 6:int(.55 * 48000) * 6])
