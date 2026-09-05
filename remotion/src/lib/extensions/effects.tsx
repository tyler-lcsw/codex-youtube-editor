import React from 'react';
import {AbsoluteFill, useVideoConfig} from 'remotion';

export const PunchIn: React.FC<{version: 1; frame: number; start: number; end: number; zoom?: number; centerX?: number; centerY?: number; children: React.ReactNode}> = ({version,frame,start,end,zoom=1.5,centerX=.5,centerY=.5,children}) => {
  const {width,height}=useVideoConfig();
  if(version!==1 || end<=start || zoom<1 || zoom>4 || centerX<0 || centerX>1 || centerY<0 || centerY>1) throw new Error('Invalid PunchIn v1 parameters');
  const active=frame>=start && frame<end;
  const x=Math.max(0,Math.min(width-width/zoom,width*centerX-width/zoom/2));
  const y=Math.max(0,Math.min(height-height/zoom,height*centerY-height/zoom/2));
  return <AbsoluteFill style={{overflow:'hidden'}}><AbsoluteFill style={{transformOrigin:'0 0',transform:active ? `translate(${-x*zoom}px,${-y*zoom}px) scale(${zoom})` : undefined}}>{children}</AbsoluteFill></AbsoluteFill>;
};
