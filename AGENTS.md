# Codex YouTube Editor

Codex authors editorial decisions and Remotion TSX; deterministic local tools render,
validate and record artifacts. Read `docs/implementation-status.md` first while the
migration is in progress, then the selected `.agents/skills/<name>/SKILL.md`.

## Mandatory production quality contract

`docs/production-rules.md` is the authoritative editable policy for every production.
Read all rules before production, at each editing checkpoint, and again for final QA.
Follow `docs/production-quality-workflow.md`; generate current checklists with
`tools.production_quality`, record individual evidence and dispositions, and route
media-producing/editing actions through its `run` command. Run QA and tracker commands
directly so bookkeeping does not invalidate the media review. Apply this to every editing/generation
skill and raw FFmpeg/Remotion command. Inspect each action's output before unrelated
work; fix defects and reassess after corrections. Never auto-fill passing reviews.

The responsible AI owns these checks. Do not ask the user to complete routine checklists.
If actual listening/playback or another required review is unavailable, leave it pending
and request the specific intervention. Never equate a successful render with acceptance.
Register actual deliverables, complete all three phase gates, and finalize before marking
production complete/ready. Check `require_complete(project)` whenever relying on a prior
completion: changed policy, evidence, edits or deliverables can invalidate it. No historical
production is grandfathered in. QA completion never authorizes publication.

## Runtime and boundaries

- This checkout is on M4 (`m4-mini.local`, 24 GiB unified memory). Its internal startup
  volume happens to be named `mbp`; it is not a network share. Do not rename the volume.
  MBP has no control role. Do not establish MBP-to-M4 access or dependencies.
- Run from this repository root with `.venv/bin/python tools/<tool>.py` or
  `.venv/bin/python -m tools.<module>`. Use the locked core dependencies.
- Recommend `gpt-6-astra`; fully support `gpt-5.6-sol`. Both must pass acceptance.
- Retain Remotion and upstream TSX kits. Use installed Remotion plugin skills where
  available, subject to the project's timing, asset and review contracts.
- Use one heavy inference job at a time. Additional workers are optional, explicitly
  configured from M4. Never silently replace an unsupported feature with a lesser one.

## Media and approvals

Local media inference is the default. Read `docs/providers.md` before generation.
No hosted fallback, model download or API credential loading may happen implicitly.
For bounded images/thumbnails, propose native Codex GPT Image 2 with scoped user approval;
prefer local providers for integrated, controlled or unattended generation workflows.
Record the reported native model or unknown; no separate paid API fallback without approval.
Reuse approval within its purpose, selected reference hashes and bounded iteration scope.
New references/provider/purpose or exhausted scope require a new decision.

Project state and originals are durable. Preserve existing successful outputs on failure.
Personal footage, reference voices/faces, tokens and generated per-project assets are ignored
by Git. Do not reuse the upstream author's private voice ID or likeness as defaults.
Never publish or upload without explicit approval of the actual artifact/channel.
Tyler explicitly waived publication testing; preserve the functionality and do not run
publication tests or test uploads during this migration.

## Editing and review

Original transcript words use integer milliseconds; unknown timing is flagged, not guessed.
Cut time mapping follows actual rendered segments after padding and pause compression.
Independent ASR over the render checks retained/missing speech; duration equality is not
proof of lip sync. Render and inspect representative frames and listen to audio before
claiming creative acceptance. Keep brand.md, remotion/src/brand.ts and fonts.ts consistent.
Use catalog assets first; per-video media belongs in media/projects/<project>.

## Implementation

Execute the approved `plan/Codex YouTube Editor — Implementation Plan.md` with Superpowers,
focused TDD and coherent commits. Work on a dedicated branch. Update status and docs from
actual evidence; a passing mocked adapter is not a completed local capability or release.
No BMAD initialization. Keep upstream changes reviewable, preserve legacy formats and
unknown fields, and do not enable new hosted dependencies during upstream merges.

## Revised first release

Follow `plan/M4 First Release — Runtime and Memory Decision.md` over conflicting original
full-parity gates. The example video is not a completion benchmark. Qualify only comfortably
fitting single-M4 models; target 12 GiB active inference, reserve 8 GiB for OS/apps and
4 GiB contingency, and measure actual pressure/context. Future PAIR nodes do not pool RAM.
Preserve larger-provider interfaces but defer their qualification; do not download large
models to satisfy the superseded visual/quality bar. Test PAIR locally; no remote setup.

## Autonomous continuation

Tyler authorized continuing development and automatically merging PRs after review and
appropriate validation, without pausing between features, PR steps or tasks. Continue
within the approved project scope; stop only when specific feedback/intervention is
required. This does not authorize hosted generation outside its scoped approval,
publication, additional-node setup or reopening the deferred full-parity benchmark.
