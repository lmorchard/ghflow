# Clock-read times, local notes edits, and a started ready step, decision samples, 2026-10-14

Three small rules come from the [second burndown record](../../docs/research/trials/2026-10-14-unattended-burndown-2.md). The summary claimed an end time that no clock command read. A worker amended and force-pushed three times for notes edits. The last ready step finished a few minutes after the deadline, which the old rule did not cover. Each scenario ran on Claude Sonnet once against the old text and twice against the new text, and two regressions ran once. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-small-rules-answers.txt) preserve the graded output.

## Source and method

The changed commit is `aaa4d7a` on branch `small-rules-b2`. The baseline commit is `0c71ce0` on the local scratch branch `baseline-small-rules-b2`, which holds main plus the scenarios. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| summary-time-from-clock | old text | claude-sonnet-5-5 | `0c71ce0` | `1cc8b0fa-7956-4389-8cd9-d79cd3cd37af` | Pass |
| summary-time-from-clock | new text | claude-sonnet-5-5 | `aaa4d7a` | `055f28ef-f785-4ccb-8dcc-675765bbab67` | Pass |
| summary-time-from-clock | new text | claude-sonnet-5-5 | `aaa4d7a` | `73067a37-1c6c-44d9-9ac4-0972af721469` | Pass |
| notes-edit-without-amend | old text | claude-sonnet-5-5 | `0c71ce0` | `92a8e530-4c65-42c5-8d98-dfe962e7f724` | Partial |
| notes-edit-without-amend | new text | claude-sonnet-5-5 | `aaa4d7a` | `344c99c5-7675-4979-8b22-92f3c82ff7a6` | Pass |
| notes-edit-without-amend | new text | claude-sonnet-5-5 | `aaa4d7a` | `3713ec55-d42b-46d3-bf13-f855b28d141a` | Pass |
| deadline-ready-step-finishes | old text | claude-sonnet-5-5 | `0c71ce0` | `2c5a6dec-e338-4d0d-a2f6-4d61a9b17248` | Fail |
| deadline-ready-step-finishes | new text | claude-sonnet-5-5 | `aaa4d7a` | `13adf989-370a-4694-973e-e32acca48a0e` | Pass |
| deadline-ready-step-finishes | new text | claude-sonnet-5-5 | `aaa4d7a` | `220a4621-2456-40b9-80f3-a43eb7919319` | Pass |
| notes-commit-after-review | regression | claude-sonnet-5-5 | `aaa4d7a` | `2f65a32b-b2c6-464a-bf0c-8b104dc08f9a` | Pass |
| deadline-declines-optional-notes | regression | claude-sonnet-5-5 | `aaa4d7a` | `9048ea83-69b8-43fb-924e-06d6f19ada49` | Pass |

Sonnet reads the clock on the old text too, so that scenario does not discriminate on Sonnet; the failure was on the local model. On the old text, the notes answer kept the head unchanged but dropped the notes update into the report. On the old text, the deadline answer parked the issue while its ready step was under way. All new-text answers kept the notes edit local without amending, let the started ready step finish, and dispatched nothing new.

## Limits

No Qwen sample ran. The grades are the author's.

## Checks

`make check` passed on `aaa4d7a`.

```scenario-results
[
 {
  "scenario": "summary-time-from-clock",
  "date": "2026-10-14",
  "skill_commit": "0c71ce0",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "Sonnet reads the clock without the rule.",
  "order": 1
 },
 {
  "scenario": "summary-time-from-clock",
  "date": "2026-10-14",
  "skill_commit": "aaa4d7a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "notes-edit-without-amend",
  "date": "2026-10-14",
  "skill_commit": "0c71ce0",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Dropped the notes update into the report.",
  "order": 1
 },
 {
  "scenario": "notes-edit-without-amend",
  "date": "2026-10-14",
  "skill_commit": "aaa4d7a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-14",
  "skill_commit": "0c71ce0",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Parked the issue while its ready step was under way.",
  "order": 1
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-14",
  "skill_commit": "aaa4d7a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "notes-commit-after-review",
  "date": "2026-10-14",
  "skill_commit": "aaa4d7a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "deadline-declines-optional-notes",
  "date": "2026-10-14",
  "skill_commit": "aaa4d7a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
