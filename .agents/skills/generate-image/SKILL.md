---
name: generate-image
description: Generate or edit a local image with the qualified M4 FLUX.2 Klein profile, or prepare an approved native Codex image handoff.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use `.venv/bin/python -m tools.media image --prompt-file P/prompt.txt --out P/image.png [--ref P/reference-copy.png]`. Observe the measured size/reference limits in docs/setup-macos.md. For bounded native Codex images use $thumbnail and scoped approval; never substitute a paid API.
