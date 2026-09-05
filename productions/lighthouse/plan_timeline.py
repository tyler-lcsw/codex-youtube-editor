"""Derive animation clocks from the actual cut manifest and word timings."""
import json,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=R/'videos/lighthouse';W=P/'work';D=R/'remotion/src/shots/lighthouse'
def write(name,component,props,frames,alpha=False,extra=''):
    (D/(name+'.tsx')).write_text(f"import React from 'react';\nimport {{{component}}} from './StoryElements';\n{extra}\nexport const compositionConfig = {{id:'{name}',durationInSeconds:{frames/30:.9f},fps:30,width:1920,height:1080,transparent:{str(alpha).lower()}}};\nexport default function Shot(){{return <{component}{props}/>;}}\n")
def main():
    m=json.loads((W/'render-manifest.json').read_text());words=json.loads((W/'edited-transcript.json').read_text())['words'];segments=m['segments'];starts={s['clip_id']:s['output_in_frame']/30 for s in segments};ends={s['clip_id']:s['output_out_frame']/30 for s in segments};end=max(ends.values());insert=starts['home']
    click=next(w['start']/1000 for w in words if w['clip_id']=='repair' and w['text'].lower().startswith('click'))
    detail=next(w['start']/1000 for w in words if w['clip_id']=='diagnosis' and w['text'].lower().startswith('connection'))
    diag=starts['diagnosis']+2.8;diag=round(diag*30)/30
    write('LighthouseTitle','Title','',105,True)
    write('LighthouseRepair','Repair',f' clickFrame={{{round((click-starts["repair"])*30)}}}',round((ends['repair']-starts['repair'])*30),True)
    write('LighthouseEnd','Title',' end',120,True)
    length=ends['diagnosis']-diag;change=round((detail-diag)*30)-4
    (D/'LighthouseDiagnosis.tsx').write_text(f'''import React from 'react';
import {{AbsoluteFill}} from 'remotion';
import {{Screencast}} from '../../lib/screencast';
export const compositionConfig = {{id:'LighthouseDiagnosis',durationInSeconds:{length:.9f},fps:30,width:1920,height:1080}};
export default function Shot(){{return <AbsoluteFill style={{{{background:'#0c2530'}}}}><Screencast favicon={{<span>☀</span>}} box={{{{x:60,y:55,w:1800,h:960}}}} pages={{[
{{img:'projects/lighthouse/LighthousePanel.png',url:'lantern.local / diagnostics',tabTitle:'Pip’s lighthouse · illustrated interface',enterAt:0,drift:.003}},
{{img:'projects/lighthouse/LighthousePanelDetail.png',url:'lantern.local / diagnostics?inspect=connection',tabTitle:'Pip’s lighthouse · illustrated interface',enterAt:{change},transition:'crossfade',transitionFrames:6,drift:.003,zoom:{{from:1,to:1.02,fx:.39,fy:.52,range:[{change},{change+24}]}}}}
]}} cursor={{[{{frame:0,x:.12,y:.75}},{{frame:{max(1,change-30)},x:.2,y:.6}},{{frame:{change-2},x:.39,y:.47}},{{frame:{change+30},x:.39,y:.47}}]}} clicks={{[{change}]}}/></AbsoluteFill>}}
''')
    shots=[{'id':'LighthouseTitle','type':'overlay','master_in_s':0,'master_out_s':3.5},
           {'id':'LighthouseDiagnosis','type':'cutaway','master_in_s':diag,'master_out_s':ends['diagnosis']},
           {'id':'LighthouseRepair','type':'split','master_in_s':starts['repair'],'master_out_s':ends['repair'],'master_box':{'x':55,'y':130,'w':760,'h':820},'master_crop_cx':.43,'master_crop_cy':.5},
           {'id':'LighthouseWait','type':'insert','master_at_s':insert,'duration_s':1},
           {'id':'LighthouseEnd','type':'overlay','master_in_s':end-4,'master_out_s':end}]
    extensions=[{'id':'crossfade','version':1,'target':'LighthouseDiagnosis','start_frame':round(diag*30),'end_frame':round(ends['diagnosis']*30),'parameters':{'in_frames':10,'out_frames':8},'time_policy':'preserve'},
        {'id':'punch-in','version':1,'target':'output','start_frame':round((starts['failure']+2.5)*30),'end_frame':round(ends['failure']*30),'parameters':{'zoom':1.08,'center_x':.7,'center_y':.5},'time_policy':'preserve'},
        {'id':'color-grade','version':1,'target':'output','start_frame':round(starts['failure']*30),'end_frame':round(ends['failure']*30),'parameters':{'brightness':-.02,'saturation':.8,'contrast':1.05},'time_policy':'preserve'}]
    timeline={'schema_version':1,'master':str(P/'output/clean.mp4'),'remotion_out':str(W/'shots'),'preview':{'end_s':end,'width':1920,'height':1080,'fps':30,'out':str(P/'output/composited.mp4')},'shots':shots,'extensions':extensions}
    (W/'timeline.json').write_text(json.dumps(timeline,indent=2))
    cues={**starts,'home':insert+1,'diagnosis_cutaway':diag,'repair_click_local':click-starts['repair'],'inspect_connection':diag+change/30,'master_duration_s':end,'output_duration_s':end+1,'insert_at_s':insert,'insert_duration_s':1,'ending_title':end-3}
    (W/'story-cues.json').write_text(json.dumps(cues,indent=2))
    # Timestamped subtitle groups follow actual word timing, including the pause insert.
    def stamp(ms):
        sec,ms=divmod(round(ms),1000);minute,sec=divmod(sec,60);hour,minute=divmod(minute,60);return f'{hour:02}:{minute:02}:{sec:02},{ms:03}'
    lines=[];index=1
    for seg in segments:
        group=[w for w in words if w['clip_id']==seg['clip_id']]
        for i in range(0,len(group),6):
            g=group[i:i+6];shift=1000 if seg['clip_id']=='home' else 0
            lines.append(f'{index}\n{stamp(g[0]["start"]+shift)} --> {stamp(g[-1]["end"]+shift)}\n'+ ' '.join(w['text'] for w in g));index+=1
    (P/'output/The Little Lighthouse.srt').write_text('\n\n'.join(lines)+'\n')
    print(json.dumps(cues,indent=2))
if __name__=='__main__':main()
