# Implementation status

Execution authorized September 5, 2026. Branch: `codex/local-media-migration`.
Source baseline: `a6ac742b44520fd3c6aeaf3cd754e113fa334fed` (fork main unchanged at fetch).
All work executes locally on M4 Pro, 24 GiB. Internal volume name `mbp` is cosmetic.

| Task | State | Evidence / remaining work |
|---|---|---|
| 1 Baseline | In progress | Source pinned; synthetic fractional clock fixture passes; human corpus and visual comparison pending |
| 2 Codex skills | In progress | Nine skills moved and discoverability audited; extended skills and dual-model exercise pending |
| 3 Mac runtime | In progress | FFmpeg installed; actual H.264/HEVC VideoToolbox and CPU probes pass; CUDA/path regressions fixed; full editor/Remotion trial pending |
| 4 Provider policy/jobs | Pending | |
| 5 Local ASR | Pending | |
| 6 Time mapping/QA | Pending | |
| 7 Voice | Pending | |
| 8 Sound/music | Pending | |
| 9 Images | Pending | |
| 10 Video/avatar/worker | Pending | |
| 11 Tracker/publishing | Pending | Upload root regression fixed; gates/receipts pending |
| 12 Upstream/extensions | Pending | |
| 13 Acceptance | Pending | No full-parity claim |

Baseline has no existing automated test suite. Initial regressions reproduced forced CUDA
decode and wrong upload root. Current focused suite: 9 passing tests including real FFmpeg
encoding. Human/identity quality gates remain open; no hosted generation or publishing done.
