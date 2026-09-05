# Upstream maintenance and provider extensions

Fork baseline: `a6ac742b44520fd3c6aeaf3cd754e113fa334fed` from tyler-lcsw/codex-youtube-editor. Source lineage: hassancs91/claude-youtube-editor. Preserve the original README under docs/upstream and retain licenses and attribution.

Fetch upstream changes into a review branch; compare skill content, tools, TSX kits, catalog formats and roadmap additions. Adapt Claude-specific invocation to `.agents/skills` and Codex; do not restore CUDA-only assumptions or automatic hosted calls. Run the focused tests, skill audit, Remotion typecheck and a relevant real fixture before merging. Never overwrite a user's brand, reference assets or active project state during an upstream update.

`tools/providers/contracts.py` is the provider boundary; `policy.py` gates local/hosted capability and `jobs.py` provides content-derived job identity, attempts and artifact validation. The currently qualified CLI adapters are listed in `tools/media.py`. A future worker must preserve the same request/artifact provenance, explicit capabilities and failure reporting; no remote transport or automatic discovery is enabled in this release.

Add new adapters without changing historical cut/timeline formats. Preserve unknown properties when updating project JSON, use stable IDs, stage artifacts and verify hashes, and record model revision, seed, input hashes and native dimensions. Re-running an existing successful job should validate its artifacts; failed work must not erase the prior success. Specialized adapters and legacy tools are not all wrapped in the general job cache yet; do not describe the entire workflow as resumable orchestration.

Qualify each capability independently: text, vision, TTS reference modes, image edits/reference count, sound generation and video are not interchangeable. Multi-reference images, music, generative SFX, avatar and video require measured implementations before being marked local-ready. Retained hosted commands require explicit opt-in and are not first-release dependencies.

The local SQLite tracker can rebuild from canonical project files. Publication remains a separate explicit approval boundary and was not tested during this migration. Planned upstream UI/assembly/shorts features can be added behind these boundaries without requiring a Claude runtime.

## Executable audit

Compare already available commits without fetching or changing branches:

```sh
.venv/bin/python -m tools.upstream_audit --base BASE_SHA --candidate CANDIDATE_SHA --output work/upstream-audit.json
```

The JSON records resolved commit hashes and changed files grouped into skills, dependencies, tools, Remotion, schemas/config, assets and documentation. Renames appear as deletion/addition so neither side disappears from review. A missing commit fails explicitly: fetch the intended source separately, then rerun. This command does not contact upstream, merge changes or certify semantic compatibility. Its optional output file is the only write.

The first live comparison used baseline `a6ac742b44520fd3c6aeaf3cd754e113fa334fed` and PR #1 merge `a1903d1b86dbf47b3a8544119b427eee9c033a3d`; receipt is `work/benchmarks/upstream-audit.json`. Tests also verify that uncommitted work and HEAD remain unchanged.
