# Test assertion specificity decision samples, 2026-10-11

Two new scenarios for the test assertion rule ran on Claude Sonnet through the Claude Code runner, two samples each against the changed text and one each against the old text. Two implement-issue scenarios ran once as regression checks. Every Sonnet sample passed, including both baselines. The implementer scenario also ran once per text on the local Qwen model that produced the trial; both local runs ended without an answer and remain ungraded. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-11-test-assertion-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `5fd11e0f43879f778f7d4a138656b5867e59c975` on branch `test-assertion-specificity`. The baseline commit is `30b1945aa0824b1970d9032efb4707ed18b5e236` on the local scratch branch `baseline-test-assertion`. It holds the skill text of `7f25349`, the head of PR #63, plus the two new scenario files, because the runner reads the scenario from the selected commit. It is not for merge.

Sonnet batches used this command form through `/tmp/ceremony-runs/run-batch.sh`, one output directory per scenario:

```sh
python3 scripts/run_scenario.py SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit COMMIT --repeat REPEAT --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was Claude Code `2.1.296` with the isolation controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records. Every Sonnet run reported runtime model `claude-sonnet-5-5`, exited 0, and returned no diagnostic. The skill change author was Claude Fable 5.1 in a Claude Code session.

The local runs used OpenCode through `--runner opencode`, endpoint `http://127.0.0.1:9931/v1`, model `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M`, context window 65536, and a 900-second timeout, one at a time. The endpoint advertised only that model before each run. OpenCode does not report provider model identity in its events, so the runtime model is recorded as unknown. Les approved these runs on 2026-10-11. Raw provenance and answers remain under `/tmp/ceremony-runs/ta-*`.

## Results

Grades use the criteria at commit `5fd11e0` for every phase.

| Scenario | Phase | Session | Selected or runtime model | Time | Grade |
| --- | --- | --- | --- | --- | --- |
| new-test-passes-on-old-text | baseline | `5a3e7999-68d0-4f44-a4b1-e3a1ba912fc2` | claude-sonnet-5-5 | 11 s | Pass |
| review-new-test-nearby-substitute | baseline | `5603fc45-d280-4c27-bd28-0e06bb506376` | claude-sonnet-5-5 | 18 s | Pass |
| new-test-passes-on-old-text | changed | `263bd1bf-f1d0-4f94-b73a-591ea29ec911` | claude-sonnet-5-5 | 8 s | Pass |
| new-test-passes-on-old-text | changed | `96765125-796f-4cee-9014-044c4f95db2a` | claude-sonnet-5-5 | 8 s | Pass |
| review-new-test-nearby-substitute | changed | `f3aef4af-3092-4d87-9913-9bd1bfb1aa8d` | claude-sonnet-5-5 | 12 s | Pass |
| review-new-test-nearby-substitute | changed | `b5feb06f-6d4e-4100-b110-d8783f46c434` | claude-sonnet-5-5 | 13 s | Pass |
| new-test-passes-on-old-text | localbaseline | `ses_ed2b454a8ffeUjNIlYnIgx2PcC` | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | 210 s | No answer, ungraded |
| new-test-passes-on-old-text | localchanged | `ses_ed2b11ab1ffe3ucDIwueOPMvNB` | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | 211 s | No answer, ungraded |
| implementation-local-only | regression | `221b19c8-5cd5-4f63-8bef-1040c32cad5a` | claude-sonnet-5-5 | 8 s | Pass |
| subagent-has-question | regression | `881b1412-a449-4293-ba64-2773cc55c010` | claude-sonnet-5-5 | 10 s | Pass |

### Sonnet

Both baselines passed on the old text. The implementer answer reached the decision through the self-review sentence "check that changed tests still establish the intended behavior", and the reviewer answer through "Examine tests before you accept their stated coverage" and the nearby-substitute question. Each identified that "whitespace" is in the pre-change error and that tier 2 also produces "line 1". The baseline implementer answer proposed running the test with tier 1 disabled "or reason from the code"; the new text makes that check required.

All four changed-text answers passed and cited the new paragraph in implement-issue or the extended question in review-changes as the deciding rule. Each named the disabled-behavior check as the first step and kept the implementation checkout unchanged in the reviewer case.

Both regression answers passed. The `implementation-local-only` answer restated the new assertion rule in its plan without reading it as permission to publish.

### Local model

Both local runs completed two steps, read `references/tasks/implement-issue.md` once, emitted about 4,200 output tokens, and exited with status 1 after about 210 seconds without an answer or a diagnostic. The timeout did not fire. These runs establish neither a decision nor a failure to decide. The [earlier local samples](2026-10-11-local-context.md) timed out the same way at 180 seconds. The local runner path needs separate investigation before it can supply decision evidence.

## Limits

The scenarios do not discriminate old from new text on Sonnet. Both baselines passed, so the rule did not change Sonnet's decision when the scenario states the facts plainly. The trial failure happened on a local model that had the same facts in view and did not act on them. Whether the new text changes that model's behavior is untested, because the local runs produced no answers. One run per baseline and two per changed scenario are samples, not proof. Decision scenarios do not establish that an implementation worker runs the disabled-behavior check on a real issue.

```scenario-results
[
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-11",
    "skill_commit": "30b1945",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-11",
    "skill_commit": "30b1945",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-11",
    "skill_commit": "5fd11e0",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-11",
    "skill_commit": "5fd11e0",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-11",
    "skill_commit": "30b1945",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": null,
    "phase": "localbaseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-11",
    "skill_commit": "5fd11e0",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": null,
    "phase": "localchanged",
    "note": null,
    "order": 2
  },
  {
    "scenario": "implementation-local-only",
    "date": "2026-10-11",
    "skill_commit": "5fd11e0",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "subagent-has-question",
    "date": "2026-10-11",
    "skill_commit": "5fd11e0",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  }
]
```
