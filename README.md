# Codex YouTube Editor

A Codex-native fork of [Claude YouTube Editor](https://github.com/hassancs91/claude-youtube-editor), retaining its Remotion compositions, editing tools and publication functionality. GPT-6 Astra is recommended; GPT-5.6 Sol uses the same skills and commands.

This first release targets one Apple Silicon Mac with 24 GiB of unified memory. It uses local transcription, alignment, cleanup, reference narration and bounded image generation/editing. Codex still runs online; local inference workers run with network access denied after explicit model setup.

## Start here

1. Follow [Mac setup](docs/setup-macos.md) for locked environments and pinned models.
2. Read [implementation status](docs/implementation-status.md) and [provider policy](docs/providers.md) for verified capabilities and limits.
3. Ask Codex to use `edit-video` for a project. It routes to `clean-cut`, `clean-audio`, `make-tsx`, `voiceover`, `thumbnail` and related skills in `.agents/skills`.
4. Review proposed cuts, rendered frames and audio before accepting a creative result. Publication requires approval of the actual artifact and channel.

```sh
.venv/bin/python tools/transcribe.py PROJECT
.venv/bin/python tools/render_cuts.py PROJECT --style natural --mode preview
.venv/bin/python tools/clean_voice.py PROJECT/output/preview-natural.mp4
npm --prefix remotion run studio
```

Create/review `PROJECT/work/analysis/cuts.json` before rendering; these are workflow commands, not a one-command unattended editor. The clean-cut skill describes ingest, cut planning and review. Keep project assets out of Git.

## Local resources

Qwen3 ASR/ForcedAligner 0.6B, DeepFilterNet3, Qwen3 TTS 0.6B Base and FLUX.2 Klein 4B are installed and exercised locally. Images are bounded to 768×512 equivalent area and one reference. Optional PAIR-backed Qwen3.5 4B/9B MLX models assist short text/vision tasks. PAIR does not pool node memory. Run one heavy inference job at a time and unload it before rendering.

Bounded native Codex images are available with scoped user approval. There is no automatic hosted fallback. Large avatar/video models, generative music, multi-reference/high-resolution image qualification and multi-node scaling remain deferred. Existing interfaces and upstream tools are retained; deferred does not mean quality-equivalent replacements exist today.

Versioned crossfades, punch-ins and color grading are available through the [timeline contracts](docs/timeline-compatibility.md). Repeatable Astra/Sol checks are documented in [acceptance](docs/acceptance.md).

See the [revised first-release decision](plan/M4%20First%20Release%20%E2%80%94%20Runtime%20and%20Memory%20Decision.md), [measured results](docs/benchmarks/first-release.md), and [upstream maintenance](docs/upstream-maintenance.md). The original example video is background research, not the release benchmark. Publication testing was explicitly waived; no test upload is part of setup.

## Verification

```sh
.venv/bin/python -m pytest -q --deselect tests/test_portability.py::test_upload_relative_paths_use_this_repository
.venv/bin/python tools/skill_audit.py
npm --prefix remotion run typecheck
```

The [original upstream README](docs/upstream/README-original.md) is preserved for provenance, not as the active setup guide. Retain upstream licensing; Remotion and optional LM Studio have their own terms. Model licenses and revisions are recorded in `config/models.lock.json`; bundled font licenses accompany their files.

## Authoritative production QA

Every production follows the editable [31 production rules](docs/production-rules.md)
through [before, during, and final QA](docs/production-quality-workflow.md). The coordinator
reads policy at runtime, journals editing actions, and invalidates stale reviews when rules,
evidence, actions, or deliverables change. Completion tracking requires a current QA receipt.
Technical checks do not replace complete playback and listening review.

## Mac production app

[Codex Media Studio](docs/mac-studio.md) consolidates footage/context intake, editable workflow
stages, native playback, frame and time-range annotations, revision feedback, resource
preferences and subscription-authenticated Codex. Build the development app with
`.venv/bin/python tools/build_studio_app.py`. Read the [approved plan](plan/Mac%20Production%20Studio%20%E2%80%94%20Implementation%20Plan.html) for scope and acceptance.

For end-user instructions, open **How to Use** in the app or read the [step-by-step user guide](docs/how-to-use.html). **Help for this tab** opens contextual instructions while preserving your current draft.
