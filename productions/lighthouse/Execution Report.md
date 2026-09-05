# The Little Lighthouse — executed production

Produced September 5, 2026 on the single M4 Pro with 24 GiB unified memory. The film tells a complete miniature story: a lighthouse fails, Pip traces the fault, closes a loose connection, waits, and brings the beacon back for a boat heading home. This exercises the qualified production workflow; it does not reopen deferred large-model parity.

## Deliverables

| Artifact | Verified result |
|---|---|
| Horizontal film | 1920×1080, 30 fps, 1,216 frames, 40.533333 seconds; −18.01 LUFS, −3.99 dBTP |
| Vertical adaptation | 1080×1920, 30 fps, 612 frames, 20.4 seconds; −18.21 LUFS, −4.05 dBTP |
| Stems | Narration, SFX and original music, each 1,945,600 samples at 48 kHz, stereo, 24-bit PCM |
| Packaging | One title, three 1280×720 JPEG thumbnail options, horizontal/vertical descriptions, SRT/VTT captions |
| Editorial handoff | Source script, generation recipes, cut/timeline recipes, cue map, proxy/editor, local tracker and hash-bound delivery inventory |

Open `videos/lighthouse/review.html` from the repository's local web server to watch both versions. The generated media is local and ignored by Git. The repository contains recipes and the recorded evidence in `delivery-manifest.json` and `generation-metrics.json`.

## Capabilities exercised

- **Voiceover:** five locally generated Qwen TTS beats using an explicitly identified, existing macOS-synthesized reference. The voice is fictional, not a personal likeness. The repair beat includes a scripted pause. A 0.82× tempo adjustment gives the narration more room.
- **Clean cut / transcription:** Qwen recognition and forced alignment, explicit kept intervals, source-preserving revision of two takes with invalid alignments, native H.264 preview and HEVC master, actual segment/sample mapping.
- **Clean audio:** DeepFilterNet cleanup with the original master preserved. Cleanup is exercised, not claimed to outperform a paid service or to improve every already-clean synthetic voice.
- **Image generation / editing:** original lighthouse and robot illustrations plus two single-reference edits: restored beacon and corrected blackout. The first supposedly dark image still glowed; visual review caught it. Images were generated at 768×512 within the qualified profile and upscaled for layout, not represented as native 1080p detail.
- **Remotion / TSX / fake screencast:** animated titles and cable connection; a screenshot-based diagnostic walkthrough, explicitly fictional; alpha overlays, a split view, a cutaway and a one-second insert. Crossfade, punch-in and color-grade timeline extensions are applied. The film uses animated illustrations, not model-generated character performance or footage of a real event.
- **Sound / music:** three procedural click/pop/tone cues, a small original deterministic score, ducked mixes, final loudness normalization and separate stems. The inherited ElevenLabs music was not reused because the catalog identifies rights tied to the upstream author's account. This is a bounded original composition, not arbitrary generative music/SFX parity.
- **Packaging / thumbnails / shorts:** three visual entry points under one title, no invented CTR prediction, and a standalone vertical adaptation with its own opening context and timed captions. The narrative format deliberately avoids the marketing skill's money/free promises and presenter-face conventions.
- **Brand setup:** project-specific teal/amber/cream art direction and vendored licensed fonts; the user's global channel identity is not invented or overwritten.
- **Editor / tracker / recovery:** raw proxy, HTTP data and 206 range responses, unchanged-cut save with backup, local tracker apply, and verified generation-cache reuse without new provider calls. General rendering remains a staged recipe, not a universal resumable scheduler.
- **PAIR:** the proxy and loaded-model preflight were exercised with two bounded 9B editorial requests and one 4B title request. All three exhausted 1,024 output tokens without a usable final JSON answer. The helper correctly rejected them; reasoning content was not used as output. Codex authored the final script and packaging. Both models were unloaded afterward. This is a remaining local-LLM reliability limitation, not evidence of a failed PAIR network hop, successful creative assistance, pooled RAM, or multi-node execution.

## Findings fixed during execution

1. **FFmpeg 9 stem export:** `-filter_complex_script` was rejected by the installed runtime. The exporter now uses the file-backed `-/filter_complex` syntax. A real regression test verifies the delayed cue, leading silence, channel format and exact duration.
2. **AAC cut placement:** input-side seeking at zero advanced a source by one AAC frame, about 21.3 ms. The cutter now decodes presentation-time audio, resamples, and trims by sample index before padding/fades. The render cache version was incremented. Regression coverage checks zero and nonzero starts. Every rebuilt source/master segment has zero measured offset at 16 kHz, with correlation above 0.9936. Decoding from the source start prioritizes timing correctness and can increase render cost for late cuts in long recordings; a reusable decoded-audio cache is a future optimization.
3. **Longer Remotion renders:** the original module-time font gate cancelled the vertical render after 28 seconds at frame 558. Font readiness now belongs to the mounted composition, after registry imports. The same 612-frame vertical render completed in 34.06 seconds. All fonts still load from vendored local files. See [Remotion's font-loading guidance](https://www.remotion.dev/docs/fonts) for the loading APIs; the failed and successful production runs are the regression evidence here.

Focused tests were run red before the FFmpeg/AAC fixes and green after them. Final suite: **97 passed, 1 publication test deselected**. TypeScript compilation passed. Successful Remotion renders ran with external network access denied and a single render worker. Local model workers used the configured 12 GiB allocation ceiling; the largest recorded image allocation was 7.361 GiB and TTS 6.004 GiB. These are provider allocations, not a claim about all macOS applications or total session swap behavior.

## Review and remaining limits

The final master and the final mixed film each independently transcribed to the intended **97-word sequence**, with no additions, omissions or substitutions. The source/master audio correlation check found zero placement offset for all five segments. These measurements do not establish subjective voice quality or physical lip sync.

The independent master recognizer reports seven pauses of at least 0.4 seconds and 42 word-time differences beyond its fixed 40 ms threshold. The pauses occur at sentence/story boundaries, including the deliberate diagnostic hesitation. Source/master waveform measurements resolve actual segment placement, while ASR word boundaries remain estimates. The final mixed recognition additionally assigns zero duration to “a” at 12.640 seconds; that is retained as a QA flag and was not used for cutting or captions. All canonical source timings used for the edit and subtitles are valid. No times were silently invented.

Visual inspection covered the opening, blackout, Pip, diagnostic click, before/after connection, waiting insert, beacon and ending, plus three vertical frames and all thumbnail options. The cursor target and excessive diagnostic zoom were corrected. The character artwork is a still illustration; this run does not demonstrate walking, acting, lip-synced avatars, or a moving model-generated boat.

**Human listening and creative acceptance are not claimed.** The outputs are ready to watch, with the timing flags documented. Publication, publication tests, hosted generation, personal avatar/voice onboarding, large generative video/music/SFX models, multi-reference images and additional PAIR nodes were not invoked. The associated interfaces remain retained.
