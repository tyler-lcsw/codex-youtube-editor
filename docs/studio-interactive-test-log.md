# Studio stability and basic-function test log

2026-09-05. Development branch `codex/mac-production-app`; not release qualification.
User requested computer-use testing after reporting a crash on opening Review directly.

| Check | Outcome | Evidence / next action |
| --- | --- | --- |
| Open Review before any other changes (original build) | FAIL, reproduced | SIGABRT; Swift runtime cannot initialize `_AVKit_SwiftUI.VideoPlayerView` superclass metadata. Original macOS report 19:29:09. |
| Persist fatal runtime message | PASS | Restored original wrapper temporarily; process exited -6 and session stderr retained the exact fatal message. Replacement restored afterward. |
| Copy app-specific macOS crash reports on launch | PASS | Real reports imported into local app logs; unrelated reports excluded by native check. |
| Open Review in empty project (replacement player) | PASS, automated native launch only | Explicit `REVIEW_SMOKE_OK`, exit 0; not computer-use acceptance. |
| Open Review with existing fixture | PASS, automated native launch only | Normal LaunchServices start; `review_smoke_passed` then `session_ended` in session 281CBCB4-2BB6-44A0-89D9-CD0389C8A205. |
| Computer-use connectivity | BLOCKED | Finder inspection works. Studio inspection crashes SkyComputerUseService with SIGTRAP in `Array.remove(at:)`, including Resources as the initial screen. Simplifying the sidebar did not resolve it; that experiment was reverted. |
| Every tab without prerequisites | PENDING | |
| New/open/cancel project | PENDING | |
| Save brief and reference link; reopen | PENDING | |
| Import footage/document | PENDING | |
| Playback/pause/seek | PENDING | |
| Frame/rectangle/range annotation; reopen | PENDING | |
| Revision-specific resolution history | PENDING | |
| Provider preference persistence | PENDING | |
| Codex subscription connect/models/task completion | PENDING UI | Earlier transport probes are not UI acceptance. |
| QA display and handoff export | PENDING | |
| Open diagnostic logs through Help | PENDING | |
| Publication | EXCLUDED | User explicitly waived publication testing. |

## Limits and reproduction

The UI rows marked pending have **not** been tested by computer use. There are no
claimed interactive passes. This prevents native app acceptance and PR7 merge.
The helper report `SkyComputerUseService-2026-09-05-193950.ips` confirms the helper
crashed independently of Studio. Repeated helper restart/reset did not recover inspection.
Do not attribute that SIGTRAP to Studio or treat tests as a substitute for click-through QA.

Review regression: launch the built bundle with `open -n <app> --args --smoke-review
--project <folder>` (use an empty string for no project). Require both
`review_smoke_passed` and `session_ended` in the new session log. Direct executable
launch can leave a macOS app with no initial window, so its timeout is inconclusive;
use LaunchServices. No editing, inference, or publication occurs in this check.

Crash diagnostics: original player restored temporarily to demonstrate exit -6 and
fatal message persistence, then replacement restored. Latest validation: 34 focused
Python tests and 13 native core checks. Logs and footage remain local and uncommitted.
