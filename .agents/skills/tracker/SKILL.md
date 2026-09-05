---
name: tracker
description: Maintain the local project tracker using stable IDs, dry-run previews and explicit apply operations.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use `.venv/bin/python tools/tracker.py P` for a preview, `--apply` to update the SQLite index, and `--list` to inspect it. Preserve project tracker.json/notion.json metadata and scripts. --props-only must not erase the stored script. Notion remains an optional compatibility integration; no account is required for local tracking.
