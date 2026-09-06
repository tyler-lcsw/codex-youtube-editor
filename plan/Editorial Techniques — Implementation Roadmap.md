# Editorial Techniques — Implementation Roadmap

Status: implementation proposal. No work below is authorized merely by this document.
The sequence assumes focused TDD, one vertical slice at a time, the existing production
quality coordinator, and the M4 first-release constraints.

## Outcome

Studio should help an editor choose *why* a beat needs treatment, propose a small set of
content-grounded techniques, preview them reversibly, and learn explicit preferences over
time. Its packaging companion should propose a recognizable, truthful title-thumbnail
promise and learn from YouTube's current watch-time experiments. It should not become an
effects generator, a retention-score optimizer, or a keyword-stuffing tool.

## Current baseline

The repository already proves source preservation, verified transcript/timing workflows,
cuts and pause handling, revision-bound annotations, workflow evidence, timeline shot
types, and preserve-time `crossfade`, `punch-in`, and `color-grade` rendering. Catalog and
procedural sound effects plus licensed music mixing exist. Authentic raw-footage editorial
qualification is still pending, so “implemented” and “creatively qualified” remain
separate states.

The missing product layer is the semantic technique system: catalog loading, versioned
profiles, per-video choices, grounded proposals, decision history, generic audiovisual
handlers for several techniques, and goal-specific evaluation.

## Dependency order

```text
catalog + profile contracts
          |
          v
Studio technique palette ---> grounded proposals ---> reversible preview/apply
          |                           |                         |
          +---------------------------+-------------------------+
                                      v
                         decision history + profile learning
                                      |
                                      v
                          authentic-footage qualification
```

## Slice 0 — Freeze data contracts

**Purpose:** turn the planning drafts into validated runtime contracts without changing
editing behavior.

**Likely files (maximum five):**

- `schemas/editorial-technique-catalog.schema.json` (new)
- `schemas/editorial-style-profile.schema.json` (new)
- `tools/editorial_techniques.py` (new)
- `tests/test_editorial_techniques.py` (new)
- `config/studio-workflow.json`

**Tests first:** reject unknown technique IDs, duplicate IDs, invalid parameter ranges,
profile/catalog version mismatch, and any profile that claims authority over production
rules. Reject evidence claims that omit platform/surface/format applicability. Preserve
unknown extension fields for forward compatibility.

**Acceptance:** the draft catalog and example profile validate; failures point to an exact
JSON path; no render or project file changes.

## Slice 1 — Per-project profile and decision ledger

**Purpose:** make taste and one-off decisions durable without conflating them.

**Likely files:**

- `tools/studio_project.py`
- `tools/studio_workflow.py`
- `tools/editorial_techniques.py`
- `tests/test_studio.py`
- `tests/test_editorial_techniques.py`

**Data additions:** project pins a catalog version and optional style-profile version;
each proposal records goal, anchors, alternatives, risks, confidence, owner disposition,
and the source/output revision. The ledger is append-only; supersession is explicit.

**Tests first:** a rejected proposal cannot silently reappear; a decision against revision
N is stale after a relevant N+1 edit; a single acceptance cannot mutate the profile;
unknown fields round-trip.

**Acceptance:** resume reconstructs exactly which preference was durable and which decision
was local to a revision.

## Slice 2 — Studio technique palette

**Purpose:** let the owner set video-level intent before proposals are generated.

**Likely files:**

- `macos/Sources/Studio/ResourcesView.swift`
- `macos/Sources/Studio/UnderstandingView.swift`
- `macos/Sources/StudioCore/CodexProtocol.swift`
- `macos/Tests/StudioCoreTests/ProtocolTests.swift`
- `tests/test_studio.py`

**Interaction:** group techniques by goal, show evidence/capability labels, expose
`preferred`, `allowed`, `ask`, and `disabled`, and let the editor set restraint, captions,
music, and motion preferences. “No intervention” remains visible. Show that current,
prototype, and planned capabilities are different. Keep long-form, Shorts, TikTok/Reels,
and advertising profiles separately scoped; do not inherit scroll-stop defaults into a
long-form project.

**Tests first:** serialization parity between Swift and Python; keyboard and VoiceOver
labels; no unsupported technique can appear as ready; production policy cannot be toggled.

**Acceptance:** a video-specific selection round-trips through Studio and remains distinct
from the reusable style profile.

## Slice 3 — Content-grounded proposal engine

**Purpose:** produce editorial proposals from source understanding rather than timers.

**Likely files:**

- `tools/editorial_techniques.py`
- `tools/studio_workflow.py`
- `tools/studio.py`
- `tests/test_editorial_techniques.py`
- `tests/test_studio.py`

**Inputs:** reviewed transcript, content map, editorial strategy, visual anchors, selected
catalog/profile versions, available assets, and current revision. The model may rank a
small candidate set, but deterministic validation enforces ranges, prerequisites, and
conflicts.

**Required output:** exact semantic trigger; source time; goal; one or more alternatives;
no-change option; proposed parameters; asset provenance; risks; confidence; and capability
label. It must not output a universal “retention score.”

**Tests first:** no proposal without a source anchor; no contradictory technique pair;
no unsupported asset; dense cue clusters trigger a warning; the same structured input is
schema-valid across Astra and Sol even if creative choices differ.

**Acceptance:** proposals are reviewable editorial hypotheses, not automatic timeline
mutations.

## Slice 4 — Apply the proven visual vocabulary

**Purpose:** connect proposals to capabilities already rendered and pixel-tested.

**Likely files:**

- `tools/timeline_extensions.py`
- `schemas/timeline.schema.json`
- `remotion/src/lib/extensions/effects.tsx`
- `tests/test_timeline_extensions.py`
- `tests/test_timeline_effect_render.py`

**First techniques:** motivated reframe/punch-in, bounded desaturation or color grade, and
crossfade only where a proposal justifies it. Keep source-time semantics and existing
unknown-field compatibility.

**Tests first:** boundary frames, overlap conflicts, default interpolation, no frame before
or after the range changes, and golden-pixel proof for intensity extremes.

**Acceptance:** Studio can preview, accept, render, and revert these interventions while
the decision ledger and output revision stay synchronized.

## Slice 5 — Evidence cutaways, highlights, and selective text

**Purpose:** prioritize information-bearing visual support.

**Likely files:**

- `schemas/timeline.schema.json`
- `tools/timeline_extensions.py`
- `remotion/src/lib/extensions/effects.tsx`
- `tests/test_timeline_extensions.py`
- `tests/test_timeline_effect_render.py`

**Contract:** every asset carries source/license/provenance plus the claim or concept it
supports. Add bounding-box or region highlights and readable selective text. Avoid a
generic stock-footage keyword inserter.

**Tests first:** missing provenance fails; color is not the only highlight channel; text
read time is flagged; source aspect/fit is deterministic; captions and overlays cannot
occupy an unresolved collision region.

**Acceptance:** representative renders demonstrate evidence, comparison, and orientation
uses, with truthfulness and readability dispositions recorded.

## Slice 6 — Audio continuity and restraint

**Purpose:** implement split edits and better music/SFX decisions before novelty voice
effects.

**Likely files:**

- `tools/timeline_extensions.py`
- `tools/mix_music.py`
- `tools/mix_sfx.py`
- `tests/test_timeline_extensions.py`
- `tests/test_audio_assets.py`

**Techniques:** J/L cuts, room-tone handles, music arcs/drops, and sparse sound punctuation.
All gains remain subordinate to speech intelligibility; audio boundaries use verified
source timing.

**Tests first:** negative/positive audio lead bounds, no clipped phonemes, loudness/peak
constraints, music ducking around speech, missing-room-tone behavior, and deterministic
mixes.

**Acceptance:** actual listening plus signal checks demonstrate smooth continuity and clear
dialogue; successful FFmpeg execution alone is insufficient.

## Slice 7 — Time and emphasis experiments

**Purpose:** add freeze/replay, process compression, and optional vocal timbre as separately
gated experiments.

**Likely files:**

- `schemas/timeline.schema.json`
- `tools/timeline_extensions.py`
- `tools/time_map.py`
- `tests/test_time_map.py`
- `tests/test_timeline_effect_render.py`

**Order:** freeze/replay first; speed/process compression second; vocal timbre only after a
provider decision. The pinned Remotion version does not currently include the documented
`@remotion/media` pitch support, so choose and qualify either a dependency upgrade or a
tested local FFmpeg path—never silently substitute pitch for formant-safe timbre.

**Tests first:** monotonic reversible time maps; transcript/caption remapping; boundary
audio continuity; freeze-frame duration; replay provenance; parameter extremes; and
round-trip behavior with legacy timelines.

**Acceptance:** each technique passes its own visual/listening gate and is still labeled
prototype until authentic footage proves comfortable M4 performance and creative quality.

## Slice 8 — Feedback and analytics loop

**Purpose:** help the owner refine taste without pretending observational data proves
causality.

**Likely files:**

- `tools/editorial_techniques.py`
- `tools/studio_project.py`
- `macos/Sources/Studio/ReviewView.swift`
- `tests/test_editorial_techniques.py`
- `macos/Tests/StudioCoreTests/ReviewTests.swift`

**Interaction:** capture accepted, changed, rejected, and deferred decisions with reasons;
offer a profile change only after repeated, comparable evidence and explicit owner
confirmation. Imported retention events remain separate observations with possible
explanations, not rewards directly assigned to an edit.

**Tests first:** no automatic profile mutation; analytics cannot bypass owner confirmation;
comparisons require compatible format/duration/audience metadata; deletions are soft and
auditable.

**Acceptance:** Studio can explain what it learned, from which decisions, and how to undo a
profile revision.

## Slice 9 — Authentic-footage qualification

**Purpose:** close the gap between synthetic correctness and real editorial readiness.

Use owner-authorized, local footage only. Run intake, source understanding, editorial
strategy, proposal review, preview/apply, render, independent ASR, frame review, listening,
and all three quality gates. Compare a restrained edit with at least one plausible
alternative; do not publish or upload.

**Acceptance:** the actual deliverable and evidence are registered with `tools.studio` and
the quality coordinator; `require_complete(project)` passes for that revision; unsupported
or weak techniques remain visibly deferred.

## Packaging track P0 — Reconcile the current YouTube contract

**Purpose:** correct a drifted assumption before building UI or data around it. YouTube now
supports up to three variants for title-only, thumbnail-only, or title-and-thumbnail tests
and chooses by watch time. The current packaging skill still describes native testing as
thumbnail-only with one fixed title and treats CTR as the isolated objective.

**Likely files (maximum five):**

- `.agents/skills/packaging/SKILL.md`
- `.agents/skills/thumbnail/SKILL.md`
- `.agents/skills/packaging/references/channel-calibration.md`
- `tests/test_skill_contracts.py`
- `docs/implementation-status.md`

**Tests first:** prohibit claims that Test & Compare is thumbnail-only or CTR-selected;
require explicit mode and watch-time result; preserve one-title/three-thumbnail as a valid
thumbnail-only mode; keep Shorts out of this long-form workflow.

**Acceptance:** active instructions match current first-party documentation while retaining
all source, approval, identity, and quality gates. This research pass does not perform the
update.

## Packaging track P1 — Versioned template and packaging profile

**Purpose:** separate stable channel-recognition tokens from each video's story content.

**Likely files:**

- `schemas/youtube-packaging-profile.schema.json` (new)
- `tools/packaging.py` (new or existing packaging module, if introduced first)
- `tools/studio_project.py`
- `tests/test_packaging.py` (new)
- `config/studio-workflow.json`

**Contract:** template ID/version; type roles; creator/logo anchors; safe zones; accent
palette; semantic-subject slot; overlay-copy slot; search/browse intent; current YouTube
test contract; and explicit provenance/identity/policy reviews. Store title, thumbnail, and
opening payoff as one promise object.

**Tests first:** profile version mismatch, missing font/license, unsafe overlay zone,
unapproved likeness, title-thumbnail contradiction, and template migration with unknown
field preservation.

**Acceptance:** the Dr. Grande pattern can be represented as a case profile without copying
its black box, wordmark, face, phrasing, or exact placements into a house default.

## Packaging track P2 — Deterministic template compositor and browse-wall QA

**Purpose:** make repeated brand structure precise while keeping image sourcing/generation
explicit and separately approved.

**Likely files:**

- `tools/gen_thumbnail.py`
- `tools/thumbnail_template.py` (new)
- `tools/production_quality.py`
- `tests/test_image_spec.py`
- `tests/test_production_quality.py`

**Behavior:** composite approved story imagery, creator signature, logo, and typography
deterministically at final canvas size. Generate a labeled A/B/C contact sheet plus Home,
Suggested, Subscription, and Search size previews. Run spelling and safe-zone checks before
creative review.

**Tests first:** pixel-stable anchors, font fallback failure, text overflow, crop behavior,
file/spec limits, provenance, and no overwrite without preserving the prior variant.

**Acceptance:** an editor can recognize the template with titles masked, read the hook at
browse size, and still identify the video-specific subject.

## Packaging track P3 — Joint title-thumbnail proposals in Studio

**Purpose:** reason about packaging as a single honest promise.

**Likely files:**

- `macos/Sources/Studio/ResourcesView.swift`
- `macos/Sources/Studio/ReviewView.swift`
- `macos/Sources/StudioCore/CodexProtocol.swift`
- `macos/Tests/StudioCoreTests/ReviewTests.swift`
- `tests/test_studio.py`

**Interaction:** select search, browse, or subscriber intent; display verified entities and
front-loaded truncation previews; show the title, thumbnail, and opening payoff together;
offer up to three meaningfully different hypotheses under an explicit current test mode.
Require one-second read and masked-title brand-recognition review.

**Tests first:** accessible labels, Unicode/title limits, exact overlay spelling, no hidden
truncation of the primary entity, distinct-hypothesis requirement, and no unsupported test
mode presented as ready.

**Acceptance:** the owner can compare three packages, understand what each tests, and trace
every important claim/image back to the video and approved sources.

## Packaging track P4 — Test-result and template-learning ledger

**Purpose:** learn which packaging grammar works for this channel without mistaking
correlation for a universal rule.

**Likely files:**

- `tools/packaging.py`
- `tools/studio_project.py`
- `macos/Sources/Studio/ReviewView.swift`
- `tests/test_packaging.py`
- `macos/Tests/StudioCoreTests/ReviewTests.swift`

**Data:** test mode, concurrent variants, hypothesis, start/end, watch-time result and
certainty label, impression/audience context when available, owner interpretation, and
template version. CTR may be contextual data but cannot replace the native result.

**Tests first:** performed-same/inconclusive cannot become winners; sequential third-party
tests are labeled separately; a result cannot mutate the template automatically; early and
late audience composition is retained as a caveat.

**Acceptance:** Studio can propose a controlled template evolution and explain the evidence,
while the owner explicitly approves any durable brand-profile change.

## Cross-cutting test matrix

| Concern | Required proof |
|---|---|
| Semantics | transcript/content-map anchor and preserved qualification |
| Timing | integer-millisecond source anchors, render-derived output map |
| Visual | representative/boundary frames and pixel assertions where deterministic |
| Audio | normal-speed listening, loudness/peak checks, independent ASR |
| Accessibility | caption accuracy, readable text, non-color cue, reduced-motion review |
| Provenance | source/license/consent for every external or generated asset |
| Performance | one heavy job at a time; measured M4 pressure and runtime |
| Compatibility | legacy/unknown-field round trips and pinned version fixtures |
| Taste | owner disposition tied to proposal and revision |
| Packaging | title-thumbnail-opening promise trace, masked-title recognition, real-size previews, current watch-time test contract |

## Release gates

1. **Contract gate:** catalogs and profiles validate and migrate safely.
2. **Proposal gate:** grounded alternatives are useful without changing a timeline.
3. **Capability gate:** each handler has deterministic and audiovisual proof.
4. **Studio gate:** owner can select, preview, reject, revise, and revert accessibly.
5. **Qualification gate:** authentic local footage completes the existing quality
   workflow. Publication remains separately authorized and out of scope.
6. **Packaging gate:** the package is accurate, recognizable, readable at browse size,
   policy-safe, and ready for an explicitly selected current YouTube test mode. Uploading
   or starting that test remains separately authorized.

## Explicit non-goals

- a universal effects-per-minute target;
- an algorithmic retention guarantee;
- cloning Atozy or any other creator’s signature;
- autonomous profile changes based on analytics;
- hosted generation, API credentials, publication tests, uploads, or additional nodes;
- replacing Remotion or the existing production-quality workflow.
- copying Dr. Grande's exact template, identity, wordmark, puns, or title length;
- treating CTR alone as the native YouTube experiment winner;
- uploading variants or starting YouTube tests without explicit publication authorization.
