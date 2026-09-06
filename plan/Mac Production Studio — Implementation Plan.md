# Mac Production Studio Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Deliver a native Mac production workspace with subscription-authenticated Codex, source intake, durable review annotations and current policy gates.

**Architecture:** A SwiftUI/AVKit client calls a small JSON-over-stdio Python project bridge and a separate persistent Codex app-server process. Existing project files, tools, Remotion and QA remain authoritative. Imported media and user context live outside version control.

**Tech Stack:** Swift Package Manager (Swift 6.3 tools / Swift 5 mode), SwiftUI, AVKit, Foundation Process, Python 3.11 standard library, existing pytest dependencies, installed Codex app-server.

**Spec:** `plan/Mac Production Studio — Specification.md`

## Global Constraints

- Use ChatGPT sign-in and subscription access to Codex exclusively; no API-key login or API fallback.
- M4 24 GiB is the controller and initial worker; one heavy inference task at a time.
- Retain Remotion and authoritative production rules; no automatic publication; no publication tests.
- Preserve original assets and version-specific annotations; no automatic QA passes.
- Use dedicated worktree/branch, focused TDD, observed native launch, commit/push/review/merge.

## File map and shared contract

- `tools/studio.py`: one-request CLI dispatcher. stdin JSON `{method,project,params}`; stdout `{ok:true,result:...}` or `{ok:false,error:...}`. Calls project domain; errors never raw traceback/secrets.
- `tools/studio_project.py`: project store, imports, brief/resources/routes, immutable revision records, annotations/handoffs. Atomic state `PROJECT/work/studio/project.json` with `schema_version,title,brief,resources,assets,revisions,annotations,routes,codex_thread_id`.
- `tools/studio_workflow.py`: runtime stage definition, evidence snapshots, invalidation and production QA adapter.
- `config/studio-workflow.json`: ordered stage IDs and required artifacts; edits change behavior.
- `macos/Package.swift`: executable Studio and library StudioCore, Swift 5 language mode, macOS 14+; no third-party libraries.
- `macos/Sources/StudioCore/`: JSON values, bridge client, subscription-only Codex protocol and transport.
- `macos/Sources/Studio/`: app entry, observable workspace, intake/understanding/review/resources/Codex views.
- `macos/Tests/StudioCoreTests/`: transport, account boundary, parsing and frame-coordinate tests.
- `tools/build_studio_app.py`: release build, .app bundle metadata, ad-hoc signing. Output ignored `work/apps/Codex Studio.app`.
- `docs/mac-studio.md`: installation, operation, actual validation and remaining limitations.

### Task 1: Durable project and workflow bridge

**Files:** Create `tools/studio.py`, `tools/studio_project.py`, `tools/studio_workflow.py`, `config/studio-workflow.json`, `tests/test_studio.py`.

**Interfaces:** `dispatch(request:dict)->dict` consumes `{method,project,params}`. Methods: create/open; update_brief `{brief}`; add_resource `{url,label,role}`; import_media `{path,role}`; add_revision `{path,label}`; add_annotation `{asset_id,time_ms,end_ms,rect,text,frame_path,transcript_ids}`; update_annotation `{id,status,resolution_revision_id,note}`; set_route `{task,provider}`; set_thread `{thread_id}`; export_handoff; workflow; record_stage `{stage,evidence,reason}`; quality. Open/mutations return project state; export returns `{path,text}`; workflow returns definitions and computed states; quality returns production gates. Asset/revision fields: `id,path,sha256,label,role,duration_ms`; annotation `id,asset_id,asset_sha256,time_ms,end_ms,rect,text,frame_path,transcript_ids,status,resolution_revision_id,history`. Rectangle is `{x,y,width,height}` in normalized video coordinates; frame/time must refer to actual selected asset. New project creates all work subdirectories needed for transcript/analysis. Protect state against malformed paths/status/transitions/unknown providers. Resolve paths absolutely. Return JSON-safe values.

- [x] Write tests first: source unchanged after copy; corrupt/empty import rejected; brief saved/reopened; link rejects non-HTTP(S); annotation out-of-duration/rectangle rejected; resolution cannot point to unknown revision; old annotation immutable across revisions; workflow rule/brief/source changes stale stages; stage prerequisites/evidence required; no API route; handoff includes authoritative source paths and scoped resource choices.

```python
from tools.studio import dispatch
result = dispatch({'method':'create','project':str(tmp_path/'project'),'params':{'title':'Review'}})
assert result['title'] == 'Review'
assert (tmp_path/'project/work/studio/project.json').is_file()
```

- [x] Run `.venv/bin/python -m pytest tests/test_studio.py -q` and observe missing behavior.
- [x] Implement JSON store with existing `atomic_json`, `file_lock`, `file_hash`, ffprobe validation and content-addressed staged imports. Implement workflow definitions with deterministic content hashes and prerequisites; use current `production_quality.gate` for final status. All nontrivial evidence needs reason and nonempty files.
- [x] Pass tests, exercise stdin CLI, review spec/quality, commit this bounded component.

### Task 2: Subscription Codex client and native project workspace

**Files:** Create `macos/Package.swift`, `macos/Sources/StudioCore/{EngineBridge,CodexProtocol,CodexClient,ProjectSelection}.swift`, `macos/Sources/Studio/{StudioApp,Workspace,IntakeView,UnderstandingView,ResourcesView,CodexView}.swift`, `macos/Tests/StudioCoreTests/ProtocolTests.swift`.

**Interfaces:** EngineBridge sends Task 1 requests from background work with arguments, not shell interpolation. Foundation JSON dictionaries preserve unknown protocol fields. Codex client publishes transcript/events, account state, pending approvals, task ID, errors. Use installed app-server schema for exact initialize/account/thread/turn messages. Models requested are gpt-6-astra/gpt-5.6-sol, validate against discovered account availability. Account type must be chatgpt before turn. Launch forces `forced_login_method="chatgpt"`, `model_provider="openai"`; remove API credential environment entries. No account logout or external token handling. Pending approval responses support command/file change, questions and explicit denial for unsupported requests. Close/interruption terminates only the app-owned process/turn.

- [x] Write transport tests for split JSON lines, out-of-order response IDs, rejecting API account and missing auth, account switching mid-session, unknown request default denial, pending failure on process termination.

```swift
XCTAssertFalse(CodexProtocol.canRun(account: ["type": "apiKey"]))
XCTAssertTrue(CodexProtocol.canRun(account: ["type": "chatgpt"]))
```

- [x] Run `.venv/bin/python tools/build_studio_app.py --checks`; observe red, implement minimal protocol/transport, rerun green.
- [x] Implement window sidebar and persistent repo/project choices. Intake file panels/drop, editable brief/link/resource forms. Understanding shows stage status and evidence requirements. Resource choices are constrained to Task 1 provider list and handoff boundary.
- [x] Connect subscription sign-in/status/model selection, send current handoff plus user request, stream output, resume associated thread, interrupt, approve/deny/respond. Show meaningful errors, never mark tasks successful from process exit alone.
- [x] Live initialize/account read and bounded Astra/Sol text turn with tools prohibited in prompt and read-only sandbox; record results without credentials. Review spec/quality and commit.

### Task 3: Version-bound audiovisual review

**Files:** Create `macos/Sources/Studio/ReviewView.swift`, `macos/Sources/StudioCore/{ReviewGeometry,AnnotationContext}.swift`, `macos/Tests/StudioCoreTests/ReviewTests.swift`.

**Interfaces:** Review consumes Task 1 revision/annotation records. AVPlayer plays selected absolute path; The FFmpeg capture bridge captures a provenance-bound frame on pause and returns its actual presentation time. Geometry converts drag coordinates through aspect-fit video bounds to normalized rectangle; clicks on letterbox bars rejected. Frame capture and receipt are saved under project work/frames before add_annotation; UI uses the returned timestamp. Transcript selection attaches stable word IDs and range from render-derived transcript when available; absence clearly displayed.

- [x] Test aspect-fit offsets: 1920×1080 in 800×600 has 75pt top/bottom padding; video center maps `(0.5,0.5)` and padding fails. Test reverse drags and clipping edges.
- [x] Run Swift tests red; implement geometry green.
- [x] Build player, revision selector, pause/mark time, end-time field, drawable region, comments, source/transcript anchors and status history. Compare revisions without rewriting original anchors. Export handoff includes unresolved feedback; status acceptance remains a user action.
- [ ] Register two real fixture revisions, create/reopen annotation, demonstrate selected frame and before/after review in native UI. Review spec/quality and commit.

### Task 4: Package, full integration and release evidence

**Files:** Create `tools/build_studio_app.py`, `docs/mac-studio.md`; update README, AGENTS, implementation status, gitignore, implementation ledger and HTML plan.

- [x] Test bundle builder rejects missing executable/engine path; test bridge end-to-end via real subprocess with malformed request and source fixture. Run red then implementation.
- [x] Build release app with `swift build --package-path macos -c release`; bundle executable and Info.plist; ad-hoc codesign. Support `--engine` and local .app path without source-path hardcoding. No embedded secrets or media.
- [ ] Run full pytest excluding publication, Swift tests, skill audit, whitespace check. Launch .app via `open`, inspect native UI and exercise intake/review. Confirm external project data survives restart and subscription session behavior.
- [x] Reconcile current skills: generic editorial profiles replace upstream channel-specific defaults; current instructions remain authoritative. App agent reads workflow/rules before actions. Do not claim real-footage qualification from synthetic fixture.
- [ ] Write exact validation/limitations. Whole-branch review, fixes, commit/push/merge per standing authorization. Show installed development app and plan; report user-input-dependent gates honestly.

## Execution record

- Native account read and exact bounded Astra/Sol subscription responses succeeded on this M4. No API authentication, credentials copied, hosted media generation or publication occurred.
- Task 1 backend and Task 2/3 native code passed independent spec/quality review after fixes to prerequisite hashes, capture provenance, project selection and Codex dispatch races.
- Project-local Swift manifest overlay handles mismatched CLT private interfaces. Executable native checks replace unavailable XCTest on this CLT installation; they exercise the shipping StudioCore code.
- Native app build and launch succeeded. Interactive UI acceptance is pending: computer-use reported the Mac locked and unable to unlock. User was asked to unlock M4; no bypass attempted.
- Runtime workflow artifacts/instructions and Studio input-bound QA receipts integrate understanding with actual media-action/completion gates.
- Final native UI inspection and subsequent automatic merge remain pending that unlock. Authentic supplied-footage creative qualification remains a separate next production test.
