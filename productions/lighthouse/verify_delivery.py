"""Technical delivery checks and a hash-bound artifact inventory, without publication."""
import json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R))
from tools.jobs import file_hash
P=R/'videos/lighthouse';W=P/'work';O=P/'output'
def probe(p):return json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)],capture_output=True,text=True,check=True).stdout)
def main():
    c=json.loads((W/'story-cues.json').read_text());short=json.loads((W/'short-plan.json').read_text());artifacts=[]
    for name,dims,duration in [('The Little Lighthouse.mp4',(1920,1080),c['output_duration_s']),('The Little Lighthouse — Vertical.mp4',(1080,1920),short['duration_s'])]:
        p=O/name;meta=probe(p);v=next(s for s in meta['streams'] if s['codec_type']=='video');a=next(s for s in meta['streams'] if s['codec_type']=='audio')
        assert (v['width'],v['height'])==dims
        assert int(v['nb_frames'])==round(duration*30)
        assert abs(float(v['duration'])-duration)<.034
        assert abs(float(a['duration'])-duration)<.05
        subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],capture_output=True,check=True)
        scan=subprocess.run(['ffmpeg','-hide_banner','-i',str(p),'-af','loudnorm=I=-18:TP=-1.5:LRA=9:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
        loud=json.JSONDecoder().raw_decode(scan.stderr[scan.stderr.rfind('{'):])[0]
        assert float(loud['input_tp'])<=-1.0,loud
        artifacts.append({'file':str(p.relative_to(R)),'sha256':file_hash(p),'size':p.stat().st_size,'frames':int(v['nb_frames']),'video_duration_s':float(v['duration']),'audio_duration_s':float(a['duration']),'dimensions':dims,'loudness':loud})
    for name in ['voice-track.wav','sfx-track.wav','music-track.wav']:
        p=O/name;s=probe(p)['streams'][0];assert int(s['duration_ts'])==round(c['output_duration_s']*48000),(name,s)
        artifacts.append({'file':str(p.relative_to(R)),'sha256':file_hash(p),'samples':int(s['duration_ts']),'sample_rate':s['sample_rate']})
    from PIL import Image
    for letter in 'ABC':
        p=P/'packaging/thumbs'/(letter+'.jpg')
        with Image.open(p) as im:assert im.size==(1280,720);im.verify()
        assert p.stat().st_size<2_000_000
        artifacts.append({'file':str(p.relative_to(R)),'sha256':file_hash(p),'size':p.stat().st_size})
    report={'status':'technical_checks_passed','artifacts':artifacts,'human_listening':'Not performed by this automated run; no human creative acceptance claim.','publication':'Not invoked or tested.'}
    (W/'delivery-verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
if __name__=='__main__':main()
