import React from 'react';
import {Img, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import {ArrowRight, Quote} from 'lucide-react';
import {COLORS, RADIUS, SHADOW} from '../../brand';
import {FONT_BODY, FONT_DISPLAY, FONT_MONO} from '../../fonts';

type PodcastTranscriptAnchor = {start_ms: number; end_ms: number; text: string};
type PodcastProvenance = {
  kind: 'transcript' | 'project_asset' | 'project_resource' | 'local_generation' | 'none';
  label: string;
  asset_id?: string;
  sha256?: string;
  resource_url?: string;
};

type VisualEventBase<Type extends string, Treatment> = {
  id: string;
  type: Type;
  chapter_id: string;
  start_ms: number;
  end_ms: number;
  transcript_anchor: PodcastTranscriptAnchor;
  purpose: string;
  treatment: Treatment;
  provenance: PodcastProvenance[];
  camera_policy: 'base_only' | 'camera_permitted';
};

export type PodcastBaseEvent = VisualEventBase<'base', {kind: 'base'}>;

export type PodcastChapterCardEvent = VisualEventBase<'chapter_card', {
  kind: 'chapter_card';
  heading: string;
  subheading?: string;
}>;

export type PodcastQuoteEvent = VisualEventBase<'quote', {
  kind: 'quote';
  text: string;
  attribution?: string;
  mode: 'quote' | 'key_point';
}>;

export type PodcastProgressiveListEvent = VisualEventBase<'progressive_list', {
  kind: 'progressive_list';
  heading: string;
  items: string[];
}>;

export type PodcastComparisonEvent = VisualEventBase<'comparison', {
  kind: 'comparison';
  heading: string;
  left: {label: string; items: string[]};
  right: {label: string; items: string[]};
}>;

export type PodcastImageSourceEvent = VisualEventBase<'image_source', {
  kind: 'image_source';
  heading: string;
  caption?: string;
  asset?: {path: string; sha256: string};
}>;

export type PodcastVisualEvent =
  | PodcastBaseEvent
  | PodcastChapterCardEvent
  | PodcastQuoteEvent
  | PodcastProgressiveListEvent
  | PodcastComparisonEvent
  | PodcastImageSourceEvent;

const nonempty = (value: string) => value.trim().length > 0;

export const validatePodcastVisualEvents = (
  events: readonly PodcastVisualEvent[],
  durationMs: number,
) => {
  const ids = new Set<string>();
  for (const event of events) {
    if (!nonempty(event.id) || ids.has(event.id)) throw new Error('Podcast visual event IDs must be unique nonempty text');
    ids.add(event.id);
    if (
      !Number.isInteger(event.start_ms) ||
      !Number.isInteger(event.end_ms) ||
      event.start_ms < 0 ||
      event.end_ms <= event.start_ms ||
      event.end_ms > durationMs
    ) throw new Error(`Podcast visual event ${event.id} has invalid timing`);

    switch (event.type) {
      case 'base': break;
      case 'chapter_card':
        if (!nonempty(event.treatment.heading) || (event.treatment.subheading !== undefined && !nonempty(event.treatment.subheading))) throw new Error(`Podcast chapter card ${event.id} has empty text`);
        break;
      case 'quote':
        if (!nonempty(event.treatment.text) || (event.treatment.attribution !== undefined && !nonempty(event.treatment.attribution))) throw new Error(`Podcast quote ${event.id} has empty text`);
        break;
      case 'progressive_list':
        if (!nonempty(event.treatment.heading) || event.treatment.items.length === 0) throw new Error(`Podcast list ${event.id} needs a title and items`);
        if (event.treatment.items.some((item) => !nonempty(item))) throw new Error(`Podcast list ${event.id} has an empty item`);
        break;
      case 'comparison':
        if (!nonempty(event.treatment.heading) || !nonempty(event.treatment.left.label) || !nonempty(event.treatment.right.label) || event.treatment.left.items.length === 0 || event.treatment.right.items.length === 0) {
          throw new Error(`Podcast comparison ${event.id} needs two labeled sides`);
        }
        if ([...event.treatment.left.items, ...event.treatment.right.items].some((item) => !nonempty(item))) throw new Error(`Podcast comparison ${event.id} has an empty item`);
        break;
      case 'image_source': {
        const asset = event.treatment.asset;
        if (asset) {
          const safePath = !asset.path.startsWith('/') && !asset.path.split('/').includes('..');
          if (!safePath || !/^[0-9a-f]{64}$/.test(asset.sha256)) throw new Error(`Podcast source card ${event.id} requires hash-bound project media`);
        }
        if (!nonempty(event.treatment.heading) || (event.treatment.caption !== undefined && !nonempty(event.treatment.caption))) throw new Error(`Podcast source card ${event.id} has empty text`);
        break;
      }
    }
    if (event.type !== event.treatment.kind) throw new Error(`Podcast visual event ${event.id} type does not match its treatment`);
    if (!nonempty(event.chapter_id) || !nonempty(event.purpose) || !nonempty(event.transcript_anchor.text) || event.provenance.length === 0) {
      throw new Error(`Podcast visual event ${event.id} is missing editorial context`);
    }
  }
};

export const activeVisualEventAt = (
  events: readonly PodcastVisualEvent[],
  timeMs: number,
): PodcastVisualEvent | undefined => {
  let active: PodcastVisualEvent | undefined;
  for (const event of events) {
    if (event.start_ms <= timeMs && timeMs < event.end_ms) {
      // A later start is more specific. Array order breaks equal-start ties, so
      // even malformed overlaps remain deterministic and never stack panels.
      if (!active || event.start_ms >= active.start_ms) active = event;
    }
  }
  return active;
};

const eventEntrance = (frame: number, fps: number, event: PodcastVisualEvent, reduced: boolean) => {
  if (reduced) return {opacity: 1, y: 0};
  const startFrame = Math.round(event.start_ms * fps / 1000);
  const endFrame = Math.round(event.end_ms * fps / 1000);
  const enterFrames = Math.max(1, Math.min(14, endFrame - startFrame));
  const exitFrames = Math.max(1, Math.min(10, endFrame - startFrame));
  const enter = Math.min(1, Math.max(0, (frame - startFrame) / enterFrames));
  const exit = Math.min(1, Math.max(0, (endFrame - frame) / exitFrames));
  const opacity = Math.min(enter, exit);
  return {opacity, y: (1 - enter) * 18};
};

const panelStyle = (unit: number): React.CSSProperties => ({
  width: '100%',
  height: '100%',
  boxSizing: 'border-box',
  border: `${Math.max(1, unit)}px solid ${COLORS.line}`,
  borderRadius: RADIUS.card * unit,
  background: `${COLORS.paper}f2`,
  boxShadow: SHADOW.card,
  padding: `${42 * unit}px ${52 * unit}px`,
  overflow: 'hidden',
});

const ChapterCard: React.FC<{event: PodcastChapterCardEvent; unit: number}> = ({event, unit}) => (
  <div style={{...panelStyle(unit), display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
    <div style={{fontFamily: FONT_MONO, fontSize: Math.max(12, 21 * unit), color: COLORS.accent, fontWeight: 700, letterSpacing: 2 * unit, textTransform: 'uppercase'}}>
      New chapter
    </div>
    <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(28, 82 * unit), lineHeight: 1.02, fontWeight: 700, marginTop: 18 * unit}}>
      {event.treatment.heading}
    </div>
    {event.treatment.subheading ? <div style={{fontSize: Math.max(15, 30 * unit), color: COLORS.muted, marginTop: 22 * unit}}>{event.treatment.subheading}</div> : null}
  </div>
);

const QuoteCard: React.FC<{event: PodcastQuoteEvent; unit: number}> = ({event, unit}) => {
  const keyPoint = event.treatment.mode === 'key_point';
  return (
    <div style={{...panelStyle(unit), display: 'grid', gridTemplateColumns: 'auto 1fr', alignItems: 'center', gap: 34 * unit}}>
      <div style={{alignSelf: 'start', width: 76 * unit, height: 76 * unit, minWidth: 34, minHeight: 34, borderRadius: RADIUS.pill, backgroundColor: keyPoint ? COLORS.signal : COLORS.accent, display: 'flex', alignItems: 'center', justifyContent: 'center'}}>
        <Quote size={Math.max(18, 36 * unit)} color={COLORS.paper} />
      </div>
      <div>
        <div style={{fontFamily: FONT_MONO, textTransform: 'uppercase', letterSpacing: 1.5 * unit, color: keyPoint ? COLORS.signal : COLORS.accent, fontSize: Math.max(11, 19 * unit), fontWeight: 700}}>
          {keyPoint ? 'Key point' : 'In their words'}
        </div>
        <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(24, 58 * unit), fontWeight: 600, lineHeight: 1.14, marginTop: 14 * unit}}>
          {event.treatment.text}
        </div>
        {event.treatment.attribution ? <div style={{fontSize: Math.max(13, 24 * unit), color: COLORS.muted, marginTop: 22 * unit}}>— {event.treatment.attribution}</div> : null}
      </div>
    </div>
  );
};

const ProgressiveList: React.FC<{
  event: PodcastProgressiveListEvent;
  timeMs: number;
  unit: number;
}> = ({event, timeMs, unit}) => {
  const span = Math.max(1, event.end_ms - event.start_ms);
  return (
    <div style={panelStyle(unit)}>
      <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(22, 48 * unit), fontWeight: 700}}>{event.treatment.heading}</div>
      <div style={{display: 'grid', gap: 18 * unit, marginTop: 30 * unit}}>
        {event.treatment.items.map((item, index) => {
          const reveal = event.start_ms + span * (index + 1) / (event.treatment.items.length + 1);
          const visible = timeMs >= reveal;
          return (
            <div key={`${index}-${item}`} style={{display: 'grid', gridTemplateColumns: `${44 * unit}px 1fr`, gap: 17 * unit, alignItems: 'center', opacity: visible ? 1 : 0.12}}>
              <div style={{width: 40 * unit, height: 40 * unit, minWidth: 22, minHeight: 22, borderRadius: RADIUS.pill, display: 'flex', alignItems: 'center', justifyContent: 'center', backgroundColor: visible ? COLORS.accent : COLORS.line, color: visible ? COLORS.paper : COLORS.muted, fontFamily: FONT_MONO, fontWeight: 700, fontSize: Math.max(10, 18 * unit)}}>{index + 1}</div>
              <div style={{fontSize: Math.max(14, 29 * unit), fontWeight: 600}}>{item}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const Comparison: React.FC<{event: PodcastComparisonEvent; unit: number}> = ({event, unit}) => {
  const column = (side: PodcastComparisonEvent['treatment']['left'], accent: string) => (
    <div style={{border: `${Math.max(1, unit)}px solid ${COLORS.line}`, borderTop: `${6 * unit}px solid ${accent}`, borderRadius: RADIUS.panel * unit, padding: `${26 * unit}px ${30 * unit}px`, background: COLORS.cream}}>
      <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(16, 30 * unit), fontWeight: 700}}>{side.label}</div>
      <div style={{display: 'grid', gap: 12 * unit, marginTop: 18 * unit}}>
        {side.items.map((item, index) => <div key={`${index}-${item}`} style={{fontSize: Math.max(12, 22 * unit), color: COLORS.muted}}>• {item}</div>)}
      </div>
    </div>
  );
  return (
    <div style={panelStyle(unit)}>
      <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(21, 43 * unit), fontWeight: 700, textAlign: 'center'}}>{event.treatment.heading}</div>
      <div style={{display: 'grid', gridTemplateColumns: '1fr auto 1fr', alignItems: 'center', gap: 22 * unit, marginTop: 26 * unit}}>
        {column(event.treatment.left, COLORS.accent)}
        <ArrowRight size={Math.max(20, 38 * unit)} color={COLORS.muted} />
        {column(event.treatment.right, COLORS.signal)}
      </div>
    </div>
  );
};

const ImageSourceCard: React.FC<{event: PodcastImageSourceEvent; unit: number}> = ({event, unit}) => (
  <div style={{...panelStyle(unit), display: 'grid', gridTemplateColumns: '1.08fr 0.92fr', gap: 34 * unit}} data-asset-sha256={event.treatment.asset?.sha256}>
    <div style={{overflow: 'hidden', borderRadius: RADIUS.panel * unit, border: `${Math.max(1, unit)}px solid ${COLORS.line}`, backgroundColor: COLORS.cream}}>
      {event.treatment.asset ? <Img src={staticFile(event.treatment.asset.path)} style={{width: '100%', height: '100%', objectFit: 'contain'}} /> : (
        <div style={{width: '100%', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: FONT_MONO, fontSize: Math.max(12, 22 * unit), color: COLORS.muted}}>SOURCE MATERIAL</div>
      )}
    </div>
    <div style={{alignSelf: 'center'}}>
      <div style={{fontFamily: FONT_MONO, fontSize: Math.max(11, 18 * unit), textTransform: 'uppercase', letterSpacing: 1.3 * unit, color: COLORS.accent, fontWeight: 700}}>Source</div>
      <div style={{fontFamily: FONT_DISPLAY, fontSize: Math.max(20, 42 * unit), lineHeight: 1.08, fontWeight: 700, marginTop: 13 * unit}}>{event.treatment.heading}</div>
      {event.treatment.caption ? <div style={{fontSize: Math.max(13, 24 * unit), color: COLORS.muted, lineHeight: 1.35, marginTop: 18 * unit}}>{event.treatment.caption}</div> : null}
      <div style={{fontFamily: FONT_MONO, fontSize: Math.max(10, 17 * unit), color: COLORS.signal, marginTop: 24 * unit}}>{event.provenance[0]?.label ?? 'Source recorded'}</div>
    </div>
  </div>
);

export const PodcastVisualEventLayer: React.FC<{
  event?: PodcastVisualEvent;
  timeMs: number;
  motion: 'standard' | 'reduced';
  unit: number;
}> = ({event, timeMs, motion, unit}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  if (!event || event.type === 'base') return null;
  const entrance = eventEntrance(frame, fps, event, motion === 'reduced');
  let content: React.ReactNode;
  switch (event.type) {
    case 'chapter_card': content = <ChapterCard event={event} unit={unit} />; break;
    case 'quote': content = <QuoteCard event={event} unit={unit} />; break;
    case 'progressive_list': content = <ProgressiveList event={event} timeMs={timeMs} unit={unit} />; break;
    case 'comparison': content = <Comparison event={event} unit={unit} />; break;
    case 'image_source': content = <ImageSourceCard event={event} unit={unit} />; break;
  }
  return <div style={{position: 'absolute', inset: 0, opacity: entrance.opacity, transform: `translateY(${entrance.y * unit}px)`}}>{content}</div>;
};
