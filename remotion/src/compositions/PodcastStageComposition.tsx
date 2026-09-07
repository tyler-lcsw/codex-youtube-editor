import React from 'react';
import {PodcastStage, PodcastStageProps} from '../lib/podcast/PodcastStage';
import {useBundledFonts} from '../fonts';

export const defaultPodcastStageProps: PodcastStageProps = {
  schema_version: 1,
  primary_audio: {asset_id: 'preview', sha256: '0'.repeat(64), duration_ms: 5000},
  render: {fps: 30, width: 1920, height: 1080},
  identity: {
    show_title: 'Your Show',
    episode_title: 'Audio-First Podcast Stage',
    speaker_name: 'Your Name',
  },
  waveform: {
    sample_period_ms: 50,
    normalization: 'peak-rms-v1',
    values: Array.from({length: 100}, (_, index) => 0.18 + Math.abs(Math.sin(index * 0.41)) * 0.72),
  },
  chapters: [{id: 'preview', title: 'Preview', start_ms: 0, end_ms: 5000}],
  motion: 'standard',
};

export const calculatePodcastStageMetadata = ({props}: {props: PodcastStageProps}) => ({
  durationInFrames: Math.max(1, Math.ceil(props.primary_audio.duration_ms * props.render.fps / 1000)),
  fps: props.render.fps,
  width: props.render.width,
  height: props.render.height,
});

export const PodcastStageComposition: React.FC<PodcastStageProps> = (props) => {
  useBundledFonts();
  return <PodcastStage {...props} />;
};
