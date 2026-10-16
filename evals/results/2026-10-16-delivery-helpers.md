# Delivery helper commands, decision samples, 2026-10-16

`worktree create`, `pr body`, and `handoff` move rule-following work out of the local model's output, based on the token counts in the [fourth burndown](../../docs/research/trials/2026-10-15-unattended-burndown-4.md). The coordinator now dispatches with a one-line prompt that names a handoff file. One new scenario checks that a worker treats such a prompt as complete, and one regression checks that a real placeholder still gets the one-line reply. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-16-delivery-helpers-answers.txt) preserve the graded output.

## Source and method

The changed commit is `428269a` on branch `cli-delivery-tools`, stacked on #118. The baseline commit is `4dafadb` on the local scratch branch `baseline-cli-delivery`, which holds the #118 branch plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| worker-handoff-file-prompt | old text | claude-sonnet-5-5 | `4dafadb` | `6f47af82-f103-4fba-85a3-1d27228130f3` | Pass |
| worker-handoff-file-prompt | new text | claude-sonnet-5-5 | `428269a` | `628872a9-0afc-4ed8-9d41-699c9f1b16ff` | Pass |
| worker-handoff-file-prompt | new text | claude-sonnet-5-5 | `428269a` | `7c546afd-7bd4-416f-b0b5-8bf41597bf4b` | Pass |
| worker-placeholder-prompt | regression | claude-sonnet-5-5 | `428269a` | `eccbef66-af4e-48cd-ab47-abd059576b4c` | Pass |

Every answer treated the short prompt as a complete handoff and tried to read the named file. The runner allows reads only inside the source snapshot, so each answer stopped and asked for access to the file, which is the right response to an unreadable handoff. The baseline did the same, so the scenario does not separate old text from new on Sonnet; it guards the new rule. The placeholder regression still returned the one-line request.

## Limits

The commands have unit tests against temporary Git repositories and fakes. `handoff` and `pr body` ran live, read-only, against decafclaw issue #929 and PR #1079. `worktree create` did not run live against the subject repository. The token savings are estimates until the next run measures them. The grades are the author's.

## Checks

`make check` passed on `428269a`.

```scenario-results
[
 {
  "scenario": "worker-handoff-file-prompt",
  "date": "2026-10-16",
  "skill_commit": "4dafadb",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "Treated the prompt as complete without the rule.",
  "order": 1
 },
 {
  "scenario": "worker-handoff-file-prompt",
  "date": "2026-10-16",
  "skill_commit": "428269a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "worker-placeholder-prompt",
  "date": "2026-10-16",
  "skill_commit": "428269a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
