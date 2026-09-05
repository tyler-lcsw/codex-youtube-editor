---
name: generate-video
description: Handle generated B-roll and video requests while preserving future local worker support.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

First decide whether the shot should be a Remotion composition. Local diffusion-video qualification is deferred in this first M4 release. Report that capability status clearly; do not substitute a still image or silently invoke fal. The preserved `tools/gen_video.py` requires deliberate hosted selection and `--allow-cloud` after approval.
