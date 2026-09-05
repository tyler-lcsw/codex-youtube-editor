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

Verification: 65 pytest tests passed (one publication test explicitly excluded), skill audit, Remotion TypeScript check and npm audit. Live evidence includes the 3.3-second synthetic edit → cleanup → Remotion cutaway → ducked SFX export and locally generated images. See the benchmark report for exact observations and limitations. No hosted media generation or publication occurred.

The next production video still needs the user's actual brand/reference inputs and ordinary editorial review. It is not necessary to recreate the original example video or set up additional PAIR nodes to use this release.

## Post-merge continuation

The setup/audit follow-up automates pinned DeepFilterNet archive installation and adds a read-only upstream comparison CLI. Archive hashes/path safety and unchanged-checkout audit behavior have focused regressions. The real pinned archive verified successfully, and the baseline-to-merge comparison produced a receipt. Full timeline-effect implementations and resource-heavy qualification remain outside this follow-up; the audit makes future upstream changes reviewable without enabling them automatically.
