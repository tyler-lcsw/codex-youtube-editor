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

### Audio-first visual podcast development — September 7, 2026

The approved [audio-first visual podcast concept](ideas/Audio-First%20Visual%20Podcast%20Mode.md)
and [multi-PR implementation plan](../plan/Audio-First%20Visual%20Podcast%20Mode%20%E2%80%94%20Implementation%20Plan.html)
target one speaker and a 25–45 minute episode. Audio is the canonical source; an
associated camera file is optional enrichment. Multiple speakers, diarization,
multicamera direction, synthetic presenters and publication remain outside this track.

The first contract slice adds explicit podcast source settings and durable imported
stream capabilities without changing the project schema version. It validates one
audio-bearing primary source and an optional video-bearing camera source, permits one
muxed file in both roles, preserves unknown and legacy project fields, and includes
active podcast settings in workflow evidence binding. A monotonic settings revision
prevents cleared settings from reviving older evidence while identical saves remain
idempotent.

The native setup slice exposes these choices in Brief & sources, adds restrained,
balanced and illustrative preferences, and states that setup does not yet generate
visuals or verify camera synchronization. Review can create provenance-bound time,
range and transcript annotations for audio-only assets without manufacturing a frame;
video assets retain frame capture and region drawing. Current evidence is 41 Studio
bridge tests, 31 native checks, a signed release build and an audio-only Review launch
smoke. The picker/save/annotation flow has not yet received a full interactive
accessibility pass.

The waveform-stage slice adds a versioned, strict descriptor bound to the exact
canonical imported audio; cached streamed-RMS extraction; and an explicitly
registered data-driven Remotion composition with calculated duration, resolution
and FPS. It renders picture with concurrency one, muxes the canonical audio,
verifies streams and duration, records output provenance, and preserves a prior
successful output on failure. A three-second synthetic silence/tone proof passed
at 320x180 and 1920x1080 with 90 H.264 frames, a 3.000-second AAC track, full
decode and representative-frame inspection. This is a deterministic visual
carrier, not long-form qualification or creative acceptance. Semantic visual
scores, camera synchronization/cutaways, captions, native render controls, a
25–45 minute pressure/throughput soak, normal-speed listening and owner review
remain later work.

The semantic-review slice adds strict episode-map and visual-score schemas bound to
the canonical audio, transcript bytes, podcast-settings revision and visual-density
preference. It supports an explicit unchanged base plus chapter card, quote/key point,
progressive list, comparison and image/source-card proposals. Score revisions are
content-addressed and immutable; owner decisions are append-only, require an explicit
action and remain bound to the exact current revision. Only accepted or keep-base
decisions can populate the separately derived reviewed stage descriptor, which is
revalidated both before rendering and immediately before publication so a mid-render
decision change cannot replace the prior output. Episode maps, current score bytes,
decisions, reviewed descriptors, transcripts, previews and visual assets participate
in workflow/completion binding, making downstream evidence stale after a semantic
change. Native Review adds an accessible episode timeline,
textual ranges, chapter details, optional representative previews and confirmed
accept/reject/base controls. The Remotion stage renders these five primitives while
retaining the waveform and respecting reduced motion. Current implementation evidence
is 180 Python tests plus 33 subtests, 35 native checks, a signed release build and a
clean Remotion typecheck. A four-second reduced-motion, accepted-only chapter-card
fixture rendered at 320x180 with verified audio/video streams and bounded duration,
covering the score-to-reviewed-stage-to-render integration. No semantic model has been
qualified, no authentic episode was rendered, and proposals, synthetic previews or
technical render success are not creative acceptance.

## Story production exercise

The September 5 lighthouse production extends the earlier short fixtures into a coherent 40.53-second horizontal story and a 20.4-second vertical adaptation. See `../productions/lighthouse/Execution Report.md` and the production specification in `plan/`. Deliverables include original local illustrations, narration, Remotion shots, captions, three thumbnails, a procedural score, aligned stems and a local viewing room.

This exercise found and fixed three issues: FFmpeg 9's removed `filter_complex_script` option, AAC input-seek priming that advanced one segment by 21.3 ms, and a module-time font gate that cancelled renders after 28 seconds. The audio cutter now trims decoded samples and uses cache revision `render-v4`; composition-mounted font readiness passed the same 34-second render that previously failed. Focused red/green tests and the full suite passed: **97 passed, 1 publication test deselected**.

The final film contains the exact 97-word intended transcript. Source/master audio correlation measures zero placement offset for all five segments. ASR boundary flags and human listening/creative review remain documented, not silently cleared. Both PAIR model sizes exhausted the production helper's bounded output budget in this exercise; its failure path worked, but useful local editorial assistance was not achieved. Deferred/hosted/publication boundaries remain unchanged.

## Production quality policy

`docs/production-rules.md` is the authoritative editable source for all production rules.
`tools.production_quality` provides runtime checklists, evidence-bound before/during/after
gates, action logging, delivery hashing, and completion receipts. Root instructions and
all production skills require this workflow; tracker completion/ready writes require a
current receipt. See `docs/production-quality-workflow.md` for operation and enforcement
boundaries. Existing outputs have not been retroactively certified. Full playback and
listening, and authentic supplied-footage qualification, remain distinct requirements.

## Native Mac production studio — development app

Approved native application plan: `../plan/Mac Production Studio — Implementation Plan.html`.
The app integrates intake/brief/resources, editable source-understanding workflow, native
AVKit playback, provenance-bound frame/rectangle/range feedback, revision-specific
resolution history, provider preferences, file-based handoff, and integrated Codex
app-server with managed ChatGPT subscription authentication. No API-key route exists.

Independent reviews corrected prerequisite-review revival, unrelated frame acceptance,
invalid resolution IDs, failed project selection, Codex dispatch/completion ordering,
stale brief reload, changed-file playback and shared annotation draft state. Media actions
now enforce Studio workflow prerequisites; completion receipts bind Studio inputs and
pre-final evidence so app and CLI cannot accept stale project context.

Current verification: **142 Python tests passed, one publication test deselected; 12 native
checks passed; skill audit passed; release .app built and ad-hoc signed.** Real native-client
account read identified ChatGPT Pro and bounded Astra/Sol subscription responses passed.
No API use, token copying, hosted media generation, remote-node setup or publication.

Installed development bundle: `~/Applications/Codex Studio.app`, with its engine set to
the retained `codex/mac-production-app` worktree until merge. Signature verification passed.
A final whole-branch review found and fixed stale cached QA display and completion
refreshes lost when leaving the Codex panel; the scoped re-review is approved.

The development app launched successfully, but native visual/playback/interaction
acceptance is **pending**: the computer-use tool reported M4 locked and unable to unlock.
The user was asked to unlock M4. Do not substitute the automated results for interactive
acceptance or merge the app as qualified until that gate is completed. A synthetic
Interface Demo production under `~/Movies/Codex Studio` is prepared for this UI check.
It is not authentic-footage editorial qualification. Native image/plugin parity remains
a capability-specific verification and scoped-approval boundary. See `mac-studio.md`.


### Review crash and stability investigation (2026-09-05)

The user reported a crash opening Review before making other changes. Reproduced
SIGABRT in Apple's `_AVKit_SwiftUI.VideoPlayerView` superclass metadata initialization.
Replaced the SwiftUI video wrapper with a direct `NSViewRepresentable` hosting the
public `AVPlayerView`. Native launch checks pass for empty and fixture projects.
Durable local diagnostics capture tab/engine/lifecycle events, fatal stderr and copied
macOS crash reports; the original failure was reproduced again to verify logging.
Focused validation: 34 Python tests and 13 native checks passed.

Interactive acceptance remains blocked, now by a separate **SkyComputerUseService**
SIGTRAP in `Array.remove(at:)` when inspecting Studio. Finder inspection works.
Resources-first launch and a reverted sidebar simplification did not resolve it.
No interactive pass is claimed. Track each basic function in
`studio-interactive-test-log.md`; keep PR7 unmerged pending that acceptance.


### Native basic workflow acceptance (September 5–6, 2026)

Completed the actual-app stability pass requested by the user; see
`studio-interactive-test-log.md` for per-function evidence and method limitations.
Create/open/cancel/reject-invalid-folder, brief/resource entry, footage/document import,
playback controls, immutable frame/range/rectangle notes, revision association, feedback
reopening, provider persistence, Astra/Sol subscription tasks, interruption, QA display,
handoff export and diagnostic-folder access passed. A native Review screenshot verified
the saved rectangle overlay. No new Studio crash occurred during the pass.

Fixed model selection resetting on tab changes, added explicit accessible labels,
activated the startup window, and disabled invalid feedback transitions or missing-note
actions. Fresh checks: 142 Python tests, publication excluded; 13 native checks; release
build/skill audit; independent review approved. This supersedes the earlier blocked
basic-interaction gate. Computer-use helper failures on some views remain an external
automation limitation; authentic-footage editing and final creative QA are still separate.

### Studio authentication recovery (September 6, 2026)

A reported browser login/retry failure exposed missing automatic account checks and
incomplete login lifecycle handling. Existing managed credentials were verified live
by Connect in the old app, then detected automatically on launch in the rebuilt app.
Studio now prevents overlapping logins, tracks pending links across tabs, supports
explicit account checks/cancellation, matches completion IDs, surfaces failure/refresh
errors and cleans up unknown callback state after start timeout. Structured auth logs
exclude credential and URL contents. Native regressions: 21 checks; Python: 142 passed,
publication excluded. Real isolated Codex login-start/cancel verified listener creation
and release. The owner's exact earlier localhost error and fresh browser completion
remain unverified; no credentials were reset. See the interactive test log.

### Precision Cut application identity (September 6, 2026)

Applied the user's approved A direction: ivory/coral/graphite. Added a clean editable
SVG master, full ICNS family and in-app PNG mark; the bundle registers and ships both.
Added adaptive theme tokens, native navigation symbols, state badges and useful empty
states. Brand colors are for the app; production styles remain project-specific.
The asset inventory records current assets and deferred document/technique/distribution
needs in `plan/Codex Studio — Visual Identity.html`.

Validation: 35 focused Python checks passed, including a new bundle regression observed
failing before implementation; release build and native dark Review layout inspected.
Token contrast ratios range from 5.57:1 to 10.92:1 for tested text pairs. The screenshot
helper remains intermittent outside Review, so this does not claim complete visual or
accessibility qualification across every screen and appearance.

### Editorial-technique research and development specification (September 6, 2026)

A research-only Studio expansion is documented in
`../plan/Editorial Techniques Research and Studio Development Specification.html`, with a
machine-readable draft technique catalog, illustrative style profile, draft decision
rules, a YouTube packaging-pattern catalog, and a test-first implementation roadmap. The
synthesis covers YouTube guidance, measured research, professional craft, dissenting
practitioner evidence, and directly inspected Atozy and Dr. Grande case studies. It
distinguishes long-form YouTube from short-form swipe-feed and advertising conventions;
it does not prescribe effects-per-minute or treat either creator as a template.

Current YouTube documentation now supports A/B testing titles, thumbnails, or their
combinations and selects by watch time. The installed packaging skill still describes a
thumbnail-only, fixed-title, CTR-centered contract; the roadmap records a narrow
source-alignment slice before further packaging development. No skill was changed in this
research pass.

No editing capability or authoritative production rule changed. Catalog/profile loading,
semantic proposals, technique controls, decision history, new render/audio handlers, and
authentic-footage qualification remain proposed work.

### Short-form research expansion (September 6, 2026)

The research now anticipates separate YouTube Shorts and TikTok support. The companion
`../plan/Short-Form Vertical Video Research and Studio Specification.html` and
machine-readable draft contract distinguish YouTube Shorts, organic TikTok, and TikTok
advertising from long-form YouTube and from each other. They cover classification and
upload envelopes, feed/search/profile acquisition, editorial archetypes, 9:16 composition,
versioned safe areas, captions, covers, native interactions, sound/remix rights, packaging,
analytics definitions, and cross-platform derivation from the reviewed source master.

The implementation roadmap adds a test-first short-form track: platform contracts,
separate briefs, reversible vertical composition, grounded short-form proposals,
platform-specific packages and rights records, native-metric observations, and one
unpublished YouTube Short plus one unpublished organic TikTok qualification from the same
authorized source. It rejects universal duration/cut/effect rules, cross-platform
engagement scores, advertising-to-organic transfer, and automatic center-crop workflows.
No short-form capability, upload, publication test, authoritative rule, or provider changed
in this research pass.

### Application name (September 6, 2026)

Renamed visible branding, the window/application name, Codex client title and build output to **Codex Media Studio**. The existing bundle identifier, executable, project folders and diagnostic paths remain stable so saved settings and existing productions continue to work.

## End-user help — September 6

Codex Media Studio now includes a **How to Use** tab and **Help for this tab** sheet.
The editable `docs/user-guide.json` contains 76 short articles across nine sections,
covering all native tabs/options, all 18 production skills and the separate browser
cut editor. Articles distinguish available, limited, retained and deferred functions.
`docs/help-coverage.md` maps the instructions to implementation; `docs/how-to-use.html`
is the standalone searchable/printable export. Both native help and HTML use the same
source. The native loader validates content and displays bundled fallback provenance.

Validation: 151 Python tests passed, one publication test deselected, 33 subtests;
24 native core checks passed and release build succeeded. Independent review corrected
missing split/insert shot descriptions, browser range constraints and publication wording.
Live native checks passed for no-project/no-auth help, missing-repository bundled
fallback, full-text search, clear, section filtering, Help menu navigation, contextual
sheet/Done preserving an unsaved brief draft, clipboard-only examples and reload.
Browser search, empty results, clear and copy passed; rendered layout was inspected.
The native CUA inspection service failed independently of Studio; AppleScript accessibility
provided the native interaction evidence. A native screenshot review was unavailable.
These are help/UI checks, not new qualification of media providers or authentic footage.

The tutorial assessment and chapter outline are in
`plan/Codex Media Studio — Tutorial Outline.md`. No tutorial was rendered: the recommended
first film demonstrates authentic footage editing, with a separate explanation of skills
that are deferred or require specific inputs. Production policy and actual audiovisual QA
still govern any later recording. Publication testing/uploads were not performed.

## Illustrated tutorial render — September 6

A 5:38 text-led tutorial is rendered and registered in the local Studio project
`~/Movies/Codex Studio/Studio Tutorial September 6`. It uses Remotion, procedural
chapter cues, a real exported Codex handoff, revision registration and the quality
coordinator. See `../productions/studio-tutorial/Execution Report.md` and its editable
scene/renderer sources. It teaches desktop handoff while the user's in-app authentication
issue remains unresolved; it does not claim a successful login or real-footage qualification.

Corrected MP4 passed full decode, 1080p30/10,140-frame/duration checks, decoded chapter
cue checks and frame inspection. Self-review found silent-track selection; explicit
FFmpeg maps repaired it without re-rendering the picture. Full normal-speed audiovisual
review, cue listening and owner acceptance remain pending; no completion receipt or
publication was issued. Media stays outside Git; reproducible sources are versioned.

### Fresh subscription sign-in and visible account checks (September 6, 2026)

Fresh browser authorization was completed by the owner in the installed app using an
isolated temporary Codex profile. Studio automatically recognized Pro; bounded native-client
requests with both Astra and Sol completed using the new login. The old localhost error
was not reproduced. Earlier fresh-login verification gaps above are superseded by this run.

Check sign-in previously refreshed the account without visible feedback after connection.
It now shows progress and a timestamped confirmation, signed-out instruction or failure
beside the button. Duplicate checks are suppressed. A reproduced archived-project-conversation
failure now restores that exact conversation and retries resume once, preserving authentication.
Validation: 28 native checks; 151 Python tests plus 33 subtests (publication test excluded).
