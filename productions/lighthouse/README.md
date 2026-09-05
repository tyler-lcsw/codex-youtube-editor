# The Little Lighthouse

An original story production using the qualified M4 workflow. Start with the [specification](../../plan/The%20Little%20Lighthouse%20%E2%80%94%20Production%20Specification.html) and `spec.json`. Local project assets live in ignored `media/projects/lighthouse/` and deliverables in `videos/lighthouse/output/`.

This is fictional animation. Its diagnostic screen is an illustrated story device, not a recording or a demonstration of real hardware. The narrator uses a macOS synthetic reference, not a person's voice. The procedural score is a small original composition, not proof of arbitrary music-model generation. Publication and hosted generators are retained but not invoked.

Recipes are explicit local commands, run from the repository root with `.venv/bin/python`. Run only one media stage at a time and unload LM Studio before media inference. The generation recipe validates cached output hashes; change the recipe only with a new output/version when intentionally requesting a different take. No provider fallback is implemented.

Execution order:

1. `generate.py voice`, then `generate.py images` (explicitly installed local providers; preserved per-take names).
2. `prepare_sources.py`, then `tools/transcribe.py videos/lighthouse --clips arrival failure diagnosis repair home --language English`. Inspect word timing; resolve failures before cutting. The recorded two replacement takes are part of the specification.
3. `tools/render_cuts.py videos/lighthouse --style natural --mode preview`, then `--mode final`; `tools/clean_voice.py videos/lighthouse/output/master-natural.mp4 -o videos/lighthouse/output/clean.mp4`.
4. `plan_timeline.py`; `render_shots.py LighthousePanel LighthousePanelDetail LighthouseWait LighthouseTitle LighthouseDiagnosis LighthouseRepair LighthouseEnd`; `tools/bake.py videos/lighthouse/work/timeline.json`.
5. `audio_finish.py`; `prepare_short.py`; `render_shots.py LighthouseShort LighthouseThumbA LighthouseThumbB LighthouseThumbC`.
6. Run `finalize_media.py` to mux the current short audio to its exact declared duration, export thumbnail JPEGs and captions; then run `verify_delivery.py`. See the execution report for the recorded final values and artifacts.

Run these scripts as `.venv/bin/python productions/lighthouse/<script>`. `check_audio_mapping.py` needs NumPy and is run with `.envs/audio/bin/python`; it measures decoded audio placement, not physical lip sync. `tools.verify_render` supplies the independent word check. Large generated assets and local work logs stay out of Git. Original TTS/image outputs have provenance receipts; rendered delivery hashes are included in the report.

The renderer uses the installed Node 24 path recorded on this M4. Adjust that explicit path for another qualified host. The voice reference is an existing ignored synthetic fixture; a clean checkout must supply that declared reference rather than silently choosing a new identity.
