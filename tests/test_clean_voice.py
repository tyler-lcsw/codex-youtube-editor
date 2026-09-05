import subprocess
import sys


def test_hosted_cleanup_requires_explicit_approval_before_reading_input():
    result = subprocess.run([sys.executable, 'tools/clean_voice.py', 'missing.mp4', '--method', 'eleven'], capture_output=True, text=True)
    assert result.returncode != 0
    assert '--allow-cloud' in result.stderr


def test_default_cleanup_is_local():
    result = subprocess.run([sys.executable, 'tools/clean_voice.py', 'missing.mp4'], capture_output=True, text=True)
    assert 'method: deepfilter' in result.stdout
    assert '--allow-cloud' not in result.stderr


def test_cleanup_rejects_overwriting_original(tmp_path):
    source=tmp_path/'original.mp4';source.write_bytes(b'original')
    result=subprocess.run([sys.executable,'tools/clean_voice.py',str(source),'-o',str(source)],capture_output=True,text=True)
    assert result.returncode != 0
    assert 'must differ' in result.stderr
    assert source.read_bytes()==b'original'
