---
name: avatar
description: Handle presenter avatar or lipsync requests with explicit identity inputs and resource qualification.
---

Read `AGENTS.md`, `docs/providers.md` and `docs/setup-macos.md` first.

Read docs/implementation-status.md. Local avatar inference is deferred under the single-M4 envelope. Preserve the request and required image/audio references for a later provider; do not impersonate the upstream author or claim Remotion animation is an equivalent avatar. Hosted `tools/gen_avatar.mjs` is retained behind explicit `--allow-cloud` approval.
