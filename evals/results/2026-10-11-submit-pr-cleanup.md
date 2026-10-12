# Submit-pr cleanup decision samples, 2026-10-11

Four new scenarios for the submit-pr cleanup ran on Claude Sonnet through the Claude Code runner, two samples each against the changed text and one each against the old text. Six related submit-pr and board scenarios ran once as regression checks. Every sample passed, including all four baselines. The local model was not used, per [issue #65](https://github.com/lmorchard/ghflow/issues/65). The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-11-submit-pr-cleanup-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `abe744ef7b983e97b16f56eea19d0ffc22236fa2` on branch `submit-pr-cleanup`. The baseline commit is `7eab79c2a74c105f22b284fb1534bc6cf2236126` on the local scratch branch `baseline-submit-pr`. It holds the skill text of main at `dfdca69` plus the four new scenario files, because the runner reads the scenario from the selected commit. It is not for merge.

Each batch used this command form through `/tmp/ceremony-runs/run-batch.sh`, one output directory per scenario:

```sh
python3 scripts/run_scenario.py SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit COMMIT --repeat REPEAT --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was Claude Code `2.1.296` with the isolation controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records. Every run reported runtime model `claude-sonnet-5-5`, exited 0, and returned no diagnostic. The skill change author was Claude Fable 5.1 in a Claude Code session. Les approved these runs on 2026-10-11. Raw provenance and answers remain under `/tmp/ceremony-runs/sp-*`.

## Results

Grades use the criteria at commit `abe744e` for every phase.

| Scenario | Phase | Session | Runtime model | Time | Grade |
| --- | --- | --- | --- | --- | --- |
| board-status-no-pre-read | baseline | `5d37c313-c785-4244-839c-8407073b3034` | claude-sonnet-5-5 | 9 s | Pass |
| submit-pr-resume-ready-readback | baseline | `9f37f27b-f009-496e-9c4c-34dd82118d82` | claude-sonnet-5-5 | 11 s | Pass |
| submit-pr-unread-finding-text | baseline | `f0d922b8-f2c2-450f-9ad3-0655c90fc74f` | claude-sonnet-5-5 | 11 s | Pass |
| submit-pr-write-identity | baseline | `92fb0a8b-22ff-4de2-8b4d-9dfa0e12cf01` | claude-sonnet-5-5 | 13 s | Pass |
| board-status-no-pre-read | changed | `01bde271-5df0-4098-95e4-09460acb146e` | claude-sonnet-5-5 | 9 s | Pass |
| board-status-no-pre-read | changed | `133d7941-a3f5-49d1-be74-045bdb5e704d` | claude-sonnet-5-5 | 9 s | Pass |
| submit-pr-resume-ready-readback | changed | `4cb7d482-1572-41bd-b5c1-06ec801e194e` | claude-sonnet-5-5 | 8 s | Pass |
| submit-pr-resume-ready-readback | changed | `24fff7e1-b058-4c76-83e9-1659c08fb154` | claude-sonnet-5-5 | 8 s | Pass |
| submit-pr-unread-finding-text | changed | `8c8c632c-0108-488b-9137-db9d75549dc8` | claude-sonnet-5-5 | 7 s | Pass |
| submit-pr-unread-finding-text | changed | `4bb5be1f-41a8-4c78-9ccc-83b54fb35ea4` | claude-sonnet-5-5 | 8 s | Pass |
| submit-pr-write-identity | changed | `e5aa66e6-c63b-4cda-8213-bdd37c7e1f25` | claude-sonnet-5-5 | 10 s | Pass |
| submit-pr-write-identity | changed | `a40de7d0-00cc-4210-ac88-d227054d839d` | claude-sonnet-5-5 | 10 s | Pass |
| board-transition-cli | regression | `46e83c0b-57a1-4b8f-80f4-20fca818efdb` | claude-sonnet-5-5 | 10 s | Pass |
| delivery-early-draft | regression | `ee10b811-ec55-41a7-8755-b934062e2ce2` | claude-sonnet-5-5 | 14 s | Pass |
| draft-pr-ready-transition | regression | `1c4be409-521b-4290-bb2f-c9ab1fba5ea3` | claude-sonnet-5-5 | 9 s | Pass |
| dry-run-pushes | regression | `6f50c898-a672-4eba-a988-b9cde3baebcc` | claude-sonnet-5-5 | 7 s | Pass |
| submit-pr-no-default-copilot | regression | `ee652b8b-ca91-41db-876c-b5c036889466` | claude-sonnet-5-5 | 8 s | Pass |
| submit-pr-sandbox-auth-context | regression | `2c9b4ec9-8689-47d8-af4a-5d1d88074c29` | claude-sonnet-5-5 | 11 s | Pass |

### Baselines against the old text

All four passed. `board-status-no-pre-read` reached the decision from the board-status procedure, which already said the tool reports `before`. `submit-pr-write-identity` gated the write on `gh api user` under the identity rules, and said it would still run `gh auth status` as the old submit-pr text required and read it as diagnostic only. `submit-pr-unread-finding-text` reached the decision through the task-notes and Evidence rules on reading notes before resuming. `submit-pr-resume-ready-readback` reached it through the GitHub writes rules on reading before an update and reading back after each write, and noted that a chained command hides which step failed.

### Changed text

All eight answers passed and cited the new submit-pr sentences as the deciding rule: the `before` sentence under "Mark the issue in review", "The active account in `gh auth status` does not establish the write identity", "State only facts that you read or ran", and the separate-command rule for readiness with its resumption paragraph. Each `submit-pr-write-identity` answer also walked the new publish sequence with both `verify-commit` forms. Each `submit-pr-unread-finding-text` answer named the gap report as the alternative to reading the source.

### Regression

All six passed. `draft-pr-ready-transition` and `delivery-early-draft` kept their express-issue decisions and picked up the new body and read-back details. `submit-pr-sandbox-auth-context` kept the sandbox rule from Agent identity and added the `gh api user` gate. `dry-run-pushes` kept the prohibition and used the new body file location. `board-transition-cli` added that it would not query the board first.

## Limits

The scenarios do not discriminate old from new text on Sonnet. All four baselines passed because the shared rules on identity, task notes, evidence, and GitHub writes already supplied the decision; the change moves those triggers into submit-pr and names the commands. The trial worker that spent four turns on GraphQL and chained the ready change was a local model, and whether the new text changes that model's behavior is untested until issue #65 is resolved. One run per baseline and two per changed scenario are samples, not proof.

```scenario-results
[
  {
    "scenario": "board-status-no-pre-read",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "submit-pr-resume-ready-readback",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "submit-pr-unread-finding-text",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "submit-pr-write-identity",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "board-status-no-pre-read",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submit-pr-resume-ready-readback",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submit-pr-unread-finding-text",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submit-pr-write-identity",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "board-transition-cli",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "delivery-early-draft",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "draft-pr-ready-transition",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "dry-run-pushes",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submit-pr-no-default-copilot",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submit-pr-sandbox-auth-context",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  }
]
```
