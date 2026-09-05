# Codex YouTube Editor Implementation Plan

## First-release scope revision — September 5, 2026

Tyler superseded full visual parity as the first-release completion gate. The supplied video is background research only. The controlling criteria and runtime shortlist are in [M4 First Release — Runtime and Memory Decision.md](M4%20First%20Release%20%E2%80%94%20Runtime%20and%20Memory%20Decision.md).

Qualify models only on this single 24 GiB M4, with room for macOS, context and normal apps. PAIR routes independent requests; future 16 GiB Macs do not enlarge one model's memory allocation. Preserve resource-heavy feature interfaces but defer their local quality qualification when they exceed this release's envelope. Publication remains present and its testing is waived. The task inventory below remains the longer-term roadmap; conflicting full-parity gates do not block the first release.


> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Use superpowers:subagent-driven-development only if the user selects delegation. Steps use checkbox syntax for tracking. This document authorizes no implementation by itself.

**Goal:** Preserve the fork's complete editing and extended generation workflows under Codex, with local media providers, an approved hybrid image route, Mac-first execution and an optional GPU worker.

**Architecture:** Retain the existing Python/Node/Remotion engine and file contracts. Add small provider adapters, normalized media results, capability discovery and resumable jobs; move operational skills to Codex. Offer native Codex GPT Image 2 for bounded approved image work and local generation for integrated pipelines, using a shared asset contract. Make quality, timing and model compatibility explicit release gates.

**Tech Stack:** Codex CLI/App; Python 3.11 core with separately locked model environments; Node LTS selected during preflight; React/Remotion 4 initially; FFmpeg; MLX Audio; local inference adapters; JSON Schema; pytest; TypeScript checking; browser interaction tests; SQLite for the local tracker index.

**Spec:** [Codex YouTube Editor — Design and Research.md](Codex%20YouTube%20Editor%20%E2%80%94%20Design%20and%20Research.md). Read the entire spec before implementation. All new APIs, flags and files below are **proposed**, not existing commands.

## Global constraints

- Project base and execution host: local M4 `m4-mini.local`, with 24 GB unified memory, at `/Users/tyler-lcsw/projects/yt-codex`. This Codex instance already runs there. An additional GPU worker remains optional and unselected. MBP has no control role; do not create MBP-to-M4 access, credentials, tunnels or dependencies.
- `gpt-6-astra` is recommended; `gpt-5.6-sol` must pass the same workflow acceptance suite.
- Preserve all nine existing skills, executable auxiliary features, review gates and reusable components.
- No required Claude runtime, Anthropic service, AssemblyAI, ElevenLabs, Gemini, fal or Notion account in the local media profile.
- Codex and YouTube are intentional online components; do not advertise full offline operation.
- Retain existing artifact formats and preserve unknown fields; new contracts use `schema_version: 1`.
- No model-quality parity claim before the relevant benchmark and human review pass.
- Hybrid image use requires scoped user approval; selecting hybrid mode alone is not approval for a call. Prefer the native Codex tool and never silently substitute a separately billed API. Preserve a complete strict local profile.
- No silent fallback to cloud, a generic voice, stock content, lower resolution, or a still image.
- Retain Remotion as explicitly required by Tyler; renderer replacement is out of scope. Keep Remotion 4 initially and document its custom license. Verify and use the available Codex Remotion plugin/skills where helpful.
- Store model weights, personal references, OAuth tokens and generated working media outside tracked source by default.
- Do not use the upstream author's voice ID, private repository paths, or likeness as the fork's defaults.
- Commit coherent implementation units after focused checks and documentation alignment; push/deploy only within the user's subsequent implementation authorization.

## Task dependencies and release slices

| Slice | Tasks | Independently useful output |
|---|---|---|
| Baseline | 1 | Feature inventory, reproducible fixtures and known failures |
| Mac + Codex foundation | 2–4 | All skills discoverable, portable encoders, local provider/job contracts |
| Local editing | 5–6 | Local transcript, reliable cut master, editor and timing QA |
| Local audio | 7–8 | Cleanup, narration, novel effects, music and stems |
| Local visual generation | 9–10 | Thumbnails, generated B-roll, avatars and vertical pilot |
| Workflow completion | 11–12 | Local tracking, publish verification, upstream extension compatibility |
| Full acceptance | 13 | Complete dual-model demonstration with network and quality evidence |

Planning allowance, not a delivery quote: roughly 4–8 weeks of focused implementation and review for a small effort, with provider quality trials on the critical path. Core editing should become reviewable earlier. If hard-noise or likeness trials fail, re-evaluate that provider before scheduling the remaining adapter work; do not spend weeks polishing an unsuitable model. Hardware inventory and first trials should refine this estimate.

## Proposed file boundaries

| Files | Responsibility |
|---|---|
| `AGENTS.md`, `.agents/skills/`, `docs/codex.md` | Codex routing, skills, model usage and operator instructions |
| `tools/runtime/paths.py`, `encoders.py`, `doctor.py` | Consistent roots, capabilities and portable media runtime |
| `tools/providers/contracts.py`, `registry.py`, `policy.py` | Task capabilities, request/result shape, local/cloud eligibility |
| `tools/jobs.py`, `tools/run_state.py` | Cache, job state, bounded execution and hash-bound approvals |
| `tools/providers/asr_*.py`, `tools/transcripts.py`, `tools/prosody.py` | Local transcription, alignment and normalized acoustic annotations |
| `tools/time_map.py`, `tools/media_qa.py` | Actual-render time mapping and machine verification |
| `tools/providers/denoise_*.py`, `tts_*.py`, `sfx_*.py`, `music_*.py`, `image_*.py`, `video_*.py`, `avatar_*.py` | One task/backend adapter per module |
| `tools/worker/client.py`, `server.py`, `schemas.py` | Optional authenticated worker transport using the same job contracts |
| `tools/tracker.py`, `tools/tracker_store.py`, `tools/editor/tracker.html` | Local content tracker and rebuildable SQLite index |
| `tools/publish_gate.py`, `tools/yt_upload.py` | Hash-bound review and verified upload plan |
| `schemas/`, `config/`, `tests/`, `docs/benchmarks/`, `docs/upstream/` | Contracts, profiles, evidence, operator docs and upstream adoption |

Do not move the whole existing engine into a new package. Add `tools/__init__.py` and scoped package files where needed; keep legacy script entry points working.

## Task 1 — Freeze the feature baseline and meaningful fixtures

**Files:** Create `docs/feature-parity.md`, `docs/upstream/baseline.json`, `docs/benchmarks/protocol.md`, `tests/fixtures/manifest.json`, `tests/test_baseline.py`, `tools/fixture_media.py`, `tools/__init__.py`; inspect all existing skills, `tools/`, `remotion/`, `docs/` and catalogs.

**Interfaces:** `tools.fixture_media.make_clock_clip(out: Path, fps: str, seconds: int) -> Path` creates a synthetic clip containing frame numbers and timed audio pulses. `manifest.json` lists file hash, source/license, feature case, FPS and expected markers. Baseline JSON records upstream URL/SHA and the exact inventory of skill names and reusable compositions.

- [ ] Checkout the fork in the intended project directory, preserving any existing plan files; read applicable instructions and Git state. Pin the inspected commit or document any newer changes before proceeding.
- [ ] Record code-backed features separately from pilot/roadmap claims. Identify missing example assets as baseline omissions rather than pretending every checked-in TSX helper is a standalone composition.
- [ ] Write the fixture test:

```python
import json
import subprocess
from fractions import Fraction
from tools.fixture_media import make_clock_clip
def test_fractional_clock_fixture(tmp_path):
    path = make_clock_clip(tmp_path / "clock.mp4", "30000/1001", 12)
    assert path.is_file()
    raw = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=avg_frame_rate", "-of", "json", str(path)])
    assert Fraction(json.loads(raw)["streams"][0]["avg_frame_rate"]) == Fraction("30000/1001")
```

- [ ] Run `python -m pytest tests/test_baseline.py -q`; expect failure before the fixture builder exists. Implement the builder with FFmpeg `testsrc2`, frame-number `drawtext`, PCM reference audio pulses and an H.264/AAC delivery copy. Record sample/frame positions in the manifest; inspect the generated clip. The probe checks the encoded rate; later tasks perform the actual A/V landmark verification.
- [ ] Build a timestamped visual capability checklist from the supplied YouTube video, which Tyler identifies as a full example made with the existing workflow, including all visible assets. Map observed techniques to repository components where supported and mark unknown mappings. Recreate representative editing/animation techniques with cleared or original content; vary their balance by project rather than imposing the reference video's style density. No additional style example is required to start.
- [ ] Add consented human recordings for fillers, false starts, accents, proper nouns and difficult noise. Use existing cleared assets or owner-provided material; do not make new paid calls for baselines without authorization. Manually annotate at least 200 word boundaries and all disputed cuts across a 10–15 minute corpus.
- [ ] Record current command failures, path assumptions and render behavior. Commit baseline, fixtures and documentation together; generated large footage remains ignored with reproducible recipes or local manifest paths.

**Pass:** Every design inventory row has a source location, an acceptance case and status; there is no unsupported claim of current parity.

## Task 2 — Make the complete workflow discoverable in Codex

**Files:** Create `AGENTS.md`, `.agents/skills/` with the nine existing skills and references, plus `edit-video`, `voiceover`, `generate-video`, `avatar`, `music`, `shorts`, `tracker`, `publish-video`; create `docs/codex.md`, `tests/test_skill_contracts.py`, `tools/skill_audit.py`; update `README.md` and operational cross-references. Preserve `CLAUDE.md` only as a compatibility/history pointer, not the default instruction source.

**Interfaces:** `tools.skill_audit.audit(root: Path) -> list[str]` returns missing metadata, broken local references, operational `.claude/skills` dependencies and absent required skills. Natural-language requests and explicit `$skill-name` both route to the appropriate skill.

- [ ] Write the failing audit test:

```python
from pathlib import Path
from tools.skill_audit import audit
def test_codex_skills_are_complete():
    assert audit(Path(__file__).resolve().parents[1]) == []
```

- [ ] Run `python -m pytest tests/test_skill_contracts.py -q`; confirm the expected missing-Codex-files failure.
- [ ] Port instructions by meaning: inputs, outputs, local provider selection, review states and exact commands. Replace execution-specific Claude language and Windows paths; keep real product names and historical attribution. Add short descriptions and optional `agents/openai.yaml` display metadata. Do not create duplicate skill copies in both project and user directories.
- [ ] Discover the actual Codex Remotion plugin and relevant skills at setup; read their instructions and use them for applicable TSX authoring/rendering work. Keep fork-specific timing, provider and review contracts authoritative. Document unavailable plugin capabilities without making unsupported claims or copying global skills into the project.
- [ ] Define the orchestrator as a file-driven sequence: inspect project state → choose next incomplete stage → invoke one skill → validate outputs → record review state. Extended skills expose existing functionality without adding a separate autonomous editorial API.
- [ ] Run the audit and inspect Codex skill discovery in a fresh task. Execute a read-only request with each model to identify the brand, cut, thumbnail-only and avatar workflows. Save CLI version, model IDs and selected skill names in benchmark receipts.
- [ ] Update the quickstart to `codex -m gpt-6-astra` and the alternative `codex -m gpt-5.6-sol`. Record that availability depends on the account; no API subscription equivalence claims. Commit.

**Pass:** No operation requires starting Claude; all original and extended operations have a Codex entry path. Sol receives the full workflow rather than a limited mode.

## Task 3 — Mac-safe paths, encoders and dependency profiles

**Files:** Create `tools/runtime/{__init__,paths,encoders,doctor}.py`, `config/runtime.example.toml`, `tests/test_runtime.py`, `docs/setup-macos.md`; update `tools/make_proxy.py`, `render_cuts.py`, `bake.py`, `editor/server.py`, `gen_vo.mjs`, `gen_avatar.mjs`, `yt_upload.py`, `requirements.txt` and `remotion/package.json` as necessary; introduce locked core dependencies.

**Interfaces:** `choose_encoder(available: set[str], prefer: str, bit_depth: int) -> str`; `resolve_project_path(root: Path, value: str) -> Path`; `doctor() -> dict` reports binary versions, actual encode-probe outcomes and provider readiness. Node tools use `fileURLToPath(import.meta.url)`.

- [ ] Write these regression cases, plus a repository path containing spaces and Unicode:

```python
from tools.runtime.encoders import choose_encoder
def test_mac_without_nvidia():
    assert choose_encoder({"h264_videotoolbox", "libx264"}, "auto", 8) == "h264_videotoolbox"
def test_cpu_linux_is_valid():
    assert choose_encoder({"libx264"}, "auto", 8) == "libx264"
def test_ten_bit_cpu_preserved():
    assert choose_encoder({"libx265"}, "auto", 10) == "libx265"
```

- [ ] Run `python -m pytest tests/test_runtime.py -q` and confirm failure. Then implement capability-based selection, codec-specific arguments and a tiny real encode probe. A detected but failing hardware encoder is removed from the usable set; CPU fallback is reported. If no selected-depth encoder works, fail with the tested choices.
- [ ] Replace forced CUDA decode, fix upload root resolution explicitly, normalize JS URL paths, and ensure output directories exist. Source dimensions/rational FPS govern delivery; review copies can be reduced only by an explicit profile. Test final HEVC playback/tag handling on Mac.
- [ ] Inspect local runtime readiness and free disk on the verified M4 host; keep source, state and artifacts in the local project. No separate controller-to-M4 transport is required. Measure a representative render on its 24 GB shared memory budget with bounded concurrency. Before full adapters in Tasks 7–10, run isolated feasibility trials for cleanup, voice, reference-image generation/editing and a short avatar/video case. Record model size, peak memory, swap, quality and elapsed time; stop unsuitable trials and identify a qualified worker requirement instead of silently dropping features. Download only selected trial models after reporting storage requirements.
- [ ] Review upstream PR #1 for reusable fixes; resolve against the current baseline and add CPU/non-NVIDIA coverage it lacks. Pin the Remotion package family consistently and select a supported Node runtime that passes registry, type and render checks.
- [ ] Run proxy, cut editor, natural/tight previews and final encode with the clock fixture. Document native Mac setup, environment activation, optional model environments and recovery. Commit.

**Pass:** Core editing does not require NVIDIA, Windows paths or the original monorepo layout. No unannounced bit-depth/FPS loss.

## Task 4 — Provider contracts, network policy and resumable jobs

**Files:** Create `tools/providers/{__init__,contracts,registry,policy}.py`, `tools/jobs.py`, `tools/run_state.py`, `schemas/{media-request,media-result,run-state}.schema.json`, `config/providers.example.toml`, `config/hybrid.example.toml`, `config/models.lock.json`, `tests/test_jobs.py`, `tests/test_provider_policy.py`, `docs/providers.md`.

**Interfaces:** `MediaRequest(task: str, inputs: dict, options: dict)`; `MediaResult(artifacts: list[dict], metrics: dict, provenance: dict)`; `Provider.capabilities() -> dict`; `Provider.run(request: MediaRequest, output_dir: Path) -> MediaResult`; `ensure_allowed(provider_kind: str, local_only: bool) -> None`; `authorize_hybrid_image(request: dict, approval: dict | None) -> bool`; `job_key(request: dict, provider_revision: str) -> str`. Stable exception types are `UnsupportedCapability`, `ProviderUnavailable`, `CloudDisabled`, `JobCancelled` and `InvalidMediaResult`.

- [ ] Write the failing contract tests:

```python
import pytest
from tools.jobs import job_key
from tools.providers.policy import ensure_allowed, CloudDisabled
def test_local_profile_blocks_cloud():
    with pytest.raises(CloudDisabled):
        ensure_allowed(provider_kind="cloud", local_only=True)
def test_revision_invalidates_cache():
    r = {"task": "sfx", "inputs": {"prompt": "click"}, "options": {"seed": 42}}
    assert job_key(r, "rev-a") != job_key(r, "rev-b")
```

- [ ] Run the focused tests. Implement canonical JSON hashing including input file hashes; atomic result writes; pending/awaiting_approval/awaiting_codex_image/running/succeeded/failed/cancelled states; timeout and bounded retry; return-code and output validation. Reuse a cache entry only after artifact hashes and media probes agree.
- [ ] Define an allowlisted provider registry. The local profile rejects cloud adapters before loading credentials. Missing local models return an explicit setup instruction; model downloads are a separate operation. Record every model dependency's URL, immutable revision, checksum and license text/hash.
- [ ] Add `codex_builtin` as a hosted, agent-mediated provider kind. Strict local policy rejects it before dispatch. Hybrid policy requires approval matching provider, purpose, reference hashes and bounded generation/edit scope; a profile flag alone is insufficient. Test absent approval, valid scope reuse, changed references, exceeded scope, cancellation and retry reconciliation. Record actual attempts without double-consuming scope on import retry.
- [ ] Store approval kind, artifact hash and timestamp in `run-state.json`. Changing an input invalidates only affected outputs/reviews. Never overwrite successful prior outputs on failure.
- [ ] Add process-level network denial to integration tests rather than relying only on mocked `requests`; it must cover Python, Node, subprocesses and model download hooks. Document that Codex, approved native image generation, web capture and publishing are outside the offline worker test. Native generation passes through a durable agent handoff; unattended workers cannot invoke it. Commit.

**Pass:** Missing credentials do not break local paths; failures cannot cause surprise billing, implicit uploads or false successful jobs.

## Task 5 — Local verbatim transcription, alignment and acoustic context

**Files:** Create `tools/providers/asr_mlx.py`, `asr_whisperx.py`, `tools/transcripts.py`, `tools/prosody.py`, `tests/test_transcripts.py`, `tests/integration/test_asr.py`, `docs/benchmarks/asr.md`; update `tools/transcribe.py`, `format_transcript.py`, `cutlib.py`, `analyze_cut.py`, `verify_cut.py`, and the Codex `clean-cut` skill.

**Interfaces:** `normalize_word(text: str, start_s: float | None, end_s: float | None, score: float | None) -> dict`; `transcribe_and_align(audio: Path, language: str | None, keyterms: list[str], out: Path) -> dict`; `extract_prosody(audio: Path, words: list[dict]) -> list[dict]`. Canonical output keeps integer-ms `words`; untimed words remain present with null times and an explicit review flag. Legacy timing consumers must be blocked until those words are aligned or explicitly resolved; never let null timestamps reach arithmetic in `cutlib.py`. ASR confidence and alignment confidence remain distinct.

- [ ] Write the normalization regression:

```python
from tools.transcripts import normalize_word
def test_seconds_are_converted_and_unknown_score_is_not_certainty():
    w = normalize_word("um", 1.25, 1.45, None)
    assert (w["text"], w["start"], w["end"]) == ("um", 1250, 1450)
    assert w["confidence"] is None
def test_untimed_words_are_not_dropped():
    w = normalize_word("p95", None, None, None)
    assert w["text"] == "p95" and w["needs_review"] is True
```

- [ ] Run the tests and implement adapters. Use Qwen3-ASR plus its aligner on MLX for Apple Silicon; retain WhisperX CPU/CUDA as an independent candidate. Chunk long audio with overlap, reconcile duplicate tokens, and obey the aligner's chunk-duration limits. Never reinterpret seconds as milliseconds or silently take a stale `transcripts-u35` directory over the active transcript selection.
- [ ] Preserve the old CLI arguments and add explicit `--provider`, `--language`, `--device`, `--model` and profile selection. Lazy-load cloud code only on explicit cloud selection. Emit source provider response and normalized JSON separately, including language and keyterm settings.
- [ ] Compute energy/pause/pitch annotations locally and link them to word/segment IDs. Give uncertain delivery cues a confidence label and review audio excerpt; do not claim emotion ground truth. Support separate correction files so a human can recover missing fillers and proper names without destroying the original response.
- [ ] Run `python -m pytest tests/test_transcripts.py tests/integration/test_asr.py -q`. Score the human corpus: WER, filler/false-start recall, median/p95 boundary error and runtime/memory. Require the selected default to pass the spec thresholds and zero accepted harmful cut decisions; where needed, add local correction/re-alignment before accepting a transcript. Document and commit.

**Pass:** The local transcript is a trustworthy editing input, not merely fluent text. Codex can inspect timing uncertainty and delivery evidence.

## Task 6 — Render-derived time mapping and independent final QA

**Files:** Create `tools/time_map.py`, `tools/media_qa.py`, `tests/test_time_map.py`, `tests/integration/test_render_timing.py`, `schemas/render-segments.schema.json`; update `tools/render_cuts.py`, `cutlib.py`, `verify_cut.py`, `bake.py`, and the cut/editor workflow.

**Interfaces:** `remap_word(word: dict, segments: list[dict]) -> list[dict]`; `check_media_sync(path: Path, landmarks: list[dict], max_drift_ms: int = 40) -> dict`. A render segment contains `clip_id`, `source_in_sample`, `source_out_sample`, `source_sample_rate`, `output_in_sample`, `output_sample_rate`, `output_in_frame`, `output_out_frame` and `fps_num`/`fps_den`. Word IDs include source clip and occurrence, so repeated source ranges can map to multiple outputs.

- [ ] Write this remapping case and add cases for reordering, repeated clips, cut-crossing words and fractional FPS:

```python
from tools.time_map import remap_word
def test_word_uses_actual_segment_offset():
    seg = {"clip_id":"a", "source_in_sample":480000, "source_out_sample":576000,
           "source_sample_rate":48000, "output_in_sample":144000,
           "output_sample_rate":48000, "output_in_frame":90,
           "output_out_frame":150, "fps_num":30, "fps_den":1}
    w = {"clip_id":"a", "id":"w1", "text":"hello", "start":10500, "end":10700}
    mapped = remap_word(w, [seg])
    assert (mapped[0]["start"], mapped[0]["end"]) == (3500, 3700)
```

- [ ] Run the tests; emit actual encoded segment timing after padding/pause compression, not just requested keeps. Use integer sample positions and rational frame arithmetic. Clip-crossing words are flagged for review rather than represented as intact words.
- [ ] Generate `edited-transcript.json` from that mapping and record the master hash. Retime every dependent cue from stable word IDs or invalidate it when the word disappears. Audio pickups and transition overlaps explicitly update or preserve timeline duration according to their declared policy.
- [ ] Keep a fresh local ASR pass over rendered speech for ghost/missing-word detection. Rewrite low-confidence handling for unknown provider scores; unresolved findings need review. Replace the expanding drift allowance with fixed landmarks and PTS/sample/frame checks. Do not treat equal stream durations alone as success.
- [ ] Inject known faults: 200 ms audio offset with equal stream durations, AAC join accumulation, 59.94/60 mismatch, clipped onset and stray false-start audio. Run `python -m pytest tests/test_time_map.py tests/integration/test_render_timing.py -q`; every injected fault must be detected. Verify editor saves still produce valid mappings. Commit.

**Pass:** Mapping and independent QA catch different failure classes and both remain present. One-frame cue accuracy and fixed A/V drift limits hold on long and fractional-FPS fixtures.

## Task 7 — Local cleanup and owner-configured voiceover

**Files:** Create `tools/providers/denoise_deepfilter.py`, `tts_qwen.py`, `tts_chatterbox.py`, `tools/voice_script.py`, `config/voice.example.json`, `tests/test_voice_script.py`, `tests/integration/test_voice.py`, `docs/benchmarks/voice.md`; update `tools/clean_voice.py`, `gen_vo.mjs` and the audio/voiceover skills.

**Interfaces:** `parse_voice_script(text: str) -> list[dict]` accepts text and a supported subset of `<break time="..."/>`; `VoiceRequest` uses the common `MediaRequest` with voice-reference paths, language, pace, expression and context text. `tools/gen_vo.mjs` remains a compatibility wrapper that invokes the chosen adapter through the job runner.

- [ ] Write pause and unsupported-control tests:

```python
import pytest
from tools.voice_script import parse_voice_script
def test_explicit_pause_is_preserved():
    assert parse_voice_script('Hello.<break time="300ms"/>Again.') == [
        {"text":"Hello."}, {"silence_ms":300}, {"text":"Again."}]
def test_unknown_ssml_fails_clearly():
    with pytest.raises(ValueError):
        parse_voice_script('<prosody volume="x-loud">Hi</prosody>')
```

- [ ] Run focused tests. Implement DeepFilterNet and retain RNNoise; create separate sample auditions before applying full-file cleanup. Correct model latency, preserve duration, copy the video stream, and measure active-speech RMS alongside the historical whole-track RMS so removed background noise does not force excessive voice gain. Record the chosen level policy; do not normalize final mix LUFS here.
- [ ] Make voice identity owner-configurable; require a supplied reference for cloning. Use the Base cloning model for that task rather than silently selecting a fixed CustomVoice speaker. Preserve supported pronunciation, rate and pause behavior using text segmentation, inserted silence and bounded local tempo adjustment. Keep context across per-beat requests; unsupported expression controls are explicit errors.
- [ ] Preserve the beat file/MP3/manifest interface and record model/ref hashes. Remove the private author voice ID from operational defaults. Keep it only in historical evidence where necessary.
- [ ] Run voice identity and intelligibility auditions plus clean/hum/hiss/wind/water/overlapping-noise trials. Compare before/after at matched speech level. Measure drift, clipping and audible artifact rates; document cases the selected cleanup model cannot pass and audition a second local model before declaring parity. Run `python -m pytest tests/test_voice_script.py tests/integration/test_voice.py -q`; commit.

**Pass:** Denoise does not damage the voice or timing; cloned speech uses the correct person, has the intended wording/pauses, and remains consistent across beats.

## Task 8 — Local sound effects, music, catalogs and stem mixing

**Files:** Create `tools/providers/sfx_moss.py`, `sfx_procedural.py`, `music_acestep.py`, `tools/audio_assets.py`, `tests/test_audio_assets.py`, `tests/integration/test_sound.py`, `docs/benchmarks/sound.md`; update `gen_sfx.py`, `gen_music.py`, `mix_sfx.py`, `mix_music.py`, `make_stems.py` and related skills.

**Interfaces:** `cue_sample(at_ms: int, onset_ms: int, sample_rate: int) -> int`; `normalize_asset(path: Path, target_lufs: float, ceiling_db: float) -> dict`; `catalog_upsert(catalog: Path, asset: dict) -> None`. Asset metadata preserves stable ID, tags, prompt, native/normalized formats, measured onset, loudness, duration, provider revision and license/provenance.

- [ ] Write the onset alignment regression:

```python
from tools.audio_assets import cue_sample
def test_cue_accounts_for_leading_silence():
    assert cue_sample(at_ms=2500, onset_ms=120, sample_rate=48000) == 114240
```

- [ ] Run tests; implement library-first reuse and deterministic synthesis for simple clicks/pops/tones. Missing arbitrary effects use MOSS-SoundEffect with its pinned tokenizer. Preserve prompt/duration control and verify actual output duration; short effects may be trimmed only without cutting the intended event/tail. Benchmark Dasheng only as an explicit alternative; upsampling its 16 kHz output is not improved fidelity.
- [ ] Implement ACE-Step instrumental beds and existing catalog/mix handoffs. Generate long enough to supply requested duration, then trim/fade at musical boundaries or use a reviewed loop. Preserve deliberate vocal/music options used by the existing CLI; instrumental generation must not introduce stray speech.
- [ ] Preserve existing LUFS/peak catalog targets and per-cue gains. Measure actual audible onset and offset placement against word/visual cues. Test ducking, negative or out-of-range cue positions, empty plans, overlapping cues and clipping. Regenerate or clear bundled starter assets without losing IDs and provenance.
- [ ] Verify full-length aligned voice/SFX/music/pickup stems and final mux against approved plans. Run `python -m pytest tests/test_audio_assets.py tests/integration/test_sound.py -q`; audition 20 representative cues and three music briefs. Save accepted and rejected results with reasons, update docs and commit.

**Pass:** Both precise reusable UI effects and novel prompt-generated effects work; music and stems preserve creative controls, timing and loudness.

## Task 9 — Hybrid images, local generation and shared asset handoff

**Files:** Create `tools/codex_image_handoff.py`, `tools/image_routing.py`, `schemas/codex-image-request.schema.json`, `tests/test_codex_image_handoff.py`, `tests/test_image_routing.py`, `tools/providers/image_qwen.py`, `tools/thumbnail_spec.py`, `tests/test_thumbnail_spec.py`, `tests/integration/test_thumbnail.py`, `config/workflows/qwen-image.json`, `config/workflows/qwen-edit.json`, `docs/benchmarks/thumbnails.md`; update `gen_thumbnail.py`, `thumb_scrim.py`, `composite_logo.py`, `remotion/src/fonts.ts`, brand/thumbnail/packaging skills.

**Interfaces:** `recommend_image_route(requirements: dict) -> str` returns `codex_builtin` or `local`; `import_codex_image(request_path: Path, output_path: Path, reported_model: str | None) -> dict` validates the output and emits the shared result; `validate_thumbnail_spec(spec: dict) -> list[str]`; image requests include prompt, ordered references, seed, aspect, requested dimensions, edit mode and text layers. Results include native resolution and any resampling/compositing operations. Keep existing `--prompt-file`, repeated `--ref`, `--out`, `--jpg`, seed and dry-run semantics.

- [ ] Write a missing-reference regression:

```python
from tools.thumbnail_spec import validate_thumbnail_spec
def test_likeness_request_requires_reference():
    errors = validate_thumbnail_spec({"prompt":"presenter smiling", "likeness":True,
        "refs":[], "width":1280, "height":720})
    assert "likeness requires at least one reference image" in errors
```

- [ ] Write routing and handoff regressions before implementation. A standalone thumbnail and a complex multi-reference thumbnail can recommend Codex; requirements for unattended multi-shot execution or unavailable native controls recommend a qualified local provider. Test strict local override, absent native capability, approval boundaries, output validation, and resume without duplicate generation. Mock all hosted operations in automated tests.
- [ ] Update thumbnail, packaging and orchestration skills to explain the route and obtain scoped approval only when needed. Check built-in tool availability on the actual Codex surface. GPT Image 2 is the target, but the inspected tool has no model selector: retain reported model provenance or unknown, and surface an unverifiable hard model requirement. Never silently switch models or fall back to CLI/API billing.
- [ ] Implement request export and result import as an agent-mediated bridge. Python writes the request and validates/imports the artifact; the Codex skill invokes the available native image tool. Include purpose, ordered selected references and hashes, scope/approval ID, job ID and state. Copy generated output into project-owned versioned assets. Reconcile an existing generation receipt after interruption before considering another call. Require no Qwen installation for this route.
- [ ] Run tests; implement pinned Qwen-Image-2512 generation and Qwen-Image-Edit-2511 multi-reference editing through a local inference environment. A workflow JSON describes only approved local nodes/adapters. Do not install arbitrary ComfyUI custom nodes or call hosted services from them.
- [ ] Preserve fully generated image/text mode and add optional deterministic typography/logos for exact brand text. Keep raw PNG, editable layer/spec metadata, provenance sidecar and a validated compressed JPG. Label native generation versus upscaling; do not describe an upscale as native 4K.
- [ ] Cache or bundle appropriately licensed fonts with notices. Prove brand proof, example TSX, screenshots and thumbnail composition render with external network denied. Brand files change together.
- [ ] Generate three genuinely different thumbnail bets under one title, plus an edit retaining face/room identity across multiple references. Inspect text spelling, resemblance, hands, composition and 160px legibility. Run `python -m pytest tests/test_thumbnail_spec.py tests/integration/test_thumbnail.py -q`; record memory/runtime and review. Commit.

**Pass:** Local packaging includes actual locally generated, reviewed images. Approved hybrid packaging includes a validated native Codex artifact, scoped approval and provenance, and the same downstream handoff. Neither route accepts a text-only prompt or generic presenter in place of requested likeness. Demonstrating hybrid output does not waive local parity. Run the routing/handoff/policy tests alongside the thumbnail suite.

## Task 10 — Generated video, avatars, optional worker and Shorts pilot

**Files:** Create `tools/providers/video_wan.py`, `avatar_infinitetalk.py`, `avatar_musetalk.py`, `tools/worker/{__init__,client,server,schemas}.py`, `config/worker.example.toml`, `tests/test_worker.py`, `tests/integration/test_generated_video.py`, `docs/worker.md`, `docs/benchmarks/video-avatar.md`; update `gen_video.py`, `gen_avatar.mjs`, `make_verdict_page.mjs` and Shorts/extended skills.

**Interfaces:** `validate_worker_request(payload: dict) -> list[str]`; worker routes `POST /jobs`, `GET /jobs/{id}`, `POST /jobs/{id}/cancel`; schemas accept only registered task names and asset hashes. `MediaRequest.task` is `video_t2v`, `video_i2v`, `avatar_i2v`, or `avatar_v2v`; requested duration/aspect/resolution are explicit capability requirements.

- [ ] Write the request validation regression:

```python
from tools.worker.schemas import validate_worker_request
def test_worker_does_not_accept_shell_execution():
    assert validate_worker_request({"task":"shell", "command":"anything"}) == ["unsupported task: shell"]
```

- [ ] Run tests. Add authenticated transport, content hashes, resumable transfers, bounded polling, cancellation, disk-space checks and output validation. Transfer source inputs only to the configured user-controlled worker. CPU/MPS/CUDA support is per provider, not inferred globally from the host OS.
- [ ] Implement Wan T2V/I2V and InfiniteTalk image/audio plus video/audio paths. MuseTalk is a dubbing alternative; evaluate LongCat-Video-Avatar 1.5 if InfiniteTalk fails identity/motion trials. Inspect every transitive checkpoint license before enabling the adapter. No existing paid endpoint is removed until its used capability has a passing local path or is explicitly recorded as unresolved.
- [ ] Preserve legacy wrappers and input controls; translate endpoint-specific settings into declared capabilities. Store generic provider metadata alongside any retained legacy sidecars. Normalize playback pixel format/FPS without hiding native generation limits. Preserve or mute generated audio according to the existing compositing contract.
- [ ] Build a 35–50s owner-configured vertical pilot: approved script → per-beat voice audition → reference/still approval → independently generated avatar bursts and B-roll → TSX evidence/name/CTA beats → SFX audit → final review. Do not depend on the author's private post repository or hardcoded identity. Preserve both portrait-video and still-reference dubbing cases.
- [ ] Run `python -m pytest tests/test_worker.py tests/integration/test_generated_video.py -q`; test worker disconnect, duplicate submission and cancellation. Compare motion, lip sync, likeness, reference continuity, actual resolution, memory and rerolls. If no local model passes a required capability, leave this task open rather than claiming full parity. Commit passing code/docs.

**Pass:** Real generated clips and both avatar input modes are reviewable from the Mac workflow. The worker improves compute availability without adding a paid generation dependency.

## Task 11 — Local tracker and verified private-draft publishing

**Files:** Create `tools/tracker.py`, `tracker_store.py`, `tools/editor/tracker.html`, `tools/publish_gate.py`, `tests/test_tracker.py`, `tests/test_publish_gate.py`, `docs/publishing.md`; update `notion_sync.py`, `yt_upload.py`, `yt_stats.py`, `yt_upload_SETUP.md`, tracker/publishing skills.

**Interfaces:** `upsert_project(index: Path, project_id: str, properties: dict, script: str, apply: bool = False) -> dict`; `can_publish(artifact_hash: str, qa: dict, approval: dict) -> bool`. Proposed tracker CLI: `python tools/tracker.py P --apply`, `--resync`, `--props-only`, `--stage`, `--list`; default is a dry run. Canonical project files rebuild the index.

- [ ] Write the gate regression:

```python
from tools.publish_gate import can_publish
def test_changed_video_invalidates_approval():
    qa = {"artifact_hash":"new", "passed":True, "unresolved":[]}
    approval = {"artifact_hash":"old", "approved":True}
    assert can_publish("new", qa, approval) is False
```

- [ ] Run tests. Implement stable project IDs, exact match-before-create, duplicate detection, stage filtering, local script display, dry-run/apply and explicit resync. Treat ambiguous title matches as review cases. Keep optional Notion synchronization separate and preserve its existing metadata mapping.
- [ ] Correct upload paths for this repository. Preserve title, description, tags, category, thumbnail, privacy and scheduling fields. Store upload receipt/video ID and support retrying metadata/thumbnail steps without creating duplicate videos. Keep OAuth credentials outside logs/source.
- [ ] Require QA and review receipts matching the exact video and packaging hashes; changed renders invalidate them. Default to private. Do not remove explicit public/scheduling capabilities, but require deliberate publication approval. Document manual YouTube Studio A/B testing separately; writing three files does not start an experiment automatically.
- [ ] Test local tracker updates with `python -m pytest tests/test_tracker.py -q`. Publication functionality remains retained; Tyler waived publication testing, including mocked upload tests and real private uploads.

**Pass:** Local organization works offline; supported publish metadata and analytics remain available through explicit YouTube operations. QA instructions are enforced, not merely described in prose.

## Task 12 — Preserve rendering and create small upstream extension boundaries

**Files:** Create `schemas/timeline.schema.json`, `remotion/src/lib/extensions/{transitions,effects,filters}.tsx`, `tools/timeline_extensions.py`, `tools/upstream_audit.py`, `tests/test_timeline_extensions.py`, `docs/upstream/porting.md`; update `bake.py`, rendering/QA scripts and relevant skills. Keep upstream libraries and examples in place.

**Interfaces:** `apply_timeline_extensions(timeline: dict) -> dict` preserves legacy behavior and unknown fields. Extension declarations use `id`, `version`, `target`, time range, parameters and explicit `time_policy`. `upstream_audit(base_sha: str, candidate_sha: str) -> dict` reports changed skills, schemas, APIs and dependencies without merging.

- [ ] Write the compatibility test:

```python
from tools.timeline_extensions import apply_timeline_extensions
def test_legacy_timeline_remains_valid():
    timeline = {"master":"master.mp4", "master_fps":30, "shots":[],
                "preview":{"end_s":12}, "custom_note":"preserve me"}
    assert apply_timeline_extensions(timeline) == timeline
```

- [ ] Run tests. Add a frame-based crossfade, punch-in/spotlight and color-grade example with versioned parameters. For crossfade, define whether it consumes handles or overlaps timeline time; update mappings for time-changing variants. Unknown versions fail clearly rather than disappearing.
- [ ] Run registry generation, TypeScript checks and representative opaque/transparent/browser/VS Code/screencast/vertical renders. Compare old-versus-new cue frames under the same renderer/fonts; inspect composited output, not only standalone stills. Keep genuine product branding in historical examples.
- [ ] Build a manual upstream comparison command and checklist. Future updates enter a review branch, carry a new provenance SHA, port new Claude skills into Codex and rerun provider/network contracts. Do not auto-enable new cloud dependencies or upgrade Remotion's major version.
- [ ] Run `python -m pytest tests/test_timeline_extensions.py -q` and `npm --prefix remotion run gen`; run type checking from the Remotion directory and save cue-frame receipts. Update the patch ledger and docs; commit.

**Pass:** Existing projects and components remain compatible, and roadmap additions have concrete boundaries without a speculative whole-editor rewrite.

## Task 13 — Demonstrate full parity on both Codex models

**Files:** Create `tests/acceptance/prompts/{longform,shorts,resume,thumbnail-edit,hybrid-thumbnail,hybrid-handoff}.md`, `tests/acceptance/manifest.json`, `tools/run_acceptance.py`, `docs/benchmarks/release.md`, `docs/known-limits.md`; update README and feature matrix from actual results.

**Interfaces:** `run_acceptance(profile: str, model: str, fixture: str, output_dir: Path) -> dict` launches the selected Codex model with the fixed task prompt and captures tool/artifact receipts. It never autonomously approves human gates or publishes. The CLI exposes the same named arguments.

- [ ] Define the four local acceptance prompts: full long-form edit, vertical avatar/B-roll pilot, fresh-task resume after interrupted generation, and reference-preserving thumbnail iteration. Use separate copies of fixture projects for each model so the second does not inherit completed creative work.
- [ ] Execute proposed commands after the harness exists:

```bash
python tools/run_acceptance.py --profile local --model gpt-6-astra --fixture longform --output-dir work/acceptance/astra-long
python tools/run_acceptance.py --profile local --model gpt-5.6-sol --fixture longform --output-dir work/acceptance/sol-long
python tools/run_acceptance.py --profile local --model gpt-6-astra --fixture shorts --output-dir work/acceptance/astra-short
python tools/run_acceptance.py --profile local --model gpt-5.6-sol --fixture shorts --output-dir work/acceptance/sol-short
```

- [ ] Add two hybrid scenarios on both Astra and Sol: bounded native thumbnail generation and imported native key imagery feeding a local pipeline. Use actual user approval for live calls; otherwise report live hybrid acceptance as pending. Verify approval reuse within scope, changed-reference and exhausted-scope blocking, strict local rejection, unavailable native tool handling, actual/unknown model provenance and interrupted generation/import recovery. Exercise native calls in an equipped Codex session; a CLI-only harness must report that capability as unavailable rather than invoking a paid API.
- [ ] Run media workers with empty paid-provider credentials and external egress denied after setup downloads. Verify fonts, model loading, reference processing and inference do not leak into remote calls. Separately exercise optional cloud adapters only with mocks unless a real call is authorized.
- [ ] Require zero accepted harmful cuts, median/p95 timing thresholds, one-frame SFX onset alignment and ≤40 ms fixed A/V drift. Audit identity, voice quality, prompt adherence, image text, alpha composition, motion, aspect/resolution and stem alignment. Preserve the author's useful creative gates with the current owner as reviewer.
- [ ] Record both models' skill selection, failure recovery, resume behavior, time, token usage where available, peak media memory, disk and rerolls. Sol may take more iterations; it may not lose a capability or skip verification. Avoid promising identical creative choices across models.
- [ ] Self-review every row of the feature matrix against actual artifacts; any unsupported generation category keeps full-parity release open. Document distinct core/extended readiness rather than presenting partial readiness as complete. Update setup, licenses and upstream ledger, run the focused release checks once, and commit.

**Pass:** A reviewer can open the complete long-form and Shorts outputs and trace every requirement to evidence on both models. Any remaining hardware, license or quality limitation is explicit.

## Execution handoff

The recommended next implementation action is Task 1, followed by local runtime preflight and the feasibility portions of Tasks 3–5 plus small trials drawn from Tasks 7, 9 and 10. The confirmed project base and execution host is this local M4, m4-mini.local, with 24 GB unified memory. Retain Remotion and qualify only single-M4 candidates under the revised first-release criteria; the supplied video is not a completion benchmark. The hostname and project location are verified; later personal test assets are just-in-time inputs. MBP access is neither required nor authorized. This planning turn installs no media stack, changes no fork code, uploads nothing and makes no claim that local quality parity is already proven.

If the user chooses execution, proceed inline with Superpowers executing-plans and review each independent task. Subagent-driven execution remains an alternative if the user explicitly selects it. No recurring monitoring or automatic upstream merge job is part of this plan.
