"""Build source clips and explicit cut inputs from generated story assets."""
import json,math,subprocess,sys,wave
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'videos/lighthouse';A=R/'media/projects/lighthouse';S=Path(__file__).parent

def run(args):subprocess.run([str(x) for x in args],check=True,cwd=R)
def main():
    (P/'work/audio').mkdir(exist_ok=True,parents=True)
    (P/'work/voice').mkdir(exist_ok=True,parents=True)
    clips=[]
    for b in json.loads((S/'spec.json').read_text())['beats']:
        name=b['id'];audio=P/'work/voice'/(name+'.wav')
        run(['ffmpeg','-y','-v','error','-i',A/(b.get('audio_asset',name)+'.wav'),'-af','atempo=0.82','-ar','48000','-c:a','pcm_s16le',audio])
        with wave.open(str(audio)) as w:dur=w.getnframes()/w.getframerate()
        img=A/({'arrival':'harbor','failure':'dark','diagnosis':'pip','repair':'pip','home':'restored'}[name]+'.png')
        frames=math.ceil((dur+.35)*30);out=P/(name+'.mp4')
        run(['ffmpeg','-y','-v','error','-loop','1','-framerate','30','-i',img,'-i',audio,'-vf',f'scale=1920:1280,crop=1920:1080,setsar=1','-af','aresample=48000,apad','-t',str(frames/30),'-c:v','h264_videotoolbox','-b:v','7M','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',out])
        run(['ffmpeg','-y','-v','error','-i',audio,'-ar','16000','-ac','1','-c:a','pcm_s16le',P/'work/audio'/(name+'.wav')])
        clips.append({'id':name,'file':name+'.mp4','keeps':[{'s':0,'e':dur}]})
    cuts={'project':'lighthouse','clip_order':[c['id'] for c in clips],'clips':clips,'styles':{'natural':{'internal_gap':1.2,'keep_gap':.45,'min_tail':.18,'max_tail':.3,'head':.12,'soft_gap':1,'soft_max_tail':.32,'soft_margin':5}}}
    (P/'work/analysis/cuts.json').write_text(json.dumps(cuts,indent=2))
    (P/'work/keyterms.txt').write_text('Pip\nlighthouse\n')
if __name__=='__main__':main()
