"""Build a standalone 9:16 story excerpt with context and transcript captions."""
import json,math,subprocess
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'videos/lighthouse';A=R/'media/projects/lighthouse';D=R/'remotion/src/shots/lighthouse';W=P/'work'
def main():
    c=json.loads((W/'story-cues.json').read_text());start=c['repair'];duration=c['output_duration_s']-start;intro=3.5;frames=round((duration+intro)*30)
    subprocess.run(['ffmpeg','-y','-v','error','-ss',str(start),'-i',str(P/'output/The Little Lighthouse.mp4'),'-vn','-ar','48000','-c:a','pcm_s16le',str(A/'short-audio.wav')],check=True)
    words=json.loads((W/'edited-transcript.json').read_text())['words'];groups=[]
    for beat in ['repair','home']:
        selected=[w for w in words if w['clip_id']==beat]
        for i in range(0,len(selected),5):
            g=selected[i:i+5];shift=1 if beat=='home' else 0
            groups.append({'start':round((g[0]['start']/1000+shift-start+intro)*30),'end':round((g[-1]['end']/1000+shift-start+intro)*30),'text':' '.join(w['text'] for w in g)})
    (A/'short-captions.json').write_text(json.dumps(groups,indent=2))
    (D/'LighthouseShort.tsx').write_text(f'''import React from 'react';
import {{AbsoluteFill,Audio,Img,Sequence,staticFile,useCurrentFrame,interpolate}} from 'remotion';
import {{FONT_BODY,FONT_DISPLAY}} from '../../fonts';
const captions={json.dumps(groups)};
export const compositionConfig = {{id:'LighthouseShort',durationInSeconds:{frames/30:.9f},fps:30,width:1080,height:1920}};
export default function Shot(){{const f=useCurrentFrame();const intro=f<105;const home=f>={round((c['home']-start+intro)*30)};const caption=captions.find(c=>f>=c.start&&f<=c.end);const join=f>={round((c['repair_click_local']+intro)*30)};
return <AbsoluteFill style={{{{background:'#0c2530',fontFamily:FONT_BODY,color:'#fff2d6'}}}}><Sequence from={{105}}><Audio src={{staticFile('projects/lighthouse/short-audio.wav')}}/></Sequence>
<div style={{{{position:'absolute',top:140,left:80,right:80,color:'#ffc36e',fontSize:27,letterSpacing:5}}}}>THE LITTLE LIGHTHOUSE</div>
<div style={{{{position:'absolute',top:220,left:80,right:80,fontFamily:FONT_DISPLAY,fontSize:79,lineHeight:1.12,fontWeight:700}}}}>{{intro?'One boat waiting. One loose cable.':home?'A way home.':'One careful click.'}}</div>
<div style={{{{position:'absolute',top:520,left:45,right:45,height:750,borderRadius:42,overflow:'hidden'}}}}><Img src={{staticFile('projects/lighthouse/'+(home?'restored':intro?'dark':'pip')+'.png')}} style={{{{width:'100%',height:'100%',objectFit:'cover',transform:`scale(${{1+Math.min(f,600)/16000}})`}}}}/></div>
{{!intro&&!home&&<svg width="920" height="150" style={{{{position:'absolute',left:80,top:1330}}}}><path d={{join?'M30 75H890':'M30 75H385M535 75H890'}} stroke="#73bcca" strokeWidth="16"/><rect x={{join?422:362}} y="45" width="38" height="60" rx="7" fill="#ffc36e"/><rect x={{join?460:520}} y="45" width="38" height="60" rx="7" fill="#ffc36e"/></svg>}}
<div style={{{{position:'absolute',left:80,right:80,top:1510,fontSize:54,textAlign:'center',lineHeight:1.35,fontWeight:600}}}}>{{intro?'A small story about finding the missing connection.':caption?.text|| (home?'Small connections. Brighter nights.':'')}}</div>
<div style={{{{position:'absolute',left:80,bottom:110,fontSize:23,color:'#a8c4c9'}}}}>An original illustrated story</div></AbsoluteFill>}}
''')
    (W/'short-plan.json').write_text(json.dumps({'source':str(P/'output/The Little Lighthouse.mp4'),'source_start_s':start,'context_intro_s':intro,'duration_s':frames/30,'caption_groups':groups},indent=2))
if __name__=='__main__':main()
