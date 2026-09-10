# Production quality workflow

[Production rules](production-rules.md) are the single authoritative source. Every production uses them, with editing supplied footage as the default. They are read at runtime, not copied into Python or individual skills. Stable IDs identify each rule; its full current wording controls the review. Edit that file to change policy. The `final-required` metadata names rules that cannot be waived at final QA.

Each rule's bold lead names its primary responsibility. A cross-reference is not a
substitute for the referenced review. The same evidence file may support several rules,
but record the distinct finding for each; do not copy a generic "quality checked" reason.

The September 10 consolidation leaves 32 active rules (96 dispositions across three
phases). R16 is retired into R15; R30 is reserved for its historical meaning and moved to
the separate [workflow qualification contract](workflow-qualification.md). Do not renumber
surviving rules, reuse retired IDs, rewrite historical records, or submit retired IDs in
fresh checklists. This is not automatic migration of approvals: regenerate and reassess
all phases under the current policy hash. Production QA and reusable-workflow
qualification remain separate decisions.

## Before production

The responsible AI reads all current rules and generates a checklist before editing. It establishes the brief, reviews the source, and records a specific plan or justified non-applicability for **every** rule. Evidence can include the brief, source inventory, inspection report, and editorial plan. A planned review is not a completed review.

Run commands from the repository root, substituting the actual project directory:

```sh
mkdir -p PROJECT/work/quality
.venv/bin/python -m tools.production_quality checklist PROJECT --phase before > PROJECT/work/quality/before.json
```

Edit that JSON: retain its phase and policy hash; fill each rule's `status`, `reason`, and `evidence` (paths to nonempty files). Before production, use `planned` or `not_applicable`; unresolved items may be `pending` or `fail`. Give individual explanations, not a blanket affirmation. Evidence paths resolve from the command's working directory; prefer absolute paths. Keep evidence in separate stable files, not the mutable checklist or coordinator state.

```sh
.venv/bin/python -m tools.production_quality record PROJECT --phase before --file PROJECT/work/quality/before.json --reviewer codex
.venv/bin/python -m tools.production_quality gate PROJECT --phase before
```

## During production

Read the rules again at each editing checkpoint and whenever the policy changes. Route production commands—including ingest, generation, cuts, cleanup, Remotion rendering, mixing, packaging, and corrective renders—through the action coordinator. Run review/checklist/gate/finalization and tracker commands directly, outside `run`; they do not edit media and must not create a new editing revision. Direct helper calls remain available for engineering diagnostics; they are not the production workflow.

```sh
.venv/bin/python -m tools.production_quality run PROJECT --rules R04 R13 R21 --reason 'Render the reviewed cut plan' --evidence PROJECT/work/edit-plan.md -- .venv/bin/python tools/render_cuts.py PROJECT --style natural --mode preview
```

Choose the rule IDs actually relevant to each action. The coordinator requires the full pre-production gate, journals command/purpose/rule IDs/evidence, and records logs and failures. It does not grant network, hosted generation, or publication authorization. Apply existing resource and approval restrictions first.

After each meaningful editing action, inspect its actual output against the applicable rules and record observations. Generate and record a `during` checklist using the same commands with `--phase during`; use `pass`, `not_applicable`, `pending`, or `fail`. Reassess all rules after the last editing action. New actions invalidate earlier during/final reviews. Do not perform unrelated edits until the preceding action's output has been inspected; correction of a discovered fault remains allowed.

A failed or interrupted action blocks QA until explicitly resolved with evidence:

```sh
.venv/bin/python -m tools.production_quality resolve PROJECT --action-id ACTION_ID --reason 'Describe the cause, correction, and successful verification' --evidence PROJECT/work/correction-report.md
```

Do not resolve a failure merely to clear the gate. Preserve successful outputs and original media.

## After production: final QA

Register every delivery file before reviewing it, including alternate formats and associated captions/stems where required:

```sh
.venv/bin/python -m tools.production_quality deliverables PROJECT --paths PROJECT/output/final.mp4 PROJECT/output/final.srt
.venv/bin/python -m tools.production_quality checklist PROJECT --phase after > PROJECT/work/quality/after.json
```

The AI reviews every rule against those exact files. Record technical checks, visual inspection, complete normal-speed playback with audio, and user acceptance as separate findings. Evidence should identify files, review method, reviewer, findings, and corrections. Automated decoding, screenshots, ASR agreement, or a successful command cannot substitute for watching and listening. If a required review cannot be performed, record it as pending and request only the intervention needed to finish it. Do not silently claim a human review occurred.

```sh
.venv/bin/python -m tools.production_quality record PROJECT --phase after --file PROJECT/work/quality/after.json --reviewer codex
.venv/bin/python -m tools.production_quality finalize PROJECT
.venv/bin/python tools/tracker.py PROJECT --stage complete --apply
```

Finalization requires current acceptable evidence for all three phases, unchanged registered deliverables, and no unresolved actions. The tracker refuses completion/ready stages without a fresh receipt. QA completion **does not authorize publication**. Publication still requires approval of the actual deliverable and destination; publication tests remain waived.

## Changes and enforcement boundaries

Every byte change to the authoritative rules file invalidates old reviews and receipts. New/removed rules change checklist coverage automatically. Regenerate checklists, reread the rules, reassess evidence, and finalize again. Changed evidence invalidates affected reviews; changed delivery selection/files invalidates final QA. New editing activity invalidates during/final review. Retain historical receipts as history, never as proof of current acceptance.

Use `production_quality status PROJECT` to inspect all gates; use `gate` for a nonzero exit when a phase fails. Persisted tracker labels are historical metadata: consumers deciding whether a production is currently complete must call `require_complete(project)`, which revalidates the policy and evidence.

Software verifies coverage, dispositions, hashes, and action state. The responsible AI/reviewer must establish the truth and adequacy of the evidence. This is not an operating-system sandbox against arbitrary commands or dishonest attestations. Existing productions are not automatically certified under these rules; the generated Lighthouse exercise does not qualify editing authentic user footage.

## Native Studio projects

If `work/studio/project.json` exists, media actions also enforce the current editable
Studio workflow prerequisites. `run` defaults to `--stage edit`; earlier preparation
uses an explicit appropriate `--stage intake` or `--stage source_understanding`.
Do not classify substantive cuts as intake to bypass source/strategy review. Final
receipts also bind Studio inputs and prerequisite evidence; changed briefs, sources,
workflow or feedback invalidate completion in both the app and CLI tracker.
