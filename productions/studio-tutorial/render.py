"""Render the tutorial through existing Remotion and procedural SFX capabilities.
Invoke through tools.production_quality run; outputs are staged and never overwrite earlier versions.
"""
import argparse,json,os,subprocess,sys,uuid,wave
from array import array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from tools.runtime.offline import offline_command
from tools.providers.sfx_procedural import synthesize
NODE=Path('/Users/tyler-lcsw/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
SCENES=json.loads((Path(__file__).parent/'scenes.json').read_text())
def main():
 p=argparse.ArgumentParser();p.add_argument('project',type=Path);p.add_argument('--stills',action='store_true');p.add_argument('--preview',action='store_true');a=p.parse_args()
 attempt=a.project/'work'/('render-'+uuid.uuid4().hex[:8]);attempt.mkdir(parents=True)
 base=[str(NODE),str(ROOT/'remotion/node_modules/@remotion/cli/remotion-cli.js')]
 entry=str(ROOT/'productions/studio-tutorial/StudioTutorial.tsx')
 if a.stills:
  start=0
  for i,s in enumerate(SCENES):
   out=attempt/f'chapter-{i+1:02}.png'
   subprocess.run(offline_command(base+['still',entry,'StudioTutorial',str(out),f'--frame={start+60}','--scale=0.5'],allow_loopback=True),cwd=ROOT/'remotion',check=True)
   start+=s['seconds']*30
  print(attempt);return
 video=attempt/'picture.mp4'
 args=base+['render',entry,'StudioTutorial',str(video),'--concurrency=1','--codec=h264','--crf=20']
 preview_seconds=sum(s['seconds'] for s in SCENES[:2])
 if a.preview:args+=[f'--frames=0-{preview_seconds*30-1}','--scale=0.5']
 subprocess.run(offline_command(args,allow_loopback=True),cwd=ROOT/'remotion',check=True)
 duration=preview_seconds if a.preview else sum(s['seconds'] for s in SCENES)
 # Purposeful chapter markers, not a music bed or simulated speech.
 sr=48000;track=array('h',[0])*(duration*sr)
 start=0
 for i,s in enumerate(SCENES):
  cue=int((start+.5)*sr)
  if cue>=len(track):break
  sound=synthesize('pop',attempt/f'cue-{i}.wav',.13,seed=i)
  with wave.open(str(sound),'rb') as f: samples=array('h',f.readframes(f.getnframes()))
  for j,v in enumerate(samples):
   if cue+j<len(track):track[cue+j]=round(v*.13)
  start+=s['seconds']
 stem=attempt/'chapter-cues.wav'
 with wave.open(str(stem),'wb') as f:f.setparams((1,2,sr,0,'NONE','not compressed'));f.writeframes(track.tobytes())
 final=attempt/('tutorial-preview.mp4' if a.preview else 'codex-media-studio-tutorial.mp4')
 subprocess.run(['ffmpeg','-v','error','-i',str(video),'-i',str(stem),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart','-shortest',str(final)],check=True)
 print(final,flush=True)
if __name__=='__main__':main()
