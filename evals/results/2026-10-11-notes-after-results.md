# Notes after results decision samples, 2026-10-11

One new scenario for the notes-after-results rule ran on Claude Sonnet through the Claude Code runner, two samples against the changed text and one against the old text. Two related scenarios ran once as regression checks. Every sample passed, including the baseline. The local model was not used, per [issue #65](https://github.com/lmorchard/ghflow/issues/65). The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-11-notes-after-results-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `a7b14c3a4a1bd08fb6d0cb8aa6793d52e88a4d7d` on branch `notes-after-results`. The baseline commit is `5871c16c8d84484b10ac26f91a8211ae402dce3f` on the local scratch branch `baseline-notes-after-results`. It holds the skill text of main at `969fdf0` plus the new scenario file, because the runner reads the scenario from the selected commit. It is not for merge.

Each batch used this command form through `/tmp/ceremony-runs/run-batch.sh`, one output directory per scenario:

```sh
python3 scripts/run_scenario.py SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit COMMIT --repeat REPEAT --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was Claude Code `2.1.296` with the isolation controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records. Every run reported runtime model `claude-sonnet-5-5`, exited 0, and returned no diagnostic. The skill change author was Claude Fable 5.1 in a Claude Code session. Les approved these runs on 2026-10-11. Raw provenance and answers remain under `/tmp/ceremony-runs/nr-*`.

## Results

Grades use the criteria at commit `a7b14c3` for every phase.

| Scenario | Phase | Session | Runtime model | Time | Grade |
| --- | --- | --- | --- | --- | --- |
| notes-result-before-run | baseline | `ca7dbf60-f3a4-4c8c-88cc-9d253afcdd03` | claude-sonnet-5-5 | 10 s | Pass |
| notes-result-before-run | changed | `1eb64169-337a-4772-9a19-086f9b6c6e2d` | claude-sonnet-5-5 | 10 s | Pass |
| notes-result-before-run | changed | `9fc2fb30-2b0b-4427-b6a7-fcf582937569` | claude-sonnet-5-5 | 10 s | Pass |
| reuse-revision-evidence | regression | `cb6e0385-d8f8-402a-892d-1beaeafb4f47` | claude-sonnet-5-5 | 13 s | Pass |
| task-notes-changed-evidence | regression | `7455e0ef-846d-420f-ad0c-a1784001bd8d` | claude-sonnet-5-5 | 11 s | Pass |

### Sonnet

The baseline passed on the old text. It reached the decision through the Task notes sentence that the `Resume here` summary holds the latest checks and their revisions, through the Evidence rule that a report must match what happened, and through the implement-issue sentence from PR #66 that behavior is verified only when a command showed it.

Both changed-text answers passed and quoted the new Task notes sentences as the deciding rule: update the checks and status after the commands run, and write an unperformed step as the next action. Each wrote the true current state, listed the gates as next actions, and said the summary would say done only after each command ran. Each also kept the push conditional on the handoff's submit-pr authorization.

Both regression answers passed and kept their reuse and recheck decisions under the Evidence rule.

## Limits

The scenario does not discriminate old from new text on Sonnet. The baseline passed because the existing notes and evidence sentences, plus the PR #66 verified-by-command rule, already implied the decision. The trial worker that wrote results before running them was a local model, and whether the new text changes its behavior is untested until issue #65 is resolved. One baseline and two changed samples are samples, not proof.

```scenario-results
[
  {
    "scenario": "notes-result-before-run",
    "date": "2026-10-12",
    "skill_commit": "5871c16",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "notes-result-before-run",
    "date": "2026-10-12",
    "skill_commit": "a7b14c3",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "reuse-revision-evidence",
    "date": "2026-10-12",
    "skill_commit": "a7b14c3",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "task-notes-changed-evidence",
    "date": "2026-10-12",
    "skill_commit": "a7b14c3",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  }
]
```
