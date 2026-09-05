# M4 First Release — Runtime and Memory Decision

September 5, 2026. This scope revision takes precedence over conflicting full-parity gates in the original design and 13-task implementation plan. Tyler explicitly requested a single-node first iteration and a PAIR evaluation. The upstream video is background research, not a completion benchmark.

## Implementation outcome

The approved procedure has now been implemented. Qwen3.5 4B/9B, local TTS and Klein weights were downloaded and used. Read [measured results](../docs/benchmarks/first-release.md) and [setup](../docs/setup-macos.md) before the historical assessment below. The installed MLX engine ignored the requested 4K context; production requests are bounded, parallelism is verified as one, and no engine-level 4K cap is claimed. The earlier no-download/unqualified statements below describe the pre-implementation assessment.

## First-release success

- Codex-native skill discovery and a reproducible editing workflow on this M4: ingest, local transcription, reviewed cuts, retained Remotion compositions, audio mixing, packaging and export. GPT-6 Astra remains recommended; GPT-5.6 Sol remains supported. Local LLMs assist bounded tasks; they do not replace those Codex models.
- Preserve existing features, formats, publication code and future provider/worker extension points. Do not delete a capability because its preferred local model is too large. Explicitly mark unqualified resource-heavy providers as deferred; their quality parity and an avatar/video showcase do not block this first release.
- Qualify only models that fit comfortably on this 24 GiB node. No dependency on bee01, M1 mini, MBP or a future cluster. No remote setup or MBP-to-M4 control is authorized by this revision.
- Run functional tests and representative original/synthetic fixtures with explicit timing and review gates. Retain detection of corrupt artifacts, unresolved word timing, unsafe cut boundaries, failed jobs and unauthorized hosted fallback. A polished recreation of the supplied video and a large human comparison corpus are not first-release requirements.
- Keep publication functionality; publication testing remains waived. Native Codex image use remains subject to scoped approval. No quality-equivalence claim for untested media providers.
- Include a bounded single-node PAIR trial. Distinguish proxy/telemetry success, MLX inference success and multi-node scheduling. Multi-node failover, speedup and aggregated capacity are future validation.

## Memory policy

PAIR routes each request to one eligible machine. It does not shard a model or pool memory. The proposed 24 + 16 + 16 GB Macs provide potential aggregate throughput, not a 56 GB model allocation. This agrees with [NVIDIA's architecture](https://github.com/NVIDIA/Personal-AI-Router/blob/main/docs/architecture.mdx).

Use an initial engineering budget of **8 GiB for macOS, Codex and ordinary apps; 12 GiB target peak for the active inference job; 4 GiB contingency**. These are allocation policies, not measured OS consumption or a memory guarantee. Include weights, KV cache, vision tokens, activations, draft models and runtime allocations in the job budget. Start text at 4,096 context tokens, one prediction at a time. Raise to 8,192 only after measuring the actual workload. Do not enable maximum advertised context by default.

Run one heavy model job at a time, and unload it before another large model or Remotion render. Require normal memory pressure and no sustained new swap/pageout growth during a warm representative trial. A model file smaller than 24 GB is not sufficient proof. Reject a candidate that depends on swap or exceeds the comfortable envelope; defer instead of forcing system memory settings.

## Runtime recommendation

**Use LM Studio/llmster as the initial PAIR-backed MLX text/vision runtime. Retain Ollama as an optional alternative. Keep specialized media inference in explicit, separately locked local adapters.**

| Consideration | LM Studio | Ollama |
|---|---|---|
| MLX today | Native MLX text/vision engine, backed by mlx-lm and mlx-vlm | Also supports MLX; older statements that it only uses llama.cpp are obsolete |
| Model exploration | Direct Hugging Face MLX discovery, local import, explicit quantizations and runtime selection make it a good fit for this project | Convenient named model packages and automation; verify exact architecture/quantization and actual runner for each model |
| Performance | Measure our model and prompts; no universal speed advantage established | Recent MLX NVFP4, caching and Gemma 4 MTP optimizations are credible reasons to benchmark it; vendor M5 Max results are not M4 measurements |
| PAIR | Supported via OpenAI-compatible proxy; local embedding path passed here | Supported via Ollama/OpenAI-compatible proxy; local engine running, currently no models |
| Openness | MLX engine is MIT; the LM Studio application is not fully open source | Core repository is MIT; each weight license still needs checking |
| Media generation | Do not assume its LLM engine runs arbitrary MLX audio/diffusion models | Experimental image generation exists, but endpoint/editing/PAIR compatibility needs separate validation |

The recommendation is about workflow and compatibility, not a verified numerical claim that LM Studio has the most models. Neither vendor publishes a directly comparable count of working MLX architectures, quantizations and capabilities. Safetensors is a container, not a compatibility guarantee. Keep the LM Studio integration optional so the local media pipeline does not acquire a compulsory proprietary dependency.

Sources: [LM Studio MLX engine](https://github.com/lmstudio-ai/mlx-engine), [MLX model discovery](https://lmstudio.ai/docs/cli/local-models/get), [Ollama MLX update](https://ollama.com/blog/mlx-performance), [Gemma MTP](https://ollama.com/blog/faster-gemma-4-mlx-mtp), [Ollama license](https://github.com/ollama/ollama/blob/main/LICENSE), [LM Studio terms](https://lmstudio.ai/app-terms), [Ollama experimental images](https://ollama.com/blog/image-generation).

## Suggested models

The package sizes below were read from Hugging Face metadata, in decimal GB. Peak ranges are conservative planning estimates, **not measured benchmarks**. Download and load one selected model at a time; no new LLM weights were downloaded in this assessment.

| Model | Download | Role | Initial context / estimated job memory |
|---|---:|---|---|
| [Qwen3.5-4B MLX 4-bit](https://huggingface.co/mlx-community/Qwen3.5-4B-4bit) | 3.06 GB | First PAIR MLX trial; tags, shot descriptions, short summaries and basic frame inspection | 4K; roughly 5–8 GiB |
| [Qwen3.5-9B MLX 4-bit](https://huggingface.co/mlx-community/Qwen3.5-9B-4bit) | 5.98 GB | Preferred everyday candidate for editorial assistance and visual descriptions | 4K then measured 8K; roughly 8–12 GiB |
| [Qwen3.5-9B MLX 6-bit](https://huggingface.co/mlx-community/Qwen3.5-9B-6bit) | 8.22 GB | Optional quantization-quality comparison after 4-bit passes | 4K; roughly 11–14 GiB; may exceed our 12 GiB target and is not the default |

Exact inspected revisions: 4B `0e7ffd5c629ef7719d4cbc04069232580bfa9d9c`; 9B 4-bit `8b2b98c00a6b4d291155e4890773ca8f769aee53`; 9B 6-bit `76fe4065e622cf34990d3c13ef80ec8531c9a0f7`. LM Studio documents Qwen3.5 in [both MLX and GGUF with vision/tool use](https://lmstudio.ai/models/qwen3.5). Actual tool-call parsing and vision must still pass our installed-runtime tests.

For an Ollama comparison, consider `gemma4:12b-mlx` at 4K context after inspecting its complete package and load estimate. Its MLX/MTP path is documented by Ollama, but it is not yet qualified for our comfortable memory budget. Do not automatically substitute a 27B/30B/35B model because its active-parameter count looks small: resident weights still matter.

For the editor's specialized media tasks:

- Retain the already tested Qwen3 ASR 0.6B and forced aligner 0.6B in MLX Audio, loaded sequentially. The existing short trial peaked at 2.09 GiB MLX memory. DeepFilterNet3 also passed an offline cleanup trial.
- Trial [Qwen3 TTS 0.6B Base](https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-Base) through MLX Audio for reference-voice narration. Do not assume LM Studio exposes this TTS model. Quality and real peak remain unqualified.
- Replace the first image feasibility candidate with **[FLUX.2 Klein 4B](https://huggingface.co/black-forest-labs/FLUX.2-klein-4B)**, quantized through the installed MFLUX backend. It supports generation and multi-reference editing; its 4B weights use Apache 2.0. Start at 512px and measure complete pipeline memory before higher resolution. The vendor's roughly 13 GB GPU figure is not a Mac memory measurement or proof of our 12 GiB target.
- Defer the inspected Qwen Image 2512/Edit 2511 MFLUX packages (27.61/28.96 GB), large avatar/video models and any media candidate that fails the envelope. Keep their extension contracts. Approved native Codex images remain available for appropriate work.

## Live PAIR assessment

Local inspection found PAIR running, Ollama **0.33.3** listening on loopback **11435**, and LM Studio's **llmster** on **1235**. PAIR owns client proxy ports **11434** and **1234**. Do not install another server onto these ports. Installed LM Studio engines: MLX **1.11.0**, llama.cpp **2.31.2**. No large LLM was installed or loaded; one existing 84.11 MB Nomic embedding GGUF was available.

A direct request to 1235 and the same request through PAIR 1234 each returned two finite 768-dimensional embeddings. Maximum component difference was zero. PAIR recorded a completed LM Studio job with matching originating and scheduled local node IDs. The direct cold request took 13.204 seconds; the warm proxy request took 0.016 seconds. **This is not a speed comparison.** The model was unloaded afterwards. Raw receipt: `work/benchmarks/pair-embedding-smoke.json` (ignored working artifact).

This proves local model discovery, forwarding and completed-job reporting for embeddings. It does not prove MLX generation, streaming cancellation, load admission, cross-node recovery or throughput. The next bounded test should use Qwen3.5 4B: direct versus routed deterministic prompts, streamed output, cancellation, a structured shot-list response, one synthetic image input, missing-model failure and measured memory/context. Require receipts naming the serving M4 and actual MLX runner. No other Mac or bee01 is part of this first-release test.
