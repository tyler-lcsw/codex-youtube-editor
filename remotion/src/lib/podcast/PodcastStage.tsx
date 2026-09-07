import React from 'react';
import {AbsoluteFill, Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, RADIUS, SHADOW} from '../../brand';
import {FONT_BODY, FONT_DISPLAY, FONT_MONO} from '../../fonts';

export type PodcastChapter = {
  id: string;
  title: string;
  start_ms: number;
  end_ms: number;
};

export type PodcastStageProps = {
  schema_version: 1;
  primary_audio: {
    asset_id: string;
    sha256: string;
    duration_ms: number;
  };
  render: {
    fps: number;
    width: number;
    height: number;
  };
  identity: {
    show_title: string;
    episode_title: string;
    speaker_name: string;
    artwork?: {path: string; sha256: string};
  };
  waveform: {
    sample_period_ms: number;
    normalization: 'peak-rms-v1';
    values: number[];
  };
  chapters: PodcastChapter[];
  motion: 'standard' | 'reduced';
};

const BAR_COUNT = 52;

const chapterAt = (chapters: PodcastChapter[], timeMs: number): PodcastChapter | undefined =>
  chapters.find((chapter) => chapter.start_ms <= timeMs && timeMs < chapter.end_ms);

export const PodcastStage: React.FC<PodcastStageProps> = (props) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const currentMs = frame * 1000 / fps;
  const currentSample = Math.floor(currentMs / props.waveform.sample_period_ms);
  const activeChapter = chapterAt(props.chapters, currentMs);
  const progress = Math.min(1, currentMs / props.primary_audio.duration_ms);
  const unit = Math.min(width / 1920, height / 1080);
  const ambient = props.motion === 'reduced' ? 0 : Math.sin(frame / 90) * 22 * unit;
  const energy = props.waveform.values[currentSample] ?? 0;

  return (
    <AbsoluteFill
      style={{
        overflow: 'hidden',
        color: COLORS.ink,
        backgroundColor: COLORS.paper,
        fontFamily: FONT_BODY,
      }}
    >
      <AbsoluteFill
        style={{
          background: `radial-gradient(${900 * unit}px ${650 * unit}px at ${28 + ambient / Math.max(1, width) * 100}% 28%, ${COLORS.accent}2b, transparent 68%), radial-gradient(${760 * unit}px ${600 * unit}px at 82% 78%, ${COLORS.signal}24, transparent 72%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.32,
          backgroundImage: `radial-gradient(${COLORS.line} ${Math.max(1, 1.5 * unit)}px, transparent ${Math.max(1, 1.5 * unit)}px)`,
          backgroundSize: `${Math.max(18, 46 * unit)}px ${Math.max(18, 46 * unit)}px`,
          transform: props.motion === 'reduced' ? undefined : `translateX(${ambient}px)`,
        }}
      />

      <div style={{position: 'absolute', inset: `${68 * unit}px ${84 * unit}px`, display: 'flex', flexDirection: 'column'}}>
        <header style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 24 * unit}}>
          <div style={{fontFamily: FONT_MONO, fontWeight: 700, fontSize: Math.max(11, 22 * unit), letterSpacing: 1.6 * unit, color: COLORS.accent, textTransform: 'uppercase'}}>
            {props.identity.show_title}
          </div>
          <div style={{fontFamily: FONT_MONO, fontSize: Math.max(10, 18 * unit), color: COLORS.muted}}>
            {activeChapter?.title ?? 'Episode'}
          </div>
        </header>

        <main style={{flex: 1, minHeight: 0, display: 'grid', gridTemplateColumns: props.identity.artwork ? '0.78fr 1.22fr' : '1fr', alignItems: 'center', gap: 72 * unit}}>
          {props.identity.artwork ? (
            <div style={{justifySelf: 'center', width: Math.min(520 * unit, height * 0.48), aspectRatio: '1', borderRadius: RADIUS.card * unit, overflow: 'hidden', border: `${Math.max(1, unit)}px solid ${COLORS.line}`, boxShadow: SHADOW.card}}>
              <Img src={staticFile(props.identity.artwork.path)} style={{width: '100%', height: '100%', objectFit: 'cover'}} />
            </div>
          ) : null}

          <div style={{minWidth: 0}}>
            <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(18, 76 * unit), fontWeight: 700, lineHeight: 1.04, letterSpacing: -1.5 * unit, maxWidth: 1120 * unit}}>
              {props.identity.episode_title}
            </div>
            <div style={{marginTop: 18 * unit, fontSize: Math.max(12, 28 * unit), fontWeight: 600, color: COLORS.muted}}>
              {props.identity.speaker_name}
            </div>

            <div style={{height: Math.max(46, 200 * unit), marginTop: 54 * unit, display: 'flex', alignItems: 'center', gap: Math.max(2, 8 * unit), padding: `0 ${20 * unit}px`, borderRadius: RADIUS.card * unit, backgroundColor: `${COLORS.paper}cc`, border: `${Math.max(1, unit)}px solid ${COLORS.line}`, boxShadow: SHADOW.soft}}>
              {Array.from({length: BAR_COUNT}, (_, index) => {
                const sampleIndex = currentSample - BAR_COUNT + index + 1;
                const value = props.waveform.values[sampleIndex] ?? 0;
                const isNow = index === BAR_COUNT - 1;
                const heightPx = Math.max(3 * unit, (20 + value * 150) * unit);
                return (
                  <div
                    key={index}
                    style={{
                      flex: 1,
                      minWidth: 1,
                      height: heightPx,
                      maxHeight: '86%',
                      borderRadius: RADIUS.pill,
                      background: isNow ? COLORS.accent : value > 0.68 ? COLORS.accent2 : COLORS.signal,
                      opacity: isNow ? 0.9 + energy * 0.1 : 0.34 + value * 0.56,
                    }}
                  />
                );
              })}
            </div>
          </div>
        </main>

        <footer>
          <div style={{height: Math.max(3, 7 * unit), borderRadius: RADIUS.pill, backgroundColor: COLORS.line, overflow: 'hidden'}}>
            <div style={{height: '100%', width: `${progress * 100}%`, background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.accent2}, ${COLORS.signal})`}} />
          </div>
        </footer>
      </div>
    </AbsoluteFill>
  );
};
