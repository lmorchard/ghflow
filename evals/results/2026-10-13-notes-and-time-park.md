# Coordinator notes location and time-park resume, decision samples, 2026-10-13

Two new scenarios cover two small changes from the [unattended burndown record](../../docs/research/trials/2026-10-13-unattended-burndown.md). The queue coordinator wrote its notes as an untracked directory in the main checkout. A time-budget park has no question, so nothing said who restores `triage:ready`. Each scenario ran on Claude Sonnet once against the old text and twice against the new text. Two related scenarios ran once as regression checks. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-13-notes-and-time-park-answers.txt) preserve the graded output.

## Source and method

The changed commit is `f5f565b` on branch `small-fixes-c`. The baseline commit is `decafa2` on the local scratch branch `baseline-small-fixes-c`, which holds main at `acbaeb1` plus the two scenarios. It is not for merge. The model was `claude-sonnet-5-5` under the Claude Code runner with the controls that earlier results record.

## Results

| Scenario | Phase | Commit | Session | Grade |
| --- | --- | --- | --- | --- |
| coordinator-notes-outside-checkout | old text | `decafa2` | `959e1e0b-cfb1-4191-9499-946fc47e6e05` | Fail |
| coordinator-notes-outside-checkout | new text | `f5f565b` | `b8836980-915c-491f-b7f0-9612178c45e0` | Pass |
| coordinator-notes-outside-checkout | new text | `f5f565b` | `33c811f7-059b-4184-97d1-be6c3a9546ed` | Pass |
| resume-time-parked-issue | old text | `decafa2` | `79733cf8-0535-42d6-b89c-30d0dfd0b1aa` | Partial |
| resume-time-parked-issue | new text | `f5f565b` | `88dfd28e-655f-4c87-a3a2-ea6394472f4d` | Pass |
| resume-time-parked-issue | new text | `f5f565b` | `f0f5bb7e-e7c4-4086-982b-b754720866c8` | Pass |
| unattended-parks-on-uncertainty | regression | `f5f565b` | `2b04d8e8-24bd-422f-8973-2c4ed0d52535` | Pass |
| notes-commit-after-review | regression | `f5f565b` | `4926ec6f-1461-4302-b110-b5f925099364` | Pass |

The old-text notes answer created a coordinator worktree only to hold notes, which the scenario does not accept. Both new answers used the state directory and kept worker notes in the worktrees. The old-text resume answer resumed from the PR correctly and noticed the stale label, but left it as "housekeeping" with no timing or owner. Both new answers restored `triage:ready` before the first dispatch and did not route the issue through sweep-needs-input.

## Limits

No sample ran on the local Qwen model. The state directory name is the author's choice. The grades are the author's.

```scenario-results
[
  {"scenario": "coordinator-notes-outside-checkout", "date": "2026-10-13", "skill_commit": "decafa2", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Fail", "phase": "old text", "note": "Created a coordinator worktree to hold notes.", "order": 1},
  {"scenario": "coordinator-notes-outside-checkout", "date": "2026-10-13", "skill_commit": "f5f565b", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "resume-time-parked-issue", "date": "2026-10-13", "skill_commit": "decafa2", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Partial", "phase": "old text", "note": "Noticed the stale label but gave it no timing or owner.", "order": 1},
  {"scenario": "resume-time-parked-issue", "date": "2026-10-13", "skill_commit": "f5f565b", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "unattended-parks-on-uncertainty", "date": "2026-10-13", "skill_commit": "f5f565b", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "notes-commit-after-review", "date": "2026-10-13", "skill_commit": "f5f565b", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
