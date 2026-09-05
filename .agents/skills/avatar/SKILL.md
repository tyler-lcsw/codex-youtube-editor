---
name: avatar
description: Handle presenter avatar or lipsync requests with explicit identity inputs and resource qualification.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Read docs/implementation-status.md. Local avatar inference is deferred under the single-M4 envelope. Preserve the request and required image/audio references for a later provider; do not impersonate the upstream author or claim Remotion animation is an equivalent avatar. Hosted `tools/gen_avatar.mjs` is retained behind explicit `--allow-cloud` approval.
