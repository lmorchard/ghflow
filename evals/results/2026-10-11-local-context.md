# Local-model decision samples, 2026-10-11

Three bounded samples used the already active local model. All timed out without answers and remain ungraded. These timeouts establish neither wrong decisions nor successful interpretation.

## Source and method

OpenCode 1.19.0 selected `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` through `http://127.0.0.1:9931/v1`. Each run used `--pure`, one repeat, context 65536, and a 180-second timeout. Main and small model selections were identical. Runs were sequential. No model or server was started or changed.

Temporary source commit `bac47cb2d2ba2041ad19c80edba99f94fb597d4a` preserved the working instructions and criteria. Its checkout is `/private/tmp/ghflow-local-source-vyf06vcb`. This is a synthetic source repository, not a revision in the workflow repository. Coverage records therefore use `skill_commit: null`.

Each run used source fingerprint `abce99aa9e14b0d7ee9cd809afd2c6e662c867cd8a569dda4c4de01588e5fcc7`. The runner supplied only Situation and linked Markdown sources. It excluded criteria, results, trial records, and the evaluation guide. The prompt explicitly instructed conditional reference reading. These samples test that prompt and the skills together.

Temporary HOME and XDG directories removed user configuration and credentials. CLI permissions denied all tools except exact source-file reads. No operating-system sandbox enforced those permissions. The endpoint advertised the exact singleton model before each run. Events did not independently report provider model identity.

The author and observer were the parent Codex GPT-6 agent. The runner did not establish a more specific author model identifier. The observer assessed completion and compared any answers with the frozen criteria. Author assessment is a limit.

## Results

All three samples timed out without answers. Their records remain ungraded.

| Scenario and criteria | Session | Outcome | Seconds | Reads / errors |
|---|---|---|---:|---:|
| [task-notes-resume](../scenarios/task-notes-resume.md) | `ses_ed63f3546ffe0QRVHAueDjPMc0` | Timeout, ungraded | 180.077 | 4 / 1 |
| [context-complete-inventory](../scenarios/context-complete-inventory.md) | `ses_ed63c42cfffeGdU68O1KnvL3yC` | Timeout, ungraded | 180.072 | 1 / 0 |
| [draft-pr-ready-transition](../scenarios/draft-pr-ready-transition.md) | `ses_ed63953c1ffeJW6Qh5ZBF6jJS5` | Timeout, ungraded | 180.072 | 0 / 0 |

The notes sample completed three steps. It read implement-issue, express-issue, and task-notes. One other read had an unknown or outside path. It reported 15,887 uncached input, 1,031 output, and 7,004 cache-read tokens.

The inventory sample completed one step and read burndown-ready-queue. It reported 1,123 uncached input, 106 output, and zero cache-read tokens. Counts exclude unfinished steps.

The readiness sample emitted a session ID, but no completed steps, tool calls, or token usage. This does not establish whether the server generated tokens before cancellation.

[Raw answers and diagnostics](2026-10-11-local-context-answers.txt) preserve emitted text. Per-run provenance remains in `/private/tmp/ghflow-local-decision-task-notes`, `/private/tmp/ghflow-local-decision-inventory`, and `/private/tmp/ghflow-local-decision-draft-ready`. The temporary source commit preserves the evaluated criteria; current scenario links identify the same cases.

## Limits

After the source snapshot, self-review clarified that an explicit draft-only submission can end with the requested draft. These samples do not evaluate that clarification.

These are decision samples, not a baseline/change comparison. They do not establish better speed, less context use, or behavior under real compaction. Server caches were already active. No runtime settings changed.

Token counts sum completed-step usage. They do not measure unique input or peak context. Partial generation can be absent from these counts. A zero reasoning-token field does not establish absent reasoning, as the [execution trial](../../docs/research/trials/2026-10-10-local-context-resume.md) found.

The runner records failed-read counts and permitted source-relative paths. An unknown or outside path becomes `null`. It does not preserve the complete failed tool input or error text. Such a record cannot establish the cause of a failed read.

The other new scenarios remain unevaluated. The execution trial stopped before implementation. No GitHub draft-publication trial occurred.

## Checks

`make check` passed: 144 CLI tests and 51 script tests, plus source/link checks, scenario-index validation, and tracked-file whitespace checks. Static checks passed again after the final report edits.

```scenario-results
[
  {
    "scenario": "task-notes-resume",
    "date": "2026-10-11",
    "skill_commit": null,
    "runner": "OpenCode 1.19.0",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": null,
    "phase": "sample",
    "note": "180-second timeout without answer; temporary source commit bac47cb2d2ba2041ad19c80edba99f94fb597d4a; selected model matches endpoint inventory, runtime model unreported.",
    "order": 1
  },
  {
    "scenario": "context-complete-inventory",
    "date": "2026-10-11",
    "skill_commit": null,
    "runner": "OpenCode 1.19.0",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": null,
    "phase": "sample",
    "note": "180-second timeout without answer; temporary source commit bac47cb2d2ba2041ad19c80edba99f94fb597d4a; selected model matches endpoint inventory, runtime model unreported.",
    "order": 1
  },
  {
    "scenario": "draft-pr-ready-transition",
    "date": "2026-10-11",
    "skill_commit": null,
    "runner": "OpenCode 1.19.0",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": null,
    "phase": "sample",
    "note": "180-second timeout without answer; temporary source commit bac47cb2d2ba2041ad19c80edba99f94fb597d4a; selected model matches endpoint inventory, runtime model unreported.",
    "order": 1
  }
]
```
