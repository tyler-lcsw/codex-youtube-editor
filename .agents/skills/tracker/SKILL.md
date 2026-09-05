---
name: tracker
description: Maintain the local project tracker using stable IDs, dry-run previews and explicit apply operations.
---

Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use `.venv/bin/python tools/tracker.py P` for a preview, `--apply` to update the SQLite index, and `--list` to inspect it. Preserve project tracker.json/notion.json metadata and scripts. --props-only must not erase the stored script. Notion remains an optional compatibility integration; no account is required for local tracking.
