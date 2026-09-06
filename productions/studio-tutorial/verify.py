"""Technical review of an existing tutorial export; never claims playback acceptance."""
import argparse,hashlib,json,subprocess,wave
from array import array
from pathlib import Path

def main():
 p=argparse.ArgumentParser();p.add_argument('video',type=Path);p.add_argument('--stem',type=Path);a=p.parse_args();v=a.video.resolve();folder=v.parent
 scenes=json.loads((Path(__file__).parent/'scenes.json').read_text());seconds=sum(s['seconds'] for s in scenes)
 data=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(v)]))
 video=next(s for s in data['streams'] if s['codec_type']=='video');audio=next(s for s in data['streams'] if s['codec_type']=='audio')
 assert (video['width'],video['height'])==(1920,1080)
 assert video['r_frame_rate']=='30/1' and int(video['nb_read_frames'])==seconds*30
 assert abs(float(video['duration'])-seconds)<1/30
 assert abs(float(audio['duration'])-seconds)<.05
 subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True)
 stats=subprocess.run(['ffmpeg','-hide_banner','-i',str(v),'-af','volumedetect','-vn','-f','null','-'],capture_output=True,text=True,check=True).stderr
 (folder/'audio-levels.txt').write_text(stats)
 loudness=subprocess.run(['ffmpeg','-hide_banner','-i',str(v),'-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-vn','-f','null','-'],capture_output=True,text=True,check=True).stderr
 (folder/'loudness-and-true-peak.txt').write_text(loudness)
 with wave.open(str(a.stem or folder/'chapter-cues.wav'),'rb') as f:
  assert f.getframerate()==48000 and f.getnframes()==seconds*48000
  samples=array('h',f.readframes(f.getnframes()))
 decoded=array('h',subprocess.check_output(['ffmpeg','-v','error','-i',str(v),'-vn','-ac','1','-ar','48000','-f','s16le','-']))
 assert max(abs(x) for x in decoded)>500, 'Export audio is silent or chapter cues are missing'
 start=0;timing=[]
 for i,s in enumerate(scenes):
  expected=round((start+.5)*48000);nonzero=next(j for j in range(expected,expected+4800) if samples[j])
  assert abs(nonzero/48000-(start+.5))<.002
  assert max(abs(x) for x in decoded[expected:expected+4800])>500, 'Missing decoded chapter cue'
  timing.append({'chapter':i+1,'start_s':start,'cue_s':nonzero/48000})
  subprocess.run(['ffmpeg','-v','error','-ss',str(start+2),'-i',str(v),'-frames:v','1','-vf','scale=960:-1',str(folder/f'final-chapter-{i+1:02}.png')],check=True)
  start+=s['seconds']
 subprocess.run(['ffmpeg','-v','error','-sseof','-0.04','-i',str(v),'-frames:v','1','-vf','scale=960:-1',str(folder/'final-last-frame.png')],check=True)
 result={'sha256':hashlib.sha256(v.read_bytes()).hexdigest(),'duration_s':seconds,'video':video,'audio':audio,'cue_timing':timing,'decode':'pass','normal_speed_audiovisual_review':'pending: tool session cannot perceive continuous playback','owner_acceptance':'pending'}
 (folder/'technical-review.json').write_text(json.dumps(result,indent=2));print(json.dumps({'duration_s':seconds,'frames':video['nb_read_frames'],'sha256':result['sha256'],'review':str(folder/'technical-review.json')},indent=2))
if __name__=='__main__':main()
