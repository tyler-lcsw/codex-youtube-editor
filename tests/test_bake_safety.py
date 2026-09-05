import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def test_unsupported_extension_fails_before_creating_output(tmp_path):
    tl={'master':'missing.mp4','shots':[],'preview':{'end_s':1,'width':320,'height':180,'fps':30,'out':str(tmp_path/'final.mp4')},
        'extensions':[{'id':'unknown','version':1,'target':'master','time_policy':'preserve','start_frame':0,'end_frame':10,'parameters':{}}]}
    path=tmp_path/'timeline.json';path.write_text(json.dumps(tl))
    result=subprocess.run([sys.executable,'tools/bake.py',str(path)],capture_output=True,text=True)
    assert result.returncode!=0 and 'Unsupported timeline extension' in result.stderr
    assert list(tmp_path.iterdir())==[path]


def test_final_bake_failure_preserves_previous_export(tmp_path):
    from tools.fixture_media import make_clock_clip
    source=make_clock_clip(tmp_path/'source.mp4','30',1)
    output=tmp_path/'final.mp4';output.write_bytes(b'previous success')
    tl={'master':str(source),'shots':[],'preview':{'end_s':1,'width':320,'height':180,'fps':30,'out':str(output)}}
    path=tmp_path/'timeline.json';path.write_text(json.dumps(tl))
    wrapper=tmp_path/'bin';wrapper.mkdir();ffmpeg=wrapper/'ffmpeg'
    ffmpeg.write_text('#!'+sys.executable+'\nimport os,sys\nfrom pathlib import Path\nif "-movflags" in sys.argv:\n Path(sys.argv[-1]).write_bytes(b"partial encode")\n sys.exit(1)\nos.execv('+repr(shutil.which('ffmpeg'))+',sys.argv)\n');ffmpeg.chmod(0o755)
    result=subprocess.run([sys.executable,'tools/bake.py',str(path)],env={**os.environ,'PATH':str(wrapper)+os.pathsep+os.environ['PATH']},capture_output=True,text=True)
    assert result.returncode!=0
    assert output.read_bytes()==b'previous success'
