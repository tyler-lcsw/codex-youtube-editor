---
name: clean-cut
description: Step 1 of the AI Video Editor pipeline — turn raw talking-head footage into a clean master cut. Use when the user wants to "clean cut", "cut the raw footage", "remove filler / dead air / bad takes", "tighten the pacing", produce cuts.json, run the cut editor, or render a cleaned preview/master for a video-N project in this repo. Covers audio extraction, local transcription, authoring cuts.json (keeps/cuts/fluff categorized), project-specific editorial policy, QA + review docs, the local cut-editor UI, tight/natural previews, the source-appropriate final render, and producing edited-transcript.json as the handoff to $make-tsx. Not for building TSX overlays (that is $make-tsx) or the raw TSX authoring rules (that is vidtsx-2d-generator).
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md` and `docs/providers.md` first. Default to local media processing; hosted generation requires explicit approved scope. Check provider readiness before any generation command. Original provider examples below describe available compatibility paths, not permission to call them. Use project state and preserve prior approvals.


# clean-cut — the step-1 cut pipeline

Turn a project's raw clips (`videos/video-N/DJI_*.MP4`) into a **clean master** + **`edited-transcript.json`** (the word-level timing spine every later step anchors to). The single source of truth is **`videos/video-N/work/analysis/cuts.json`** — shared by Codex and the editor UI. Every tool lives in `tools/` and takes the project dir as its first arg.

**You (Codex) author the cuts by reading the transcript.** No separate LLM call. The tools handle audio, encoding, QA, and the editor; the judgment — what is a retake, a false start, filler, or fluff — is yours.

## Pipeline (run in order)

Let `P` = the project (e.g. `video-1`). Clip **id** = a short handle (`0233`); every artifact for a clip is named by that id (`0233.wav`, `0233.json`). The raw MP4 path is stored per-clip in cuts.json as `file`.

1. **Extract 16 kHz mono WAV per clip** → `P/work/audio/<id>.wav` (used for transcription + the RMS noise-floor / snap-to-audio tails). Not scripted — run ffmpeg per clip:
   `ffmpeg -i videos/video-1/DJI_...0233_D.MP4 -vn -ac 1 -ar 16000 videos/video-1/work/audio/0233.wav`
2. **Draft this video's keyterms → `P/work/keyterms.txt`** (do this before transcribing). Keyterms bias the recognizer toward this video's proper nouns / product / tech names so they aren't mangled (e.g. "Seedream" not "sea dream", "Cloudflare" not "cloud flare"). Accuracy here is load-bearing: the transcript text drives cut decisions AND `$make-tsx` greps it for phrases to time beats — a garbled term breaks both. From the video's topic/title, list the ~10–40 likely brand names, tools, tech, and jargon, one per line (blank lines and `#` comments ignored). **This is per-video — never hardcode terms in `transcribe.py`.** If you skip the file, transcription still runs (empty fallback), just with more errors on specialty words. The shape is one term per line:

   ```
   # tools + brands named in this video
   Claude Code
   Remotion
   AssemblyAI
   ElevenLabs
   Cloudflare
   ```
3. **Transcribe** (local Qwen MLX recognition/alignment; inspect fillers and timing uncertainty; auto-loads `work/keyterms.txt`):
   `python tools/transcribe.py P` → `P/work/transcripts/<id>.json`. `--clips 0233` for one, `--force` to redo. It prints how many keyterms it loaded — a "none" line means you haven't drafted them.
4. **Readable take view** for analysis: `python tools/format_transcript.py P` → `P/work/analysis/takes-<id>.txt` (segments on >0.8s gaps, fillers tagged inline with timestamps).
5. **Author `cuts.json`** (see schema below) by reading `takes-*.txt`: mark every span as a keep or a categorized cut, add fluff suggestions and judgment-call flags.
6. **QA + review docs**:
   `python tools/analyze_cut.py P [--style tight]` → `qa-report.md` (internal dead-air, clipped-tail risks, tiny fragments, fluff, hard entries at cut joins, **ghost speech** = untranscribed energy riding inside a keep, low-confidence kept tokens). Ghost/hard-entry checks exist because a transcript diff CANNOT see a mistimed token (clipped word onset) or an untranscribed false start ("and it—") that survives the cut — only energy-vs-token cross-checks catch them (a careful listen caught both before these checks existed).
   `python tools/make_review.py P` → `review.md` (per-clip keep/cut table + estimated length per style).
7. **Editor proxy** (once): `python tools/make_proxy.py P` → `P/work/editor/{proxy.mp4, waveform.png, manifest.json}` (720p concat of raw clips + per-clip offsets).
8. **Previews** (render BOTH, user picks): `python tools/render_cuts.py P --style tight --mode preview` and `--style natural` → `P/output/preview-<style>.mp4` (720p H.264 with VideoToolbox or CPU).
8.5. **Machine verification of the render (MANDATORY after every preview render, before
   showing the user).** Extract the preview's WAV → `transcribe.py P --clips preview
   --force` → `python tools/verify_cut.py P` → `verify-report.md`. A second ASR pass
   over the RENDER, diffed against the intended kept tokens: EXTRA words = untranscribed
   ghosts that rode along (false starts glued to word tails — invisible to the raw
   transcript, and energy heuristics can't tell them from word releases); MISSING words
   = clipped/dropped; plus interior-pause anomalies and low-confidence rendered tokens.
   Born in testing: a mistimed ASR token clipped a word onset ('slash dot
   env' → '...env') and a ghost 'and it—' survived to the render; a careful listen caught
   both, now these tools do. Treat every finding as "listen here": explain each one or
   fix it — don't declare the cut good while the report has unexplained lines.
9. **USER AUDIT** — this is a hard gate, same as the plan step. Open the editor: `python tools/editor/server.py P` → http://localhost:8765. User drags keep/cut edges, adds cuts (I/O + C), compares raw vs edited playback; Save rewrites cuts.json (backup to `work/analysis/backups/`, appended to `changes.log`); Render button re-runs a preview. Iterate until approved.
10. **Final master**: `python tools/render_cuts.py P --style <chosen> --mode final` → `P/output/master-<style>.mp4` (source-resolution 10-bit HEVC with VideoToolbox or CPU). Two MANDATORY post-render steps:
   - **Timing review:** use `work/render-manifest.json` and `work/edited-transcript.json` from the actual encoded segments. Unknown/zero-duration source timing must be corrected before cutting. Verify retained speech with fresh ASR and listen to flagged joins; equal stream durations alone do not prove lip sync.
   - **Delivery compatibility:** retain the requested native master and make an H.264 review copy when needed. Inspect actual FPS/PTS and a representative frame before handing it off. Do not re-stamp FPS based on an old NVENC workaround without evidence.
11. **Handoff spine:** use the render-derived `work/edited-transcript.json`. Its `master_sha256` binds words to the exact rendered master. Fresh ASR is independent QA and must not silently replace that mapping. Re-render/invalidate dependent cues when cuts change.

Do steps 1–4 and 7 once; loop 5→6→8→9 until the cut is approved; then 10–11.

## cuts.json schema (what you author)

```jsonc
{
  "project": "video-1",
  "clip_order": ["0232", "0233", "0234", "0235"],   // concat order (assume filename order)
  "clips": [{
    "id": "0233",
    "file": "DJI_20260707121304_0233_D.MP4",         // raw MP4, relative to the project dir
    "duration": 245.3,
    "keeps": [ { "s": 7.32, "e": 13.13, "text": "...", "gap": {"d":0.89,"t":"silence"} } ],
    "cuts":  [ { "s": 2.18, "e": 5.04, "cat": "retake", "text": "...", "note": "why" } ],
    "fluff_suggestions": [ { "s": 40.1, "e": 44.0, "text": "...", "crit": "restated-idea",
                            "note": "...", "status": "suggested" } ]   // or "auto_applied"
  }],
  "styles": { "tight": {…}, "natural": {…} },         // timing knobs, below
  "flags":  [ { "id": 1, "clip": "0233", "at": "00:30", "issue": "...", "default": "keep both" } ]
}
```

- `cat` ∈ `retake | false_start | filler | long_pause | dead_air`. Times are raw seconds within that clip.
- **Keeps are never deleted.** A fluff span with `status:"auto_applied"` just *hides* the keeps it covers (undo = flip back to `"suggested"`). Reserve `auto_applied` for high-confidence fluff; leave the rest `"suggested"` (suggest-only — the renderer never drops suggested fluff).
- `flags` = judgment calls surfaced to the user with a `default`.

## Cut policy (how to decide)

Use the current project brief and source-understanding evidence to select an editorial profile.
For Studio projects, read `config/studio-workflow.json` and record its required source
understanding and strategy artifacts before substantive cuts. Talking-head tutorials,
interviews and personal stories need different pacing; no universal silence target applies.

- Identify the argument, prerequisites, qualifications, demonstrations and conclusion first.
- Treat apparent on-camera editing directions as contextual evidence: distinguish an actual
  instruction from quoted speech, a joke, or a demonstration before applying it.
- Remove confirmed retakes, false starts and unnecessary repetitions with a recorded reason.
- Preserve meaningful hesitation, emphasis, reactions, silence and personality.
- Leave uncertain removals suggested and flag their source timestamps for review.
- Do not assume clip filename order equals narrative order. Record the chosen sequence.
- Compare representative source and preview material before applying settings broadly.

## Style params (in `styles`, general knobs — no per-video constants)
`internal_gap` (split keeps into speech-run atoms at pauses ≥ this) · `min_tail`/`max_tail` (snap-to-audio tail range after a word) · `head` (lead-in before an atom) · `margin` (dB over noise floor that counts as "decayed") · `soft_gap` (a following gap ≥ this = section end → soft landing) · `soft_max_tail`/`soft_margin` (the softer landing).
Reference values that matched the reference cut: tight `{internal_gap:0.4, min_tail:0.14, max_tail:0.4, head:0.11, soft_gap:1.2, soft_max_tail:0.6, soft_margin:3.0}`; natural bumps `min_tail:0.26, max_tail:0.45, head:0.19`.

**Tune `head` to the SPEAKER, don't take the reference on faith.** `head` must exceed the speaker's
onset ramp — the lag between a word's first audible energy and the ASR token start — or every cut-in
clips a word attack. Measure it: for each atom start at a real cut join, walk the RMS envelope back
to the last point at/below floor+6 dB. On video-1 the ramp clustered at **0.18s**, so tight's 0.11
clipped onsets (14 hard entries) while 0.15/0.17 gave **0**. Sweep `head` against
`analyze_cut`'s hard-entry count and pick the smallest value that reaches zero — going further costs
real runtime (0.19 → 0.42 bought 3 fewer entries for +1:39 of lead-in).

**`soft_max_tail` is a ceiling, not a fixed value** — `snap_tail` returns early on clean endings, so
raising it only affects words that genuinely need a long release. Raise it if the video's last word
clips: video-1's `"...upcoming videos."` needed 0.90s to decay and 0.60 cut it off.

## The transcript lies about TIME — cross-check every suspicious span against the envelope

Word *text* is usually right; word *times* are not, and the cut engine trusts them completely
(`split_atoms` takes each atom's bounds from word times, so **no amount of keep-edge editing in
cuts.json can fix a mistimed token** — you must correct the token). Four failure modes, all seen on
video-1, all found with an RMS walk over `work/audio/<id>.wav`:

| Symptom | What it does to the cut | How it shows up |
|---|---|---|
| **Late start** (token begins after the word) | cut-in slices into the word | `analyze_cut` hard entry |
| **Inflated span** (word timestamped across seconds of silence) | dead air kept *inside* a keep | `verify_cut` big interior pause |
| **Merged repeat** (two utterances in one token) | a doubling you cannot see in the transcript | user says "it's twice", transcript says once |
| **Phantom** (token with no audio at all) | you cut a boundary into real speech | hard entry after a clamp |

Worst cases measured: `"post"` timestamped 66.60→72.40 hiding **5.24s** of dead air mid-sentence;
`"Connect"` 0.44s late; a doubled `"here's"` merged into one 1.03s token; a `"this."` with no audio.
Record every correction in `work/analysis/token-time-fixes.json` — `transcribe.py --force` wipes them.

Detector worth running before every preview: flag kept words whose duration exceeds ~1.0s, or whose
leading/trailing silence exceeds 0.35s. Discriminate real from false by asking whether the surviving
hot span could plausibly hold the word — 4 syllables in 0.17s means the detector tripped on a soft
onset, not a real inflation.

## Notes

- The cut engine (`tools/cutlib.py`) does word-aware segmentation, per-clip 10th-percentile noise floor, and snap-to-audio tails so word releases aren't clipped — you don't hand-tune tail padding, you tune the style knobs.
- **`plan_clip` takes the clip's `cuts` and will not let a segment extend into one.** Pass them. `snap_tail` walks forward until the audio decays, so when the material after an atom is cut SPEECH rather than silence it walks straight through and the cut words ride into the render (measured: 0.70s of a cut `"for quick demo—"` survived). This only bites on *intra-phrase* splices — the kind the user asks for during audit — because between original takes there is always silence. Corollary: with the clamp active, a cut boundary placed inside speech now hard-clips instead of silently over-including, so **place cut ends in the quiet between words** and re-check hard entries after every audit round.
- `render_cuts.py` re-encodes and records actual segment/frame/sample timing in the render manifest.
  Use current encoder capability probes and source properties, not historical fixed resolution/FPS
  defaults. See `docs/timeline-compatibility.md` and `docs/production-quality-workflow.md`.
- Review joins and actual synchronization. Equal stream lengths alone never prove lip sync.
- Adapt media to the actual Remotion composition's requirements and verify playback/rendered
  motion; avoid copying fixed portrait dimensions into a landscape project.
- Complete full normal-speed audiovisual review before final acceptance. Spot frames and
  transcript checks supplement it and cannot substitute for unavailable listening.

Handoff: an approved master + `edited-transcript.json` → **`$make-tsx`** (build the visual beats) and the rest of steps 2–5.

For render-side QA use `.venv/bin/python -m tools.verify_render PROJECT --style natural` (or the selected style). It extracts the exact manifest master and binds independent ASR to its hash; an older transcript cannot establish current render timing.
