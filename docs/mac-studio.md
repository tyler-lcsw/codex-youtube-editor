# Codex Media Studio for Mac

A developmental native workspace around the existing production engine. It retains Remotion, local inference, source files, provider approvals, and authoritative production QA. Codex uses ChatGPT sign-in and subscription access exclusively. There is no API-key entry or API fallback.

## How to use the app

Open **How to Use** in the sidebar for step-by-step help, or choose **Help for this tab** to read instructions without leaving your current screen. Search by a task or control name and use the section selector to narrow the results. **Copy example** copies a request for you to adapt; it does not send it to Codex.

The same guide is available as [a standalone user manual](how-to-use.html). Its editable source is `docs/user-guide.json`. **Reload help** reads updates from the configured engine repository; the installed app includes a fallback copy. After editing the source, run `.venv/bin/python -m tools.build_user_guide` to refresh the HTML, and rebuild the app to refresh its bundled copy. Current production rules remain authoritative. The [coverage audit](help-coverage.md) maps the guide to controls and skills.

## Build, install and open the current version

On M4 with the existing Python environment, FFmpeg and Swift command-line tools:

```sh
.venv/bin/python tools/build_studio_app.py --install
open "$HOME/Applications/Codex Media Studio.app"
```

Keep that exact app pinned in the Dock. It is the one canonical installed copy.
`--install` preserves the outer app directory that the Dock bookmarks, replaces only
its validated contents, and refuses to proceed while any Studio build is running.
The prior installed contents are retained under
`~/Library/Application Support/Codex Media Studio/Backups/` with a non-launchable
`.app-backup` suffix. This prevents a Dock bookmark or Launch Services from reopening
yesterday's build. The app footer identifies the running version, build and exact source
revision. A build without `--install` is only a work-tree artifact for validation; do not
pin or routinely open it.

The bundle is ad-hoc signed for local use, not notarized for distribution. It contains the native executable and an engine path, not your footage, credentials, Python environment or model weights. Its sidebar footer shows the app version, numeric build and exact engine source revision so an older installed copy is identifiable. Choose another engine/Python/Codex path in Codex & QA if the checkout moves. The default Codex executable is the desktop application's bundled CLI. Source requires Swift 6.3 package tooling, with Swift 5 language mode and macOS 14+ APIs.

The installed command-line tools on the initial M4 have mismatched private/public PackageDescription interfaces. The builder supplies a project-local VFS overlay of the matching public interfaces; it does not edit developer tools. This CLT installation also lacks XCTest. `--checks` runs executable native behavior checks using the same StudioCore implementation, with failures producing a nonzero exit.

## Your workflow

1. Create a production folder (the legacy-compatible default storage location is `~/Movies/Codex Studio`) or open one created by Studio. Use **Brief** for audience, purpose, pacing, required content and meaningful context. Import files or drag them into **Sources**; copies are staged and hashed while originals remain untouched. Links are labeled as source, reference or background, and adding a link does not automatically download it.
2. Open **Editing Styles** to choose the project’s editorial style. Every new style begins as an editable copy of the current master rule list. The checkbox beside each rule controls whether that wording is included in the selected project style; edit the wording and choose **Save style**. These project preferences are stored in `work/studio/editing-styles.json`, included in Codex handoffs, and bound to workflow evidence. The authoritative production-quality rules still apply in full.
3. Open **Workflow Guide**. A new or migrated project starts with a **Long-form YouTube** workflow; **Add Workflow** can add **Solo podcast**, **Short-form video**, **Clean audio**, **Tighten silence**, or **Thumbnail** workflows. A project may hold several named workflows. Switch the active workflow and use **Edit workflow inputs** to scope its sources and output revisions. Step states are evidence-based—Complete, Ready, Not started, Blocked, or Needs review—and Studio does not manufacture a completion percentage.
4. For a one-speaker episode, add a **Solo podcast** workflow. Its specialized setup then appears in **Sources**, where you choose canonical audio, optional camera and restrained, balanced or illustrative visual density. The setup is absent from ordinary projects. Podcast source settings are currently project-level, so multiple Solo podcast workflow instances in one project share that setup. Camera association remains separate from synchronization proof.
5. Choose task-specific resource preferences. These are included in each handoff. Codex still checks actual provider readiness, qualified limits and approval scope before work. Local PAIR remains bounded assistance; its availability is not proof of useful editorial output. Native images remain a scoped capability/handoff until verified in the actual session; no automatic API substitution.
6. A Workflow Guide step may open its relevant screen or choose **Prepare editable Codex prompt**. Preparation fills the text box in **Codex & QA** and navigates there; it never sends automatically. Review or change the wording, then explicitly choose **Send to Codex**. Studio checks managed ChatGPT subscription authentication, presents approval/questions explicitly, and offers **Stop task** for the current turn.
7. Add an output in **Revisions** or **Feedback**, or have Codex register it through `tools.studio`. Studio attaches UI-added revisions to the active workflow atomically; the Revisions list shows every workflow that owns each output. Choose **Review this revision** to open that exact file in Feedback. For video, **Pause & capture frame** records the actual presentation time and a provenance-bound frame; for audio-only media, **Pause & mark time** records a frame-free moment. Feedback remains tied to its exact source or revision.
8. Record only evidence actually reviewed in Workflow Guide. A bound source, output revision or related annotation change makes that workflow's evidence stale; unrelated selected-input changes in another workflow do not. Shared brief, editing-style, resource, policy or workflow-definition changes can require broader reassessment.
9. Refresh QA and inspect each phase's findings. Final playback/listening and user acceptance remain distinct from technical checks. Adding or selecting a workflow, preparing a prompt, importing a revision, recording evidence, or completing a render does not itself complete QA or authorize publication.

Export handoff copies a Markdown handoff and saves it inside the project. This can be given to desktop Codex independently; project state remains usable without an integrated session. Codex's task ID is associated with the project so later turns resume the same task. If Codex explicitly reports that this saved conversation is archived, Studio unarchives that exact conversation and retries resume once. It does not create a replacement conversation or retry a dispatched turn. Other errors remain visible without clearing authentication. Conversation history itself remains managed by Codex; the app's live transcript is not a second authoritative chat archive.

## Portable project data and engine interface

State is `PROJECT/work/studio/project.json`; project editing styles are readable JSON in `PROJECT/work/studio/editing-styles.json`; staged originals are under `source/`, review outputs under `revisions/`, frame captures under `work/frames/`, and ordinary engine artifacts retain their existing paths. Avoid committing production folders containing personal footage/context. The app default stores them outside the repository; native build products and studio state are ignored.

The bridge reads a JSON request from stdin and writes one JSON response. It does not interpolate shell commands:

```sh
printf '%s\n' '{"method":"open","project":"/absolute/project","params":{}}' | .venv/bin/python -m tools.studio
```

Responses are `{ "ok": true, "result": ... }` or `{ "ok": false, "error": "..." }`. Methods cover create/open, editing-style create/update/select/delete, workflow-instance create/select/input updates, brief/resources/imports, revisions, capture/annotation/resolution, provider preferences, task association, workflow evidence, QA status and handoff export. `workflow_instances` returns the six real templates and current per-project instances. `workflow` and `record_stage` accept a workflow ID so evidence is evaluated against that instance's bound inputs. Style mutations require the returned revision and SHA-256 so a stale screen cannot overwrite a manual file edit. `capture_frame` returns `time_ms`; use that actual frame time when adding an annotation. Staged import hashes and capture receipts detect altered media or images. A resolution must point to an existing different revision.

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

When a current transcript-bound episode map and visual-score revision exist, choose
**Podcast visual score** in Feedback to inspect the whole-episode density timeline and
chapter-scoped proposals. Each event records its purpose, treatment, transcript
anchor, provenance and camera policy. A required-note confirmation appends an explicit,
revision-bound owner decision: accept the proposal, reject it, or keep the continuous
base stage. Stale bindings disable decisions. A score revision, representative preview
or owner decision is still not a render or creative-quality acceptance; only accepted
current-revision events can be materialized into the separate
`work/podcast/stage-reviewed.json` descriptor.

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

For an owner-reviewed stage whose canonical audio is 25–45 minutes, exactly
1920×1080 and 30fps, run the technical qualification through the production
quality coordinator with `.venv/bin/python -m tools.podcast_qualification qualify
PROJECT --evidence PROJECT/work/edit-plan.md`. The command enforces current
edit-stage prerequisites, renders with one worker, samples child-process RSS and
macOS memory pressure, checks cache state, counts frames, probes streams and fully
decodes audio/video. Success requires exactly one video and one audio stream, with the
audio duration within 100ms of the target, container and frame-derived video duration.
It atomically publishes `output/podcast-qualified.mp4` and
`work/podcast/qualification/report.json` only after revalidating the reviewed
score; failures and interruptions retain attempt records without replacing the
prior success. The native qualification section is read-only, checks current source,
contract, score decision and output hashes before calling a saved success current, and
also requires the exact referenced production-quality action to have completed
successfully with the canonical worker command. Otherwise it labels the report as
historical evidence with bounded stale reasons. It deliberately
leaves visual inspection, normal-speed listening, owner acceptance and creative
acceptance pending.

`config/studio-workflow.json` defines the authoritative ordered stages, prerequisites, instructions and required evidence artifacts. `config/studio-workflows.json` defines the six contextual template labels, descriptions, routes and prompt starters shown in Workflow Guide. `docs/production-rules.md` remains the authoritative rule wording. A template presents the workflow for a purpose; it does not weaken prerequisites, prove progress or change QA authority. Workflow changes and changed prerequisite assessments invalidate dependent evidence, including transitive dependencies. The coordinator verifies hashes and evidence existence, not the truth of a narrative analysis.

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

Help → **Open Diagnostic Logs** opens the legacy-compatible diagnostic path
`~/Library/Logs/Codex Studio/`.
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
