import React from 'react';
import {AbsoluteFill} from 'remotion';

// CSS grading for authored TSX. This is deliberately distinct from FFmpeg's additive
// brightness control: brightness here is a multiplier with neutral value 1.
export const ColorGrade: React.FC<{version: 1; frame: number; start: number; end: number; brightness?: number; contrast?: number; saturation?: number; children: React.ReactNode}> = ({version,frame,start,end,brightness=1,contrast=1,saturation=1,children}) => {
  if(version!==1 || end<=start || [brightness,contrast,saturation].some(v=>!Number.isFinite(v) || v<0 || v>3)) throw new Error('Invalid ColorGrade v1 parameters');
  return <AbsoluteFill style={{filter:frame>=start && frame<end ? `brightness(${brightness}) contrast(${contrast}) saturate(${saturation})` : undefined}}>{children}</AbsoluteFill>;
};
