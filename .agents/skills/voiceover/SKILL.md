---
name: voiceover
description: Generate local narration or per-beat voiceover using an explicit voice reference and scripted pauses.
---

Production quality contract: read `docs/production-rules.md` before production,
at each editing checkpoint, and at final QA. Follow `docs/production-quality-workflow.md`:
route media-producing/editing commands through `tools.production_quality run`, inspect outputs,
and record individual rule evidence. Re-read changed rules; do not use stale approvals.
Run QA and tracker commands directly; they assess state rather than edit media.
Do not declare production complete without all phase gates and a current final QA receipt.


Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Use `.venv/bin/python -m tools.media tts --text-file P/beat.txt --ref-audio P/voice.wav --ref-text P/voice.txt --out P/vo.wav`. Keep beats short, preserve explicit pauses, and record the returned sample manifest. No generic voice or upstream author voice default. If no reference is provided, ask for the intended voice input before identity-dependent generation. The synthetic setup fixture does not qualify personal resemblance.
