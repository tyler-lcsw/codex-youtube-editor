---
name: generate-video
description: Handle generated B-roll and video requests while preserving future local worker support.
---

Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

First decide whether the shot should be a Remotion composition. Local diffusion-video qualification is deferred in this first M4 release. Report that capability status clearly; do not substitute a still image or silently invoke fal. The preserved `tools/gen_video.py` requires deliberate hosted selection and `--allow-cloud` after approval.
