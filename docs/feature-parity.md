# Feature parity inventory

Baseline source paths below refer to the pinned upstream commit. All creative/provider acceptance remains pending unless backed by a receipt in implementation-status.md.

| Capability to preserve | Existing implementation | Migration acceptance |
|---|---|---|
| Brand interview, font/contrast proof | `brand-setup`, `brand.md`, `remotion/src/brand.ts`, `fonts.ts`, `BrandProof.tsx` | All three contracts stay synchronized; fonts render without runtime download |
| Verbatim multi-take transcript | `transcribe.py`, `format_transcript.py`, `work/keyterms.txt` | Local ASR retains repeats, false starts and fillers; word times use documented milliseconds |
| Editorial cuts, natural/tight styles, reversible fluff decisions | `cutlib.py`, `analyze_cut.py`, `make_review.py`, `render_cuts.py` | Preserve schema, clip order, categories, audio-tail handling, manual changes and both previews |
| Interactive cut editor | `tools/editor/server.py`, `index.html`, `make_proxy.py` | Raw/edited playback, waveform, edge dragging, keyboard cuts, save/backups/log and rerender work on Mac |
| Master and handoff transcript | `render_cuts.py`, `edited-transcript.json` | Source FPS respected, no accumulating drift, downstream timing follows actual rendered segments |
| TSX visuals, transparent overlays, cutaways | `make-tsx`, `vidtsx-2d-generator`, `bake.py`, Remotion registry/scripts | Existing example compositions, browser/VS Code kits and cue frames remain usable |
| Simulated screencasts and actual web stills | `fake-screencast`, `screencast.tsx`, `capture_web.py` | Cursor, click, scroll, URL changes and transitions preserved; actual captures labeled distinctly |
| Voice cleanup | `clean_voice.py`, `clean-audio` | Denoise with preserved voice level, duration and untouched video stream; review by ear |
| SFX generation and catalog reuse | `gen_sfx.py`, `mix_sfx.py`, `suggest-sfx` | Novel prompt generation, reuse-first selection, normalized assets, onset-aligned cues and ducking |
| Music generation and mixing | `gen_music.py`, `mix_music.py` | Prompted beds, instrumental mode, requested length, gains, fades and catalog provenance |
| Stems and voice pickups | `make_stems.py` | Full-length voice/SFX/music/pickup stems retain offsets; final mux matches picture |
| Packaging and separate thumbnail iteration | `packaging`, `thumbnail`, `gen_thumbnail.py`, `thumb_scrim.py`, `composite_logo.py` | One title plus three genuine visual bets, supplied likeness, image edits, optional style elements, PNG/JPG outputs and visual review |
| TTS and cloned per-beat narration | `gen_vo.mjs` | Owner-provided voice identity, pauses, pace, expressive delivery and continuity across beats; same manifest handoff |
| Generated physical B-roll | `gen_video.py` | Image/text-conditioned clips with duration, framing, reference continuity and reproducible job metadata |
| Image-driven avatars and video dubbing | `gen_avatar.mjs`, `make_verdict_page.mjs` | Both image+audio and video+audio tasks; identity verdicts and independently rerollable beats |
| Shorts pilot workflow | `docs/shorts-factory-plan.md`, vertical TSX examples | Configurable owner inputs, vertical framing, script/audio/still/clip/final review gates; no dependency on author's private X-post repository |
| Content tracking | `notion_sync.py` | Local tracker supports metadata, script body, stage/list, match-before-create and explicit updates; optional Notion export remains |
| Upload and analytics | `yt_upload.py`, `yt_stats.py`, setup guide | Private-draft default, title/description/tags/category/thumbnail, supported scheduling and channel statistics preserved |
