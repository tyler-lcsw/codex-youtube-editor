# M4 first-release evidence

September 5, 2026. Local M4 Pro, Mac16,11, 24 GiB. This is functional qualification on short synthetic inputs, not a recreation of the upstream video or a claim of commercial-provider quality equivalence. Raw artifacts live in ignored `work/benchmarks/` on this checkout.

## Models actually downloaded and used

| Provider | Measured short trial | Result and boundary |
|---|---|---|
| Qwen3.5 4B, MLX 4-bit | About 4.2 GiB process-footprint peak | Direct and PAIR text replies, synthetic vision, streamed response interruption and subsequent response worked |
| Qwen3.5 9B, MLX 4-bit | About 6.9 GiB process-footprint peak | PAIR schema-validated ordinary JSON, vision and one tool call worked; tiny 512-token prompts can exhaust their output budget in reasoning |
| Qwen3 ASR + ForcedAligner, 0.6B 8-bit each | 2.09 GiB MLX peak; 6.87 s audio in 1.84 s | Models loaded sequentially under network denial; unknown confidence remains null; unresolved/zero-duration words block cutting |
| DeepFilterNet3 | Original 6.87 s trial around 0.106 s inference | Offline CPU cleanup and sample-count preservation; integrated video cleanup also passed |
| Qwen3 TTS 0.6B Base, 8-bit | About 5.59 GiB MLX peak for short adapter trial | Explicit synthetic reference, exact 300 ms scripted pause, valid WAV; fresh ASR recognized the intended two sentences |
| FLUX.2 Klein 4B, MFLUX Q4 | 7.30 GiB MLX generation peak, 7.36 GiB editing peak | 768×512 image generation and single-reference color edit worked; no multi-reference/large-canvas qualification |

MLX allocator peaks and macOS process footprints are different measures; neither equals whole-system consumption. During the bounded PAIR trials pressure remained normal (1), existing swap stayed at 865 MB and did not grow. Later in the full desktop session, swap was 1207.12 MB. An isolated repeated image run kept pressure at 1 and ended at 1199.12 MB swap (no increase). Session-wide swap growth cannot be attributed to one model from these observations. These results do not authorize long contexts or simultaneous heavy jobs. The 9B 6-bit candidate was not downloaded.

All exact repositories/revisions/file hashes are in `config/models.lock.json`. Python environments are frozen separately. Models are not committed. Media adapters require local pinned assets and run with OS networking denied. Optional LM Studio is proprietary; the core local media pipeline does not require it.

## PAIR findings

Embedding direct/proxy vectors matched exactly (2×768 finite values). PAIR completed-job records identified this same originating and serving node. Qwen MLX requests then exercised the proxy on 1234 and direct engine on 1235. This validates one-node routing and reporting, not multi-node scaling, failover or memory pooling.

Use canonical model keys `qwen3.5-4b` and `qwen3.5-9b` as loaded identifiers. A custom alias advertised by `/v1/models` failed PAIR routing. Missing-model requests failed rather than falling back.

The installed MLX runtime ignored the requested 4096-token context: actual windows were 123648 (4B) and 92672 (9B). CLI `--parallel 1` applies; the standalone SDK load experiment did not reliably apply its settings and was not retained. `tools.load_local_llm` verifies actual parallelism and records actual context. The helper restricts input to 2048 UTF-8 bytes and output to 1024 tokens; this is a request bound, not an engine-level 4K cap.

Thinking controls were unreliable. JSON-schema responses could put JSON only in `reasoning_content`, leaving the answer empty. These are failures. The helper accepts only final answer JSON that passes schema validation and rejects truncation. Closing an SSE response exercised client cancellation/continued availability; it does not establish a precise engine cancellation latency or recovery under node loss.

## Integrated workflow

`work/benchmarks/first-release/` contains a 24 kHz synthetic narration source, two rendered speech segments, derived transcript/manifest, DeepFilterNet cleanup, a locally rendered Remotion brand cutaway, a procedural pop mixed with ducking, and a 99-frame/3.3-second export. No hosted media was used. A separate two-segment HEVC VideoToolbox master also rendered and passed the same 11-word independent ASR comparison.

The integrated trial exposed a real sample-rate bug: trimming before resampling doubled 24 kHz audio when assembling 48 kHz PCM. Resampling now precedes sample-exact trimming, with a regression test. Cleanup and final cut muxes stage output before replacing a previous success.

Fresh ASR bound to the exact cut-master hash found 11 intended words, zero extra/missing/replaced words and one 60 ms word-timing review flag. All confidence scores are unknown, as expected for this provider. Final video duration is 3.300 s and audio 3.285333 s, a 14.667 ms end difference. Duration agreement is not proof of lip sync. Fractional-FPS and sample-count regressions are tested separately; a human audiovisual benchmark remains future work.

The cut editor loaded in the in-app browser. Its data endpoint, HTTP range playback, unchanged save with backup and rerender all passed on the nested fixture project. Rerender previously lost the nested directory; the corrected absolute path has a regression test.

Representative Remotion frames were visually inspected. A first generated image contained unwanted lettering and was rejected; a revised prompt/seed produced a clean background that was visually inspected. Both attempts and provenance were retained. Local model output still requires visual review. Narration was checked by independent ASR, not a human listening/likeness panel. No personal voice or face qualification is claimed.

## Codex compatibility

Astra and Sol each completed a bounded read-only workflow discovery check using the same eight repository files. Both selected the correct skills, explicit-reference narration command, approved native image handoff, avatar deferral and publication waiver. This proves workflow discovery, not identical creative output on a long production task. Reports: `work/benchmarks/{astra,sol}-discovery.md`; prompt: `tests/acceptance/prompts/discovery.md`.

Homebrew Codex CLI 0.146.0 was rejected for Astra; app-bundled CLI 0.153.4 succeeded. No global CLI or other host was reconfigured.

Publication tests/uploads were explicitly waived. Native hybrid approval/resume/import has contract tests; no hosted generation was executed. Generative music/SFX, avatar/video, complex image integration, long-form quality, other operating systems and remote workers remain unqualified.
