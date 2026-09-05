# M4 local setup

This first-release profile targets one Apple Silicon Mac with 24 GiB. PAIR nodes do not pool memory. Use the revised plan for scope; larger avatar/video and multi-reference qualification is deferred. Never run two heavy media models together.

## Environments

Use Python 3.11, Node 22–24 LTS, FFmpeg/ffprobe and uv. On this M4, FFmpeg 9.0.1 and Python 3.11.15 are installed through Homebrew. Node 24.19.0 is available in the Codex bundled runtime; system Node 25 is outside the tested range.

```sh
uv venv --python python3.11 .venv
uv pip sync --python .venv/bin/python requirements-core.lock
uv venv --python python3.11 .envs/audio
uv pip sync --python .envs/audio/bin/python requirements-audio.lock
uv venv --python python3.11 .envs/denoise
uv pip sync --python .envs/denoise/bin/python requirements-denoise.lock
uv venv --python python3.11 .envs/image
uv pip sync --python .envs/image/bin/python requirements-image.lock
npm --prefix remotion ci
npm --prefix remotion run gen
```

Do not merge these inference environments. DeepFilterNet currently needs Torch/Torchaudio 2.5.1; the newer Torchaudio removed an API it imports. Locked packages capture the tested Mac environment, not cross-platform qualification. Downloading dependencies is an explicit setup step.

## Pinned media models

`config/models.lock.json` records repositories, revisions, local paths and file hashes. Model weights are ignored by Git. These commands download one selected model; inference itself cannot fetch missing assets.

```sh
.envs/image/bin/python -m tools.setup_models asr
.envs/image/bin/python -m tools.setup_models aligner
.envs/image/bin/python -m tools.setup_models tts
.envs/image/bin/python -m tools.setup_models image_klein
.venv/bin/python -m tools.setup_models denoise
.envs/image/bin/python -m tools.setup_models llm_4b
.envs/image/bin/python -m tools.setup_models llm_9b
```

DeepFilterNet3 setup uses the exact upstream archive under `denoise` in the lock. It verifies the archive and every selected file before installing from a temporary directory, rejects unsafe archive paths, and leaves an existing valid installation untouched. If an existing installation is damaged or modified, setup fails rather than deleting it; move it aside explicitly before reinstalling. Add `--verify-only` to check any installed model without network access. DeepFilterNet setup/verification uses the core Python environment; Hugging Face downloads use the image environment.

## Media commands

Run from the repository root. The runner locks local inference, requires LM Studio models to be unloaded, denies network access in the worker process and terminates its process group on timeout/cancellation. It preserves inference errors rather than switching providers.

```sh
.venv/bin/python -m tools.media asr --audio P/clip.wav --out P/transcript.json --language English
.venv/bin/python tools/clean_voice.py P/master.mp4 --method deepfilter -o P/master-clean.mp4
.venv/bin/python -m tools.media tts --text-file P/beat.txt --ref-audio P/voice.wav --ref-text P/voice.txt --out P/voiceover.wav
.venv/bin/python -m tools.media image --prompt-file P/prompt.txt --out P/image.png
.venv/bin/python -m tools.media image --prompt-file P/edit.txt --ref P/reference-copy.png --out P/edited.png
```

Replace `P` with an actual project path. TTS requires a clear 1–30 second reference and its correct transcript. Short beats support explicit `<break time="300ms"/>` pauses. Their sample-count manifest makes pauses reviewable. No personal voice reference is bundled.

Image generation/editing is qualified at 768×512 or equal-area dimensions divisible by 16, with at most one same-size reference. Prepare smaller reference copies explicitly and preserve originals. Larger requests fail with the profile limit. Final thumbnail typography and canvas compositing can use existing Pillow/FFmpeg tools; record upscaling truthfully. More resolution or references requires another measured trial.

## PAIR and local text/vision

PAIR is already managing this M4's engines. Client ports: LM Studio proxy 1234, Ollama proxy 11434. Direct engine ports: LM Studio 1235, Ollama 11435, both loopback. Do not start replacement servers on the proxy ports or reconfigure other nodes.

Downloaded models are in `~/.lmstudio/models/mlx-community/Qwen3.5-{4B,9B}-4bit`. Exact upstream revisions and sizes are in the runtime decision document. Use the project loader to serialize loads with media jobs and verify the actual runtime settings.

```sh
.venv/bin/python -m tools.load_local_llm qwen3.5-4b
.venv/bin/python -m tools.providers.local_llm --model qwen3.5-4b --prompt P/prompt.txt --schema P/schema.json --out P/result.json
lms unload qwen3.5-4b
```

The helper uses PAIR, requires the single chosen model already loaded with parallel=1, accepts at most 2048 UTF-8 input bytes and 1024 output tokens, and validates answer JSON. Model load requests for 4096 context were ignored by the installed MLX engine: actual reported windows were 123648 (4B) and 92672 (9B). The helper's conservative request budget is not a hard engine-level token cap. No long-context or multi-user admission claim is made. Use `lms ps --json` and saved load receipts to inspect real settings.

The server also ignored tested thinking controls. Some schema-constrained responses placed JSON in reasoning with an empty answer. The helper rejects those; ordinary JSON answers validated successfully. Do not harvest reasoning as the final artifact. Vision/tool calling were exercised separately through PAIR; the bounded production helper intentionally exposes text JSON only.

## Verification

```sh
.venv/bin/python -m pytest -q --deselect tests/test_portability.py::test_upload_relative_paths_use_this_repository
.venv/bin/python tools/skill_audit.py
npm --prefix remotion run typecheck
```

Publication testing is explicitly waived. No upload should be performed during setup. Personal likeness, difficult-noise equivalence, long-context inference and multi-node scaling are separate future reviews.

Use the app-bundled Codex CLI 0.153.4 or newer for Astra/Sol; Homebrew CLI 0.146.0 was rejected by the service for Astra. On this installation the bundled binary is `/Applications/ChatGPT.app/Contents/Resources/codex`.

Render QA: `.venv/bin/python -m tools.verify_render PROJECT --style natural` extracts the exact manifest master and binds fresh ASR to its hash. Unresolved word timing fails explicitly and requires review/re-alignment; unknown confidence remains unknown.

Timeline export validation and failure preservation are described in [timeline compatibility](timeline-compatibility.md). Existing output remains intact when a bake fails.
