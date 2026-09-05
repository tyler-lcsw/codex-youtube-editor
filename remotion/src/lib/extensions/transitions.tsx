import React from 'react';
import {AbsoluteFill} from 'remotion';

export const crossfadeWeight = (frame: number, start: number, end: number, inFrames: number, outFrames: number): number => {
  if (![frame,start,end,inFrames,outFrames].every(Number.isFinite) || end<=start || inFrames<0 || outFrames<0 || inFrames+outFrames>end-start) throw new Error('Invalid crossfade frame range');
  if (frame<start || frame>=end) return 0;
  return Math.min(1,inFrames ? (frame-start)/inFrames : 1)*Math.min(1,outFrames ? (end-frame)/outFrames : 1);
};

// Composites within the existing clock; neither child is shortened or retimed.
export const Crossfade: React.FC<{version: 1; frame: number; start: number; end: number; inFrames: number; outFrames: number; base: React.ReactNode; incoming: React.ReactNode}> = (p) => {
  if(p.version!==1) throw new Error('Unsupported Crossfade version');
  const opacity=crossfadeWeight(p.frame,p.start,p.end,p.inFrames,p.outFrames);
  return <AbsoluteFill>{p.base}<AbsoluteFill style={{opacity}}>{p.incoming}</AbsoluteFill></AbsoluteFill>;
};
