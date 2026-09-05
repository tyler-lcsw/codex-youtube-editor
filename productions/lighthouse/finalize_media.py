"""Package the current mix with rendered vertical picture, thumbnails and captions."""
import json,os,re,subprocess
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[2];P=R/'videos/lighthouse';A=R/'media/projects/lighthouse';W=P/'work';O=P/'output'
def main():
    plan=json.loads((W/'short-plan.json').read_text());duration=plan['duration_s'];delay=round(plan['context_intro_s']*48000)
    staged=O/'vertical-staged.mp4'
    subprocess.run(['ffmpeg','-y','-v','error','-i',str(W/'shots/LighthouseShort.mp4'),'-i',str(A/'short-audio.wav'),'-map','0:v','-map','1:a','-c:v','copy','-af',f'aresample=48000,adelay={delay}S:all=1,apad,atrim=end_sample={round(duration*48000)},asetpts=N/SR/TB','-c:a','aac','-b:a','256k','-t',str(duration),'-movflags','+faststart',str(staged)],check=True)
    os.replace(staged,O/'The Little Lighthouse — Vertical.mp4')
    for letter in 'ABC':
        with Image.open(A/('LighthouseThumb'+letter+'.png')) as im:im.convert('RGB').save(P/'packaging/thumbs'/(letter+'.jpg'),quality=92)
    text=(O/'The Little Lighthouse.srt').read_text()
    (O/'The Little Lighthouse.vtt').write_text('WEBVTT\n\n'+re.sub(r'(\d\d:\d\d:\d\d),(\d\d\d)',r'\1.\2',text))
if __name__=='__main__':main()
