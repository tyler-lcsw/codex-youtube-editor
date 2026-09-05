import json
from pathlib import Path
import subprocess
import sys


def clip(path, color, filters=None):
    command=['ffmpeg','-y','-v','error','-f','lavfi','-i',f'color={color}:s=64x64:r=30:d=2','-f','lavfi','-i','sine=frequency=440:sample_rate=48000:duration=2']
    if filters:command+=['-vf',filters]
    subprocess.run(command+['-c:v','libx264','-pix_fmt','yuv420p','-c:a','aac',str(path)],check=True)


def bake(tmp_path, master, shots, effects,expected_frames=60):
    output=tmp_path/'output.mp4'
    tl={'master':str(master),'remotion_out':str(tmp_path),'preview':{'end_s':2,'width':64,'height':64,'fps':30,'out':str(output)},'shots':shots,'extensions':effects}
    path=tmp_path/'timeline.json';path.write_text(json.dumps(tl))
    subprocess.run([sys.executable,'tools/bake.py',str(path)],check=True,capture_output=True)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(output),'-map','0:v','-pix_fmt','rgb24','-f','rawvideo','-'])
    assert len(raw)==expected_frames*64*64*3
    return lambda frame,x=32:tuple(raw[(frame*64*64+32*64+x)*3:(frame*64*64+32*64+x)*3+3])


def effect(name,target,start,end,parameters):
    return {'id':name,'version':1,'target':target,'start_frame':start,'end_frame':end,'parameters':parameters,'time_policy':'preserve'}


def test_cutaway_crossfade_blends_without_changing_frame_count(tmp_path):
    master=tmp_path/'master.mp4';clip(master,'red');clip(tmp_path/'blue.mp4','blue')
    pixel=bake(tmp_path,master,[{'id':'blue','type':'cutaway','master_in_s':0,'master_out_s':2}],
               [effect('crossfade','blue',0,60,{'in_frames':15,'out_frames':15})])
    assert pixel(0)[0]>220 and pixel(0)[2]<30
    assert pixel(20)[2]>220 and pixel(20)[0]<30
    assert pixel(59)[0]>200


def test_output_punch_in_is_bounded_to_selected_frames(tmp_path):
    master=tmp_path/'master.mp4';clip(master,'red','drawbox=x=32:y=0:w=32:h=64:color=lime:t=fill')
    pixel=bake(tmp_path,master,[],[effect('punch-in','output',15,45,{'zoom':2,'center_x':.75,'center_y':.5})])
    assert pixel(0,8)[0]>220 and pixel(59,8)[0]>220
    assert pixel(30,8)[1]>220 and pixel(30,8)[0]<30


def test_output_grade_does_not_affect_other_frames(tmp_path):
    master=tmp_path/'master.mp4';clip(master,'gray')
    pixel=bake(tmp_path,master,[],[effect('color-grade','output',15,45,{'brightness':.2})])
    assert abs(pixel(0)[0]-pixel(59)[0])<=2
    assert pixel(30)[0]>pixel(0)[0]+35


def test_output_grade_uses_clock_after_insert(tmp_path):
    master=tmp_path/'master.mp4';clip(master,'red');clip(tmp_path/'insert.mp4','blue')
    pixel=bake(tmp_path,master,[{'id':'insert','type':'insert','master_at_s':.5,'duration_s':1}],
        [effect('color-grade','output',60,75,{'brightness':.2})],expected_frames=90)
    assert pixel(59)[1]<20 and pixel(75)[1]<20
    assert pixel(60)[1]>30 and pixel(74)[1]>30
