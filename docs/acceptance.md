# Repeatable acceptance checks

Use the app-bundled Codex CLI or pass `--codex PATH`. The manifest fixes the supported models and bounded read-only scenarios. These checks use Codex online; they do not run local media generation, publish, approve native image calls or configure other nodes.

```sh
.venv/bin/python -m tools.run_acceptance --model gpt-6-astra --fixture timeline
.venv/bin/python -m tools.run_acceptance --model gpt-5.6-sol --fixture resume
```

Fixtures: `discovery` for workflow routing, `timeline` for effect clocks/versions/export safety, and `resume` for interruption/approval/artifact recovery. Each permits at most eight repository files and requests under 350 words. CLI sandboxing is read-only; the prompt additionally prohibits provider calls. This is an instruction-bound model exercise, not a network-denied media worker.

Every invocation creates a unique directory under `work/acceptance` containing the report, JSONL events, stderr and receipt. The receipt records model, CLI version, Git HEAD, dirty-checkout status, prompt/report hashes, exit status and elapsed time. Logs may contain inspected repository context and stay ignored by Git. A changed dirty checkout is not claimed to be a perfectly reproducible source snapshot.

Status `completed_unreviewed` means the process exited successfully with a report. Review the report against the manifest's criteria; this is never automatic creative acceptance. Failures, timeouts and cancellation retain receipts. Worker cancellation terminates remaining process-group members even if the leader exits first. Models or fixtures outside the manifest fail before launch. The runner does not silently install/update a CLI or fall back to a different model.

Astra and Sol timeline reviews correctly identified master versus final-output clocks, exclusive end frames, version rejection and the distinct brightness conventions. The initial recovery reviews identified the native dispatch ambiguity and surviving-child cancellation gap; both led to concrete fixes and tests. See `docs/benchmarks/acceptance.md` for follow-up results.
