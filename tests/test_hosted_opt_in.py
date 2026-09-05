import subprocess
import sys
import pytest

@pytest.mark.parametrize('script', ['gen_thumbnail.py','gen_sfx.py','gen_music.py','gen_video.py'])
def test_hosted_python_tools_require_explicit_opt_in(script):
    r=subprocess.run([sys.executable,'tools/'+script],capture_output=True,text=True)
    assert r.returncode!=0 and '--allow-cloud' in r.stderr

@pytest.mark.parametrize('script',['gen_vo.mjs','gen_avatar.mjs'])
def test_hosted_node_tools_require_explicit_opt_in(script):
    r=subprocess.run(['node','tools/'+script],capture_output=True,text=True)
    assert r.returncode!=0 and '--allow-cloud' in r.stderr

@pytest.mark.parametrize('script',['gen_vo.mjs','gen_avatar.mjs'])
def test_unsupported_dry_run_cannot_bypass_hosted_gate(script):
    r=subprocess.run(['node','tools/'+script,'--dry-run'],capture_output=True,text=True)
    assert r.returncode!=0 and '--allow-cloud' in r.stderr
