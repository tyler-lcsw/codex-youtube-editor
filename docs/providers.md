# Media provider policy

See `implementation-status.md` for the implemented first-release paths and explicit deferrals. Legacy paid CLI tools must not be called merely because they remain in the source.
Local generation is default. A missing local provider must report setup requirements, never
fall back to an API. Model downloads are explicit setup operations, separate from inference.

Hybrid thumbnails use native Codex image generation after approval of provider, purpose,
selected references and bounded iterations. The built-in interface may not report its image
model; record unknown honestly. Do not claim exact GPT Image 2 selection without evidence.
An API/CLI image path is a separate paid choice requiring approval.

Local inference tests run with external networking denied after assets are cached. Codex
itself is online; transcripts and review frames supplied to it are not an offline workflow.
Publishing, browser capture and approved hybrid generation are separate network operations.
Remotion remains retained with its actual license, regardless of local model licensing.

## Current local commands

See `setup-macos.md` for pinned setup and `benchmarks/first-release.md` for measured results.

| Capability | Provider / entry point | Current scope |
|---|---|---|
| Transcription/alignment | `tools.transcribe` / `tools.media asr` | Local Qwen; unresolved timing requires correction |
| Voice cleanup | `tools/clean_voice.py` | DeepFilterNet default; original preserved |
| Reference narration | `tools.media tts` | Explicit short reference + transcript, scripted pauses |
| Images/editing | `tools.media image` | Klein 4B, 393216 pixels, at most one reference; visual review required |
| Editorial text | `tools.providers.local_llm` | Optional PAIR, bounded JSON; rejects empty reasoning-only answers |
| SFX | Catalog + `providers.sfx_procedural` | Click/pop/tone only; arbitrary generated sounds deferred |
| Music | Existing licensed catalog + `mix_music.py` | Generation deferred |
| Tracker | `tools.tracker` | Local JSON/SQLite, dry-run before apply |
| Avatar/video | Retained interfaces | Local inference deferred; no equivalence claim |

Legacy hosted generators now require `--allow-cloud` before generation. Their dry-run/help modes do not grant permission. The user approved setup/model downloads for this implementation; that does not grant unbounded future hosted calls. Human review of words, voice likeness, image artifacts and final creative quality remains part of using the editor.

## Native image recovery

The sequence is `prepare` → scoped approval → `claim` → `begin REQUEST_JSON` → one native tool call → `import REQUEST_JSON IMAGE_PATH`. `begin` records a one-time dispatch marker before the call. Reclaiming cannot reset it. A marker proves intent to dispatch, not whether the native service completed; an interruption requires recovering the existing output or a new approved request, never an automatic second call.

Imports revalidate approval scope and references, write a separate import attempt, and publish its receipt only after artifacts are valid. Corrupted imported artifacts can be repaired from the original native output without another generation or another consumed reservation. The original source and older attempts remain available. No hosted call was used to test these state transitions.
