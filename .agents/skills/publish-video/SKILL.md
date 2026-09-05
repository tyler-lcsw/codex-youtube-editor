---
name: publish-video
description: Prepare an explicitly approved YouTube publication using the retained upload functionality.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Publication code is retained, but publication testing is waived for this migration. Do not run test uploads or publication tests. For a later actual user-authorized publication, review the exact artifact, channel, metadata, privacy and scheduling before invoking tools/yt_upload.py. Preserve the returned video ID/receipt; never treat a packaging request as upload approval.
