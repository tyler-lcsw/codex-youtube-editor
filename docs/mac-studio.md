# Codex Media Studio for Mac

A developmental native workspace around the existing production engine. It retains Remotion, local inference, source files, provider approvals, and authoritative production QA. Codex uses ChatGPT sign-in and subscription access exclusively. There is no API-key entry or API fallback.

## How to use the app

Open **How to Use** in the sidebar for step-by-step help, or choose **Help for this tab** to read instructions without leaving your current screen. Search by a task or control name and use the section selector to narrow the results. **Copy example** copies a request for you to adapt; it does not send it to Codex.

The same guide is available as [a standalone user manual](how-to-use.html). Its editable source is `docs/user-guide.json`. **Reload help** reads updates from the configured engine repository; the installed app includes a fallback copy. After editing the source, run `.venv/bin/python -m tools.build_user_guide` to refresh the HTML, and rebuild the app to refresh its bundled copy. Current production rules remain authoritative. The [coverage audit](help-coverage.md) maps the guide to controls and skills.

## Build and open

On M4 with the existing Python environment, FFmpeg and Swift command-line tools:

```sh
.venv/bin/python tools/build_studio_app.py
open 'work/apps/Codex Media Studio.app'
```

The bundle is ad-hoc signed for local development, not notarized for distribution. It contains the native executable and an engine path, not your footage, credentials, Python environment or model weights. Choose another engine/Python/Codex path in Codex & QA if the checkout moves. The default Codex executable is the desktop application's bundled CLI. Source requires Swift 6.3 package tooling, with Swift 5 language mode and macOS 14+ APIs.

The installed command-line tools on the initial M4 have mismatched private/public PackageDescription interfaces. The builder supplies a project-local VFS overlay of the matching public interfaces; it does not edit developer tools. This CLT installation also lacks XCTest. `--checks` runs executable native behavior checks using the same StudioCore implementation, with failures producing a nonzero exit.

## Your workflow

1. Create a production folder (the default location is `~/Movies/Codex Studio`) or open one created by Studio. Import files or drag them onto Brief & sources. Copies are staged and hashed; originals remain untouched. Add the audience, purpose, pacing, required content and meaningful context. Links are labeled as source, reference or background; adding a link does not automatically download it. For a one-speaker podcast, use **Solo podcast visuals** to choose the canonical audio, optional camera and restrained, balanced or illustrative visual-density preference. This records setup only; it does not yet generate a waveform, proposal or render, and camera synchronization remains unverified.
2. Review the Understanding stages. The responsible AI documents the source's content, narrative and proposed edit using the current workflow definition. Existing evidence can be selected and recorded from the interface. Changing inputs or policy makes prior assessments stale.
3. Choose task-specific resource preferences. These are included in each handoff. Codex still checks actual provider readiness, qualified limits and approval scope before work. Local PAIR remains bounded assistance; its availability is not proof of useful editorial output. Native images remain a scoped capability/handoff until verified in the actual session; no automatic API substitution.
4. Open Codex & QA; Studio automatically connects and checks existing managed ChatGPT authentication. If signed out, Sign in with ChatGPT opens the Codex-managed browser login. Keep Studio open until its subscription status is confirmed. Only one browser attempt can be pending; its link and cancellation control survive tab changes. Check sign-in refreshes the account without starting another browser login and shows progress followed by a timestamped result beside the button. If localhost reports an error, check status first; if still signed out, cancel the pending attempt and start again from Studio instead of reloading an old callback page. Completion failures appear in the app, and finished or cancelled links are cleared. The app does not read or copy tokens. Choose Astra or Sol, describe the task, and send it. Current project context, resource choices and feedback accompany the request. Requests for approval and individual user questions are shown explicitly. Unknown request types are declined visibly. Stop task interrupts the app's current turn.
5. Add an output as a revision, or have Codex register the result through `tools.studio`. Review sources and revisions with native playback. For video, **Pause & capture frame** records the actual presentation time and a provenance-bound frame; a rectangular region, optional time range and transcript anchors can accompany the comment. For audio-only media, **Pause & mark time** records a frame-free moment with an optional range and transcript anchors; region drawing remains unavailable because there is no picture to mark.
6. Compare versions using the media selector. Feedback stays with its original asset/hash/time/frame. Select a replacement revision and enter a resolution note to move a comment through addressed, ready for review and accepted. Acceptance is your explicit action. Reopening keeps history. No automatic timestamp migration after an edit.
7. Refresh QA and inspect each phase's findings. Final playback/listening and user acceptance remain distinct from technical checks. Completion still requires the existing production-quality receipt. Nothing in Studio automatically publishes.

Export handoff copies a Markdown handoff and saves it inside the project. This can be given to desktop Codex independently; project state remains usable without an integrated session. Codex's task ID is associated with the project so later turns resume the same task. If Codex explicitly reports that this saved conversation is archived, Studio unarchives that exact conversation and retries resume once. It does not create a replacement conversation or retry a dispatched turn. Other errors remain visible without clearing authentication. Conversation history itself remains managed by Codex; the app's live transcript is not a second authoritative chat archive.

## Portable project data and engine interface

State is `PROJECT/work/studio/project.json`; staged originals are under `source/`, review outputs under `revisions/`, frame captures under `work/frames/`, and ordinary engine artifacts retain their existing paths. Avoid committing production folders containing personal footage/context. The app default stores them outside the repository; native build products and studio state are ignored.

The bridge reads a JSON request from stdin and writes one JSON response. It does not interpolate shell commands:

```sh
printf '%s\n' '{"method":"open","project":"/absolute/project","params":{}}' | .venv/bin/python -m tools.studio
```

Responses are `{ "ok": true, "result": ... }` or `{ "ok": false, "error": "..." }`. Methods cover create/open, brief/resources/imports, revisions, capture/annotation/resolution, provider preferences, task association, workflow evidence, QA status and handoff export. `capture_frame` returns `time_ms`; use that actual frame time when adding an annotation. Staged import hashes and capture receipts detect altered media or images. A resolution must point to an existing different revision.

Imported media records its actual `stream_types` (`audio`, `video`, or both). The
audio-first podcast contract is additive to the same project format: call
`set_podcast_settings` with `primary_audio_asset_id` and an optional
`camera_asset_id`. It also accepts `visual_density` as `restrained`, `balanced`
or `illustrative`; the default is `balanced`. Call `clear_podcast_settings` to return to a general
production. The primary selection must contain audio, the optional camera selection
must contain video, and one muxed asset may fill both roles. Studio never chooses a
source automatically or treats camera association as synchronization proof. Older
projects and assets remain readable; stream capabilities are probed when an older
asset is first selected. Active podcast settings are workflow-bound inputs, so a
change makes prior stage assessments stale.

Review supports media with no video stream. Audio-only annotations remain bound to
the exact selected asset and time but intentionally have no captured frame or picture
region. This capability does not imply that a branded waveform or visual proposal has
already been generated.

The first deterministic visual carrier is available through
`.venv/bin/python -m tools.podcast_stage`. Run `prepare PROJECT --show-title ...
--episode-title ... --speaker-name ...` to create `work/podcast/stage.json`; it
uses the canonical audio saved by **Solo podcast visuals** unless `--asset-id`
is supplied. Run `render PROJECT` to create `output/podcast-stage.mp4`. The
versioned contract binds the exact imported audio hash and duration, stores a
bounded streamed-RMS waveform, and drives an explicitly registered Remotion
composition at the requested FPS and dimensions. The renderer creates picture
with concurrency one, muxes the canonical audio, verifies audio/video streams
and duration, and only then atomically replaces a prior successful output.
Optional artwork must already be a hash-bound file under `media/`; the current
CLI does not expose artwork or chapter editing controls.

`config/studio-workflow.json` defines the editable ordered stages, prerequisites, instructions and required evidence artifacts. `docs/production-rules.md` remains the authoritative rule wording. These files are not copied into the app. Workflow changes and changed prerequisite assessments invalidate dependent evidence, including transitive dependencies. The workflow coordinator verifies hashes and evidence existence, not the truth of a narrative analysis.

For Studio projects, `production_quality run` enforces workflow prerequisites, defaulting to the edit stage. Use `--stage intake` or `--stage source_understanding` for appropriate earlier media preparation; do not misclassify cuts to bypass strategy review. Final QA receipts bind current Studio inputs and pre-final evidence so CLI tracking cannot accept an outdated brief/workflow.

The app uses Codex app-server private stdio, managed ChatGPT authentication, an explicit OpenAI provider, subscription account checks before every task, workspace-write sandbox with repository/project roots and network disabled pending approval. API credential environment values are removed. No global Codex configuration or credentials are rewritten. Selected provider routes are passed to the agent as policy; they are not an OS-level prohibition against arbitrary shell commands.

## Validation and boundaries

Baseline integration evidence: subscription account read identified ChatGPT Pro; exact bounded responses from both `gpt-6-astra` and `gpt-5.6-sol` completed over the native client. The probes requested no tools, file changes or media generation. These prove subscription transport, not full production quality or desktop-plugin parity.

```sh
.venv/bin/python tools/build_studio_app.py --checks
.venv/bin/python -m pytest -q --deselect tests/test_portability.py::test_upload_relative_paths_use_this_repository
.venv/bin/python tools/skill_audit.py
```

Optional `--account-only` checks managed sign-in; `--probe` runs the two bounded model requests using subscription usage. Neither reads credential contents. Build/test results and final UI evidence are maintained in `docs/implementation-status.md`.

This increment is not a general nonlinear editor, multi-user service, automatic distributed scheduler or App Store release. There is no automatic scene-understanding model or guarantee that local helpers equal Codex; the agent builds and verifies the content map using existing capabilities. Native image generation/plugin exposure still needs a session-specific capability test and scoped approval. Authentic supplied-footage qualification requires actual footage and complete audiovisual review; the synthetic interface fixture cannot satisfy that criterion. Publication testing remains explicitly excluded.


## Crash diagnostics

Help → **Open Diagnostic Logs** opens `~/Library/Logs/Codex Studio/`.
Each launch writes an immediately flushed `session-<id>.jsonl` containing lifecycle,
tab selections, engine operation names/exit status and error types. Matching `.stderr`
files preserve native fatal runtime messages, including Swift traps that ordinary
error handling cannot catch. On the next launch, Studio copies its latest macOS
`.ips` crash reports from `~/Library/Logs/DiagnosticReports/` into the same folder.
macOS may generate those reports after the process exits; an additional launch can
collect a delayed report. A missing `session_ended` means an unclean exit, not proof
of a crash (force quit, test termination and shutdown can also cause it).

Files are local only, created with owner-only permissions. Structured events omit
project content, prompts and credentials; native stderr/system crash reports can
contain paths and runtime details. Nothing is uploaded automatically. Startup prunes
older diagnostic files, retaining the latest 40 before adding current-session files
and importing up to 10 recent crash reports. A running session's output is not byte
capped. Review logs before sharing. If log storage cannot be opened, macOS system
logging receives a warning; system crash reporting remains independent.

See `studio-interactive-test-log.md` for actual stability-test outcomes and blockers.


The native basic-workflow acceptance record is `studio-interactive-test-log.md`.
Codex model choice persists across tab changes and launches. Feedback status changes
require a resolution note; only allowed transitions are enabled, and resolving a note
requires a replacement revision. The backend still independently validates each change.

Authentication diagnostics record account-check outcomes, login start/completion/cancellation and connection failures. They omit email addresses, tokens, login URLs and callback parameters. Detailed protocol errors are displayed in the app; they are not copied into structured authentication logs. A login-start timeout closes only Studio's owned app-server connection because no login ID is available to cancel safely. Stored credentials remain intact.

## Visual identity

The approved Precision Cut direction uses ivory (`#F5EBDD`), coral (`#F36B4F`),
and graphite (`#303234`). The app includes a Dock/Finder/About icon, sidebar brand
mark, native navigation symbols, text-and-symbol state badges and guided empty states.
Dynamic UI colors follow macOS appearance; text and buttons use contrast-adjusted coral
shades. Video production colors remain project-specific.

See [the visual identity and asset inventory](../plan/Codex%20Studio%20%E2%80%94%20Visual%20Identity.html).
The editable source is `macos/Brand/PrecisionCut.svg`; theme tokens are in
`macos/Sources/Studio/StudioTheme.swift`. Regenerate committed icon resources with
`.venv/bin/python tools/build_studio_icons.py` (macOS `iconutil` and librsvg's
`rsvg-convert` required only for regeneration). Normal app builds simply bundle the
committed resources. No external service is required to build or display the identity.

The application brand is **Codex Media Studio**. Its bundle identifier, internal executable name, saved preferences, existing project location (`~/Movies/Codex Studio`) and diagnostic location (`~/Library/Logs/Codex Studio`) remain stable for continuity. Existing projects need no migration.
