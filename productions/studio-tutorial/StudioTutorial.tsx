import React from 'react';
import {AbsoluteFill, Composition, interpolate, registerRoot, useCurrentFrame} from 'remotion';
import {FONT_BODY, FONT_DISPLAY, useBundledFonts} from '../../remotion/src/fonts';
import scenes from './scenes.json';

export const compositionConfig = {id:'StudioTutorial', durationInSeconds:scenes.reduce((n,s)=>n+s.seconds,0), fps:30, width:1920,height:1080};
const C = {paper:'#F5EBDD',ink:'#303234',coral:'#F36B4F',deep:'#A93420'};
const starts = scenes.map((_,i)=>scenes.slice(0,i).reduce((n,s)=>n+s.seconds*30,0));
export const StudioTutorial:React.FC=()=>{
 useBundledFonts();
 const frame=useCurrentFrame();
 const index=Math.max(0,starts.findLastIndex(start=>frame>=start));
 const scene=scenes[index]; const local=frame-starts[index];
 const enter=interpolate(local,[0,15],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'});
 return <AbsoluteFill style={{backgroundColor:C.paper,color:C.ink,fontFamily:FONT_BODY,padding:88}}>
  <div style={{position:'absolute',left:0,top:0,height:10,width:`${100*(frame+1)/(compositionConfig.durationInSeconds*30)}%`,background:C.coral}}/>
  <div style={{display:'flex',justifyContent:'space-between',alignItems:'center',fontSize:25,fontWeight:600,letterSpacing:2}}><span>CODEX MEDIA STUDIO</span><span style={{color:C.deep}}>ILLUSTRATED WORKFLOW • {index+1} / {scenes.length}</span></div>
  <div style={{marginTop:50,fontSize:25,fontWeight:600,color:C.deep}}>{scene.tab.toUpperCase()}</div>
  <div style={{opacity:enter,transform:`translateY(${(1-enter)*16}px)`}}>
   <h1 style={{fontFamily:FONT_DISPLAY,fontSize:index===0?86:76,lineHeight:1.08,margin:'20px 0 20px',whiteSpace:'pre-line',letterSpacing:-2}}>{scene.title}</h1>
   <p style={{fontSize:34,margin:0,maxWidth:1700}}>{scene.subtitle}</p>
  </div>
  <div style={{display:'flex',gap:90,position:'absolute',left:88,right:88,top:index===0?475:390,bottom:190}}>
   <div style={{flex:1,display:'flex',flexDirection:'column',justifyContent:'center',gap:30}}>
    {scene.steps.map((step,i)=><div key={step} style={{display:'flex',alignItems:'flex-start',gap:22,opacity:interpolate(local,[8+i*5,20+i*5],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}><div style={{flexShrink:0,width:50,height:50,borderRadius:25,background:C.ink,color:C.paper,display:'flex',alignItems:'center',justifyContent:'center',fontSize:26,fontWeight:600}}>{i+1}</div><div style={{fontSize:35,lineHeight:1.4,flex:1}}>{step}</div></div>)}
   </div>
   <div style={{width:760,display:'flex',flexDirection:'column',justifyContent:'center',gap:18}}>
    {scene.cards.map(([label,text],i)=><div key={label} style={{background:C.ink,color:C.paper,borderRadius:18,padding:'26px 32px',borderLeft:`8px solid ${C.coral}`,opacity:interpolate(local,[12+i*5,24+i*5],[0,1],{extrapolateLeft:'clamp',extrapolateRight:'clamp'})}}><div style={{fontSize:21,fontWeight:600,letterSpacing:1.5,color:'#FF947C',marginBottom:10}}>{label}</div><div style={{fontSize:31,lineHeight:1.3}}>{text}</div></div>)}
   </div>
  </div>
  <div style={{position:'absolute',left:88,right:88,bottom:76,borderTop:'2px solid #30323433',paddingTop:23,display:'flex',gap:24,alignItems:'center'}}><span style={{color:C.deep,fontSize:23,fontWeight:600}}>REMEMBER</span><span style={{fontSize:27}}>{scene.tip}</span></div>
 </AbsoluteFill>;
};
const Root:React.FC=()=> <Composition id={compositionConfig.id} component={StudioTutorial} width={1920} height={1080} fps={30} durationInFrames={compositionConfig.durationInSeconds*30}/>;
registerRoot(Root);
