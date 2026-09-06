# Studio tutorial — execution report

Rendered September 6, 2026 on M4 using the existing Studio engine and desktop Codex handoff. The in-app authentication problem remains unresolved; this production does not claim to fix it.

## Output

- Local Studio project: `~/Movies/Codex Studio/Studio Tutorial September 6`.
- Video: `output/codex-media-studio-tutorial.mp4` (about 9.2 MB).
- Chapter list: `output/chapters.txt`.
- Registered Studio revision: SHA-256 `9354c6f0309c2aeb2f190eff70d511161b86211e441a51eb9337f589311e2e7e`, labeled “Tutorial v1 — full playback review pending”.
- Format: H.264/AAC MP4, 1920×1080, constant 30 FPS, 338 seconds, 10,140 frames.
- Actual handoff: `work/studio/codex-handoff.md` inside the project.

This is an illustrated, text-led walkthrough with quiet procedural chapter markers, not a narrated screen recording. Twelve chapters follow a fictional desk-setup edit. The video explains the working handoff route, versions, feedback and quality checks without pretending a successful in-app login or authentic raw-footage acceptance occurred.

## Checks and correction

All twelve initial chapter stills were visually inspected. Reading holds were extended to about 175 words/minute plus entrance time, giving a final 5:38 duration. A directional phrase in the handoff chapter and an awkward second-take text wrap were corrected. The 45-second preview was decoded and its entrance, chapter change and final frames inspected before the full render.

The first full render succeeded technically but its exported audio was silent: FFmpeg automatically preferred Remotion's silent stereo track over the intended mono cue stem. The corrected exporter explicitly maps video input 0 and audio input 1. The good picture stream was reused, preserving the earlier attempt. The verification script now rejects decoded silence and missing chapter cues, rather than relying only on the source WAV.

Corrected output passed complete decode, dimensions/FPS/frame count/duration, exact 48kHz cue-stem duration and all twelve decoded chapter-cue checks. True peak measured **−24.08 dBTP**. This intentionally sparse sound track is not a music bed or narration master. No loudness normalization was applied to the delivery.

All twelve full-render chapter frames were inspected. After the audio correction, the handoff chapter and final frame were inspected again; encoded video-stream hashes matched, proving the remux preserved the inspected picture. No clipping, missing fonts or incorrect live-success claim was found.

## Explicitly pending

The production-quality coordinator contains individual before/during/after dispositions. **R23 listening assessment and R25 complete normal-speed audiovisual review remain pending** because this tool session could not perceive continuous playback with sound. Technical and frame checks do not replace that review. Owner acceptance is also pending. No completion receipt or ready/complete tracker status was issued.

To finish review, watch the exact registered 5:38 MP4 with sound and record actual observations or corrections. Any revised output must be revalidated. No publication/upload/test, hosted generation, model download, voice cloning or remote worker setup occurred. Authentic raw-footage qualification remains a separate task.
