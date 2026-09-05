import json
import subprocess
import sys
from pathlib import Path

def test_render_records_actual_segments_and_invalidates_changed_cuts(tmp_path):
    from tools.fixture_media import make_clock_clip
    root=Path(__file__).resolve().parents[1]
    src=make_clock_clip(tmp_path/'clip.mp4','30000/1001',2)
    work=tmp_path/'work';(work/'audio').mkdir(parents=True);(work/'analysis').mkdir();(work/'transcripts').mkdir()
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(src),'-ar','16000','-ac','1',str(work/'audio/a.wav')],check=True)
    (work/'transcripts/a.json').write_text(json.dumps({'words':[{'text':'pulse','start':200,'end':500,'confidence':None}]}))
    cuts={'project':'fixture','clip_order':['a'],'clips':[{'id':'a','file':'clip.mp4','keeps':[{'s':0,'e':1}]}],
          'styles':{'natural':{'internal_gap':2,'keep_gap':.3,'min_tail':.1,'max_tail':.2,'head':.1,'soft_gap':1,'soft_max_tail':.2,'soft_margin':5}}}
    (work/'analysis/cuts.json').write_text(json.dumps(cuts))
    cmd=[sys.executable,str(root/'tools/render_cuts.py'),str(tmp_path),'--style','natural','--mode','preview','--encoder','libx264']
    subprocess.run(cmd,check=True,capture_output=True)
    manifest=json.loads((work/'render-manifest.json').read_text())
    assert manifest['segments'][0]['fps_num']==30000 and manifest['segments'][0]['fps_den']==1001
    assert manifest['segments'][0]['output_in_sample']==0
    assert (work/'edited-transcript.json').is_file()
    old=manifest['render_key'];cuts['clips'][0]['keeps']=[{'s':.1,'e':.7}]
    (work/'analysis/cuts.json').write_text(json.dumps(cuts));subprocess.run(cmd,check=True,capture_output=True)
    assert json.loads((work/'render-manifest.json').read_text())['render_key']!=old


def test_audio_tail_is_padded_to_actual_video_sample_count(tmp_path):
    import wave
    from tools.fixture_media import make_clock_clip
    from tools.render_cuts import render_audio_segment
    src=make_clock_clip(tmp_path/'end.mp4','30',1)
    out=tmp_path/'tail.wav'
    render_audio_segment(src,.9,.5,out)
    with wave.open(str(out)) as wav:assert wav.getnframes()==24000


def test_sample_exact_audio_resamples_before_trimming(tmp_path):
    import wave
    from tools.render_cuts import render_audio_segment
    source=tmp_path/'24khz.wav'
    with wave.open(str(source),'wb') as wav:
        wav.setparams((1,2,24000,0,'NONE','not compressed'));wav.writeframes(b'\0\0'*24000)
    out=tmp_path/'48khz.wav';render_audio_segment(source,0,.5,out)
    with wave.open(str(out)) as wav:assert wav.getnframes()==24000
