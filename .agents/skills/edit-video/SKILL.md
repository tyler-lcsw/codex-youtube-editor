---
name: edit-video
description: Coordinate a Codex-native local video edit, from source footage through reviewed cuts, Remotion overlays, sound, packaging and export.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use $clean-cut, $clean-audio, $make-tsx or $fake-screencast, $suggest-sfx and $packaging in dependency order. Read project state first. Run deterministic tools, inspect rendered frames and listen to flagged joins. Use render-derived transcript timing and preserve originals. Ask for creative choices only when needed; never upload as part of this coordinator.

For render-side QA use `.venv/bin/python -m tools.verify_render PROJECT --style natural` (or the selected style). It extracts the exact manifest master and binds independent ASR to its hash; an older transcript cannot establish current render timing.
