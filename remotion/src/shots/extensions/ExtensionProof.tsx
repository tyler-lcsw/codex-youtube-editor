import React from 'react';
import {AbsoluteFill, useCurrentFrame} from 'remotion';
import {Crossfade} from '../../lib/extensions/transitions';
import {PunchIn} from '../../lib/extensions/effects';
import {ColorGrade} from '../../lib/extensions/filters';
import {FONT_BODY} from '../../fonts';

export const compositionConfig = {id:'ExtensionProof',durationInSeconds:3,fps:30,width:1280,height:720};
const Scene: React.FC<{color:string;label:string}> = ({color,label}) => <AbsoluteFill style={{background:color,display:'flex',alignItems:'center',justifyContent:'center',fontFamily:FONT_BODY,color:'#fff',fontSize:58}}><div style={{border:'6px solid white',padding:'65px',borderRadius:30}}>{label}</div></AbsoluteFill>;
export default function ExtensionProof() {
  const frame=useCurrentFrame();
  return <ColorGrade version={1} frame={frame} start={60} end={90} saturation={.25}><PunchIn version={1} frame={frame} start={45} end={75} zoom={1.25}><Crossfade version={1} frame={frame} start={0} end={90} inFrames={30} outFrames={30} base={<Scene color="#075c52" label="Original scene"/>} incoming={<Scene color="#3047a5" label="Incoming scene"/>}/></PunchIn><div style={{position:'absolute',left:28,bottom:22,fontFamily:FONT_BODY,fontSize:22,color:'white'}}>Frame {frame} · same 90-frame clock</div></ColorGrade>;
}
