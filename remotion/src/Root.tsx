import React from 'react';
import { Composition } from 'remotion';
import { shots } from './registry.gen';
import {useBundledFonts} from './fonts';
import {PodcastRoot} from './PodcastRoot';

const fontReadyShots = shots.map(({Comp, config}) => ({
  config,
  Comp: function FontReadyComposition() {
    useBundledFonts();
    return <Comp />;
  },
}));

// Every shot file exports `compositionConfig` + a default component. gen-registry.mjs
// discovers them into registry.gen. This maps each to a <Composition>.
export const RemotionRoot: React.FC = () => {
  return (
    <>
      <PodcastRoot />
      {fontReadyShots.map(({ Comp, config }) => (
        <Composition
          key={config.id}
          id={config.id}
          component={Comp as React.FC}
          durationInFrames={Math.max(1, Math.round(config.durationInSeconds * config.fps))}
          fps={config.fps}
          width={config.width}
          height={config.height}
        />
      ))}
    </>
  );
};
