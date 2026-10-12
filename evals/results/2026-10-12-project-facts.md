# Project facts decision samples, 2026-10-12

Three new scenarios cover the `facts` command and the prepare-project-facts task. The handoff scenario ran on Claude Sonnet once against the old text with the new criteria and twice against the changed text. The two scenarios that select the new task ran twice against the changed text; they have no baseline, because the runner refuses a snapshot without the task file. Three related scenarios ran once as regression checks. Every sample passed, including the one baseline. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-project-facts-answers.txt) preserve the output used for grading. The source is the issue #1054 delivery record in [PR #74](https://github.com/lmorchard/ghflow/pull/74): both workers rediscovered the fixture layout and the generated files, and the coordinator spent 15 minutes composing a handoff that restated the project's setup.

## Source and method

The changed source commit is `9a42fa0d001e66af1ccad8ba40bd4cca6d5715bf` on branch `project-facts`. The baseline commit is `f9d5ef6` on the local scratch branch `baseline-project-facts`, which holds the skill text of main at `6cc6f46` plus the three new scenario files. It is not for merge.

Runs used the Claude Code runner `2.1.296` with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records: restricted read-only file tools confined to the source snapshot, no command, web, MCP, or agent tools, and a minimal environment without identity or GitHub variables. The selected model was `claude-sonnet-5-5`, and every run reported that runtime model. The author of the change is Claude Fable 5.1. Runs took 7 to 16 seconds.

## Results

Grades use the criteria at commit `9a42fa0` for both phases.

| Scenario | Phase | Commit | Session | Seconds | Grade |
| --- | --- | --- | --- | ---: | --- |
| handoff-points-to-project-facts | old text | `f9d5ef6` | `9dad29f4-82ed-41dc-aba0-e50d46aef129` | 13 | Pass |
| handoff-points-to-project-facts | new text | `9a42fa0` | `2c8a012a-170b-41aa-b38d-38e2e89a6ada` | 15 | Pass |
| handoff-points-to-project-facts | new text | `9a42fa0` | `914bff72-bbeb-41e4-910f-e29e0a952583` | 14 | Pass |
| project-facts-stale-source | new text | `9a42fa0` | `3d5657e7-175a-46c6-82d0-385a461e17b1` | 16 | Pass |
| project-facts-stale-source | new text | `9a42fa0` | `3ac3ffc4-c8fc-4181-9cd1-67679af1154f` | 13 | Pass |
| project-facts-live-state | new text | `9a42fa0` | `8c71ac76-2fc0-4316-b46a-c10d75ac1fda` | 8 | Pass |
| project-facts-live-state | new text | `9a42fa0` | `294b72c1-2b98-4980-ad20-078582633d3d` | 7 | Pass |
| coordinator-ready-to-dispatch | regression | `9a42fa0` | `557c76d8-5477-4848-a32a-32a45ec2513d` | 12 | Pass |
| context-read-selected-task | regression | `9a42fa0` | `aed3dad7-f415-409b-8499-2501d7cb1e2c` | 13 | Pass |
| implementation-handoff-operation-scope | regression | `9a42fa0` | `ca7f4d5f-d99a-4a51-b2be-18d6f9e65f97` | 14 | Pass |

The old-text handoff answer pointed the worker to the facts file from the existing "link instead of copying" rule and added only the facts the worker could not recover. Both new-text answers quoted the new Handoffs sentence and the `Project facts:` line of the template, and one named a task-specific fact it would keep. Both stale-source answers continued the delivery, told the worker to confirm the gates against the current Makefile, offered a separate refresh, and refused to edit the file inside the delivery. Both live-state answers left the head, PRs, board status, and identity out, kept the source hashes, and ended the file with the `facts` command. The regression answer for `coordinator-ready-to-dispatch` added the facts pointer to its handoff unprompted.

## Limits

The handoff scenario does not discriminate old from new text on Sonnet, which matches every earlier rule change: Sonnet reaches the decision from the general rules, and the new sentence names it. The two task scenarios have no baseline by construction. No sample ran on the local Qwen model. No real project has a facts file yet; the live `facts` output was checked by hand against the decafclaw checkout, and the task has not been run by a worker. The grades are the author's.

## Checks

`make check` passed: the CLI tests including the `facts` tests, the script tests, source and link checks, scenario-index validation, and whitespace checks.

```scenario-results
[
  {"scenario": "handoff-points-to-project-facts", "date": "2026-10-12", "skill_commit": "f9d5ef6", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "old text", "note": "Scratch baseline: main text with the new criteria; decided from the existing link-instead-of-copy rule.", "order": 1},
  {"scenario": "handoff-points-to-project-facts", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "project-facts-stale-source", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": "No baseline: the task file does not exist at the baseline commit.", "order": null},
  {"scenario": "project-facts-live-state", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": "No baseline: the task file does not exist at the baseline commit.", "order": null},
  {"scenario": "coordinator-ready-to-dispatch", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "context-read-selected-task", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "implementation-handoff-operation-scope", "date": "2026-10-12", "skill_commit": "9a42fa0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
