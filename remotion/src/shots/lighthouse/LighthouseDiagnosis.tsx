import React from 'react';
import {AbsoluteFill} from 'remotion';
import {Screencast} from '../../lib/screencast';
export const compositionConfig = {id:'LighthouseDiagnosis',durationInSeconds:6.600000000,fps:30,width:1920,height:1080};
export default function Shot(){return <AbsoluteFill style={{background:'#0c2530'}}><Screencast favicon={<span>☀</span>} box={{x:60,y:55,w:1800,h:960}} pages={[
{img:'projects/lighthouse/LighthousePanel.png',url:'lantern.local / diagnostics',tabTitle:'Pip’s lighthouse · illustrated interface',enterAt:0,drift:.003},
{img:'projects/lighthouse/LighthousePanelDetail.png',url:'lantern.local / diagnostics?inspect=connection',tabTitle:'Pip’s lighthouse · illustrated interface',enterAt:142,transition:'crossfade',transitionFrames:6,drift:.003,zoom:{from:1,to:1.02,fx:.39,fy:.52,range:[142,166]}}
]} cursor={[{frame:0,x:.12,y:.75},{frame:112,x:.2,y:.6},{frame:140,x:.39,y:.47},{frame:172,x:.39,y:.47}]} clicks={[142]}/></AbsoluteFill>}
