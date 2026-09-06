# Studio stability and basic-function test log

Run: September 5–6, 2026, M4. Synthetic production: **Stability QA September 5**,
under `~/Movies/Codex Studio`. This checks the application; it does not certify a
finished production or authentic supplied-footage editorial quality.

## Outcome

The reproduced Review crash is fixed. The basic workflows below passed through the
actual native application. Two usability corrections from this pass retain the Codex
model selection and prevent invalid feedback-status actions. Explicit accessibility
labels and startup window activation improve native control operation.

| Workflow | Result | Observed evidence |
| --- | --- | --- |
| Open Review before changing other tabs | PASS after fix | Original wrapper aborted with SIGABRT. Direct AVPlayerView opens in empty and populated projects; native and interactive checks passed. |
| Visit all five tabs with an empty new project | PASS | Review, Resources, Codex & QA, Brief & sources, Understanding each displayed its expected content without a crash. |
| Create a production; cancel creating another | PASS | New named folder/state created; Cancel preserved the active production. |
| Open/reopen a production | PASS | Native folder picker reopened the same project; brief, imports and feedback remained available. |
| Open a non-project folder | PASS, expected rejection | `/tmp` produced “Project does not exist; create it first.” Dismissing the alert preserved the current project. |
| Enter and save a brief | PASS on keyboard retest | “Development testers” and “Verify stable source editing” persisted and appeared after relaunch. |
| Add a resource link | PASS | `https://example.com` and label “QA resource” saved through the form and persisted. |
| Import footage | PASS | Native file picker imported the eight-second `raw.mp4`; UI listed source role and confirmed original preservation. |
| Import a document | PASS | `production-rules.md` imported through the same picker and appeared with document role. This test copy is not a replacement for repository policy. |
| Playback, pause and seek | PASS, transport check | Native player loaded 00:08 duration, entered playing state, advanced and sought. This is not a listening-quality assessment. |
| Capture a paused frame | PASS | UI confirmed capture and 2.000 s; matching immutable PNG receipt and source association persisted. |
| Save/reopen a frame note | PASS | Note and thumbnail reappeared after project reopen; timestamp remained 2000 ms. |
| Save a time range | PASS | New note stored 0–3500 ms; UI displayed “Range ends at 3.500 s”. |
| Draw/save/review a rectangle | PASS | Real drag saved normalized x=.1643, y=.3241, width=.2738, height=.2863. Clicking the saved timestamp restored the rectangle; native screenshot confirmed the overlay on the correct frame. |
| Add a rendered revision | PASS | Native picker registered `revision2.mp4`; it appeared separately in the Viewing and Replacement revision menus. |
| Address and reopen feedback | PASS | Explicit notes and replacement revision were recorded in history; reopening returned the fixture note to open. No owner acceptance was fabricated. |
| Reject invalid status actions in UI | PASS after improvement | Missing notes disabled all four actions. Allowed transitions and replacement requirements remain validated by the backend. |
| Save a provider preference | PASS | Selecting local-remotion persisted after navigation and relaunch. |
| Connect with ChatGPT subscription | PASS | UI reported “ChatGPT subscription · pro”; no API-key route used. |
| Run Astra and Sol from the app | PASS | Both returned the requested UI test response. Task `01a07403-6092-7343-9a44-ee307110c10a`; completion while another tab was open also worked. |
| Retain selected Codex model across tabs | PASS after fix | Sol previously reset to Astra when the view was recreated. AppStorage now preserves the choice; returning from Resources still showed Sol. |
| Stop an active task | PASS | Observed Working, pressed Stop Task, then observed the task leave running state. |
| Show QA gates | PASS | Expanded gate showed missing reviews rather than a false completion. No QA evidence was fabricated. |
| Export handoff | PASS | Header action generated the project handoff and displayed “Handoff copied for Codex.” |
| Open diagnostics from Help | PASS | Open Diagnostic Logs opened the Codex Studio logs folder in Finder. |
| Publication | EXCLUDED | User explicitly waived publication testing. No upload performed. |

## Crash evidence and diagnostics

The original macOS report was `CodexStudio-2026-09-05-192909.ips`. The Swift runtime
failed to initialize `_AVKit_SwiftUI.VideoPlayerView` superclass metadata. The fix
uses the public native AVPlayerView through NSViewRepresentable.

The original wrapper was temporarily restored for a negative control: exit -6 and
its exact fatal message were retained in the new session stderr file. The replacement
was restored immediately afterward. No subsequent Studio crash was observed during
this UI pass; the last Studio report was the deliberate 19:37 negative control.
Native checks verify durable events, app-specific report import and duplicate exclusion.
Logs and footage are local and excluded from Git.

## Test method and limits

The user explicitly authorized macOS accessibility scripting after the bundled
computer-use helper crashed with SIGTRAP in Array.remove(at:). AppleScript/JXA operated
actual controls, dialogs, selections and keyboard entry; a native mouse drag operated
the canvas. Computer-use inspection and screenshots later worked on Review, including
the saved rectangle. The helper remained intermittent on other views. Restoring a
minimized window helped in one case but did not explain every helper crash.

Initial AXValue-only edits could appear in controls without reaching SwiftUI state;
those were discarded as evidence and repeated with keyboard input. One synthetic URL
lost hyphens during scripted typing; the lossless example.com case was separately
verified. An initial PID-directed drag did not register; normal HID drag did. These
are recorded as automation limitations, not silently called application passes.
Standalone screen capture from the shell lacked permission; native Review screenshots
were obtained through the computer-use tool. No claims of pixel-perfect validation of
every view, full accessibility conformance, fresh sign-in enrollment, owner acceptance,
heavy model/media generation or finished-video listening/creative acceptance are made.

Fresh validation: **142 Python tests passed, 1 publication test deselected; 13 native
checks passed; skill audit and release build passed.** Independent review found no
blocking defects in the crash, diagnostic, accessibility, model-selection or feedback
validation changes. Native basic workflow acceptance is complete within this scope.

## Authentication follow-up — September 6, 2026

The owner reported a browser login that appeared successful without Studio showing an
account, followed by an unknown localhost error on retry. The original error was not
retained in the previous diagnostic format; its precise cause remains unconfirmed.
In the existing app, pressing Connect immediately reported ChatGPT subscription · pro,
confirming usable managed credentials were already present. This exposed a misleading
initial disconnected state. Code inspection also found duplicate login starts, stale
browser links, ignored completion failures and silently discarded refresh errors.

Changes: automatically check managed authentication when opening Codex & QA; keep one
pending login in the persistent client; expose Check sign-in and Cancel sign-in; bind
completion to the active login ID; clear completed/cancelled links; display failures;
close only Studio's owned connection after a login-start timeout with no returned ID.
Authentication logs contain fixed event/outcome metadata, not email, URLs or tokens.

| Check | Outcome | Evidence |
| --- | --- | --- |
| Existing account after app restart | PASS | Installed rebuilt app launched directly into Codex & QA and displayed ChatGPT subscription · pro without a Connect click or browser login. |
| Live managed login start/cancel | PASS | Separate temporary CODEX_HOME with file credential storage; real bundled Codex returned HTTPS URL and login ID, listened on localhost:1455, then confirmed cancellation and released the listener. No browser authorization or existing credentials changed. |
| Callback state and recovery | PASS | Eight native regression cases exercise the real Swift client over controlled JSON-line subprocesses: failure, duplicate attempts, existing account, early success, cancel/retry with stale completion, refresh failure, start timeout, and concurrent checking during login start. Full native suite: 21 checks. |
| Python regression suite | PASS | 142 passed; publication test excluded. |
| Subscription task dispatch | PASS | Fresh bounded no-tool requests completed with the expected response using both gpt-6-astra and gpt-5.6-sol. |
| Fresh browser authorization completed by owner | NOT REPEATED | Existing credentials already work. Tests do not prove the exact previously reported localhost failure is reproduced or resolved. No sign-out or credential reset was performed. |

The native computer-use helper still failed to inspect Studio; the user-approved
accessibility scripting fallback verified the live account label. These findings
supersede the earlier implication that the Connect-only test covered browser enrollment.

## Fresh browser sign-in and Check sign-in — September 6, 2026

The installed app was launched with a private temporary CODEX_HOME and file credential
storage. It initially showed ChatGPT sign-in required. The owner completed the browser
flow; Studio received login completion and automatically displayed ChatGPT subscription · pro.
No normal credentials were read, copied, deleted or reset. Both Astra and Sol completed
bounded no-tool requests through the native client using the newly authenticated profile.
This closes the previously untested fresh browser authorization path for this run; the
historical localhost error was not reproduced.

The owner then reported Check sign-in still appeared not to work. A direct accessibility
click produced a fresh successful account-check log, but no visible change: only initial
connection drove the Checking label. The client now publishes manual-check progress and
a timestamped result next to the button, prevents overlapping checks, and shows errors there.

A separate real Send to Codex attempt failed because the saved QA conversation was archived.
Studio now restores only the exact saved conversation identified by Codex's archived-session
error and retries resume once. It neither replaces history nor retries turn dispatch.
Regression coverage rejects unrelated failures and mismatched conversation IDs.

Installed-app verification after rebuild (normal profile restored): automatic Pro detection;
Check sign-in updated the visible confirmation from 3:30:37 PM to 3:30:51 PM; Send to Codex
restored the archived QA conversation and returned STUDIO_AUTH_OK with Astra; selecting Sol
and sending again returned STUDIO_SOL_OK on the same conversation. The app finished both
turns and returned to idle without an authentication or task error. Accessibility scripting
was used for native clicks, typing and result inspection. Final suite: 28 native checks,
151 Python tests and 33 subtests; publication testing remains excluded.
