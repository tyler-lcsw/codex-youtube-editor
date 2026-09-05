---
name: edit-video
description: Coordinate a Codex-native local video edit, from source footage through reviewed cuts, Remotion overlays, sound, packaging and export.
---

Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use $clean-cut, $clean-audio, $make-tsx or $fake-screencast, $suggest-sfx and $packaging in dependency order. Read project state first. Run deterministic tools, inspect rendered frames and listen to flagged joins. Use render-derived transcript timing and preserve originals. Ask for creative choices only when needed; never upload as part of this coordinator.

For render-side QA use `.venv/bin/python -m tools.verify_render PROJECT --style natural` (or the selected style). It extracts the exact manifest master and binds independent ASR to its hash; an older transcript cannot establish current render timing.
