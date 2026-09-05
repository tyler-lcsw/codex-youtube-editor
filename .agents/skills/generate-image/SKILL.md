---
name: generate-image
description: Generate or edit a local image with the qualified M4 FLUX.2 Klein profile, or prepare an approved native Codex image handoff.
---

Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use `.venv/bin/python -m tools.media image --prompt-file P/prompt.txt --out P/image.png [--ref P/reference-copy.png]`. Observe the measured size/reference limits in docs/setup-macos.md. For bounded native Codex images use $thumbnail and scoped approval; never substitute a paid API.
