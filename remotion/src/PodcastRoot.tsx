import React from 'react';
import {Composition} from 'remotion';
import {
  calculatePodcastStageMetadata,
  defaultPodcastStageProps,
  PodcastStageComposition,
} from './compositions/PodcastStageComposition';

/**
 * The podcast renderer bundles this root directly so long-form renders do not
 * load every generated legacy shot. Root.tsx also reuses it for Studio.
 */
export const PodcastRoot: React.FC = () => (
  <Composition
    id="PodcastStage"
    component={PodcastStageComposition}
    durationInFrames={150}
    fps={30}
    width={1920}
    height={1080}
    defaultProps={defaultPodcastStageProps}
    calculateMetadata={calculatePodcastStageMetadata}
  />
);
