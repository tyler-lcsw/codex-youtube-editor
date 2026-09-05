# Media provider policy

The migration is in progress; see `implementation-status.md` for implemented versus pending
paths. Legacy paid CLI tools must not be called merely because they remain in the source.
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
