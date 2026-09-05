# Implementation status

First-release implementation is complete within the revised single-M4 scope. See `../plan/M4 First Release — Runtime and Memory Decision.md`, `setup-macos.md` and `benchmarks/first-release.md`. The supplied video is not a completion benchmark; resource-heavy parity remains deferred.

Execution authorized September 5, 2026, including model downloads/use. Publication functionality retained; publication testing explicitly waived. PR #1 merged into `main` at `a1903d1b86dbf47b3a8544119b427eee9c033a3d`. Baseline: `a6ac742b44520fd3c6aeaf3cd754e113fa334fed`. All execution occurred on this M4 Pro, 24 GiB; no remote-node setup or MBP control role.

| Area | First-release result | Remaining boundary |
|---|---|---|
| Codex | 18 native skills; Astra and Sol workflow-discovery checks passed | Full creative parity across models not claimed |
| Mac runtime | Actual H.264/HEVC VideoToolbox and CPU probes; local integrated export; editor data/range/save/rerender passed | Other OS/worker qualification deferred |
| Remotion | Retained kits, pinned packages, bundled licensed fonts; 90-frame network-denied render | Review each newly authored shot |
| Policy/jobs | Scoped native image approval, file locks, atomic metadata, artifact hashes and network-denied workers | General job cache is an extension utility, not every legacy tool's execution path |
| ASR/alignment | Real pinned Qwen models; render-bound independent verification | Null/zero timing blocks cutting; no calibrated confidence |
| Time mapping | Actual segment/sample manifest and derived transcript; 24 kHz/fractional-FPS regressions | Integrated trial has one 60 ms ASR timing flag; no blanket lip-sync claim |
| Voice | DeepFilterNet cleanup and Qwen TTS explicit-reference narration exercised locally | Human listening, personal likeness and difficult-noise equivalence unqualified |
| Sound/music | Existing catalog mixing and procedural UI effect integrated | General generative SFX/music deferred |
| Images | Klein generation + single-reference edit; native approval/import tests | Larger/multi-reference images deferred; native hosted generation not run |
| PAIR | Local embedding, MLX text/vision/tool call and forwarding exercised | No memory pooling, no multi-node test; context override not honored |
| Tracker/publication | Local tracker persistence/filter/resync tests; publication retained | Publication tests/uploads waived |
| Upstream | Original docs preserved, extension boundaries and merge procedure documented | Future upstream features need capability-specific qualification |

Verification: 94 pytest tests passed (one publication test explicitly excluded), skill audit, Remotion TypeScript check and npm audit. Live evidence includes the 3.3-second synthetic edit → cleanup → Remotion cutaway → ducked SFX export and locally generated images. See the benchmark report for exact observations and limitations. No hosted media generation or publication occurred.

The next production video still needs the user's actual brand/reference inputs and ordinary editorial review. It is not necessary to recreate the original example video or set up additional PAIR nodes to use this release.

## Current continuation state

PRs #1, #2 and #3 are merged. Setup verifies and stages the pinned DeepFilterNet archive; the read-only upstream audit compares local commits without changing the checkout. Timeline validation preserves unknown fields/reused asset references and stages final exports. Registered v1 crossfade, punch-in and grade handlers preserve time; reusable Remotion components and a 90-frame visual proof are included. Pixel tests include an output effect after an insert. See `timeline-compatibility.md`.

The acceptance runner records bounded Astra/Sol discovery, timeline and recovery scenarios with unique attempts, logs, hashes and explicit unreviewed status. It never converts a successful command exit into creative approval. Recovery reviews identified gaps that are now covered by regressions: one-time native dispatch markers, import repair in separate attempt folders, scope revalidation and cleanup of surviving child processes after the leader exits.

Remaining limits are listed in `known-limits.md`. General job-cache integration across all legacy commands, full creative/identity parity, large media models and multi-node scaling are not claimed. Ordinary production work needs the owner's footage/brand/reference inputs and review; it does not require the upstream example video.

## Story production exercise

The September 5 lighthouse production extends the earlier short fixtures into a coherent 40.53-second horizontal story and a 20.4-second vertical adaptation. See `../productions/lighthouse/Execution Report.md` and the production specification in `plan/`. Deliverables include original local illustrations, narration, Remotion shots, captions, three thumbnails, a procedural score, aligned stems and a local viewing room.

This exercise found and fixed three issues: FFmpeg 9's removed `filter_complex_script` option, AAC input-seek priming that advanced one segment by 21.3 ms, and a module-time font gate that cancelled renders after 28 seconds. The audio cutter now trims decoded samples and uses cache revision `render-v4`; composition-mounted font readiness passed the same 34-second render that previously failed. Focused red/green tests and the full suite passed: **97 passed, 1 publication test deselected**.

The final film contains the exact 97-word intended transcript. Source/master audio correlation measures zero placement offset for all five segments. ASR boundary flags and human listening/creative review remain documented, not silently cleared. Both PAIR model sizes exhausted the production helper's bounded output budget in this exercise; its failure path worked, but useful local editorial assistance was not achieved. Deferred/hosted/publication boundaries remain unchanged.
