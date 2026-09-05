---
name: music
description: Select, mix and track music assets; distinguish catalog mixing from novel music generation.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Inspect the existing music catalog, its provenance and the per-video mix plan. Use tools/mix_music.py with the retained CLI. Do not present procedural tones or existing clips as novel generated music. Generative music qualification is deferred unless a measured provider is marked ready. Legacy tools/gen_music.py requires explicit hosted approval and --allow-cloud.
