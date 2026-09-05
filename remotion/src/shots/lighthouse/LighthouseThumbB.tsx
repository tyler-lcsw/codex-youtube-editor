import React from 'react';
import {AbsoluteFill,Img,staticFile} from 'remotion';
import {FONT_DISPLAY} from '../../fonts';
export const compositionConfig = {id:'LighthouseThumbB',durationInSeconds:1,fps:30,width:1280,height:720};
export default function Shot(){return <AbsoluteFill style={{background:'#0c2530'}}><Img src={staticFile('projects/lighthouse/restored.png')} style={{width:1280,height:853,objectFit:'cover',position:'absolute',top:-65}}/><AbsoluteFill style={{background:'linear-gradient(0deg,rgba(3,18,25,.9),transparent 65%)'}}/><div style={{position:'absolute',left:55,bottom:45,fontFamily:FONT_DISPLAY,fontSize:91,fontWeight:700,color:'#ffcf79',textShadow:'0 5px 15px #051f2b'}}>HOME AGAIN</div></AbsoluteFill>}
