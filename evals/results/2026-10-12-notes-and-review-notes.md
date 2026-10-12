# Notes after ready and reviewer notes decision samples, 2026-10-12

Two changes from the [issue #1053 delivery record](../../docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md): no notes-only commit before or after the PR is marked ready, and reviewer notes separated from findings so the coordinator settles them without the user. One scenario was updated and two were added. Each ran on Claude Sonnet once against the old text with the new criteria and twice against the changed text; five related scenarios ran once as regression checks. Two of three baselines failed as intended, and every changed-text and regression sample passed. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-notes-and-review-notes-answers.txt) preserve the output used for grading.

## Source and method

The changed source commit is `de884ff6641ae33988766dafa8fca487f5b7849e` on branch `trial-1053-followups`. The baseline commit is `fde3ed5` on the local scratch branch `baseline-1053-followups`, which holds the skill text of main at `b7d51bb` plus the three scenario files. It is not for merge.

Runs used the Claude Code runner `2.1.296` with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. The author of the change is Claude Fable 5.1. Runs took 7 to 16 seconds.

## Results

Grades use the criteria at commit `de884ff` for both phases.

| Scenario | Phase | Commit | Session | Seconds | Grade |
| --- | --- | --- | --- | ---: | --- |
| notes-commit-after-review | old text | `fde3ed5` | `40a28fc0-182c-4ad8-869b-b8854761e05c` | 12 | Fail |
| notes-commit-after-review | new text | `de884ff` | `86c08a70-26b6-4333-833a-e5c85e34962a` | 11 | Pass |
| notes-commit-after-review | new text | `de884ff` | `d05b7b1d-b610-4dbc-92d2-149b4d946cae` | 13 | Pass |
| review-note-not-finding | old text | `fde3ed5` | `f79bf742-4018-49c5-bf5a-fbd553bdecbe` | 16 | Fail |
| review-note-not-finding | new text | `de884ff` | `7a7453e2-6269-40e8-b637-1910a2f43834` | 14 | Pass |
| review-note-not-finding | new text | `de884ff` | `6816f0ce-8125-4a46-bb13-e0f44293ea20` | 10 | Pass |
| coordinator-settles-review-notes | old text | `fde3ed5` | `2729a955-4f5c-4b7c-9013-4eccffc1e820` | 9 | Pass |
| coordinator-settles-review-notes | new text | `de884ff` | `68bc467c-a592-461f-8cf1-15affccf8246` | 8 | Pass |
| coordinator-settles-review-notes | new text | `de884ff` | `6054d974-d620-4d93-bd32-f3905d722bb3` | 8 | Pass |
| draft-pr-ready-transition | regression | `de884ff` | `9aa642ef-e881-4d2d-b6f9-293ecee43c15` | 9 | Pass |
| submit-pr-resume-ready-readback | regression | `de884ff` | `81c28e53-850e-4f04-a9a5-f71e9a260530` | 10 | Pass |
| express-complete-return | regression | `de884ff` | `57f1697a-334a-4496-a2bb-5fa844a89441` | 13 | Pass |
| review-comments-unread | regression | `de884ff` | `feb2864a-9bb6-4267-9283-3ce4a8f0ae0e` | 7 | Pass |
| corrections-same-worker | regression | `de884ff` | `482bec75-1670-43e9-8833-77918db9e0f4` | 8 | Pass |

The old-text notes answer refused the commit before ready and then planned one notes-only commit after ready with a CI wait, which the old sentence allowed and the new criteria forbid. Both new-text answers kept the notes uncommitted, ran `pr ready` on the reviewed head, and named the reopened follow-up as the reason. The old-text reviewer answer labeled the backticked closing reference a low-severity finding, which is now a note; both new-text answers listed the two notes separately with suggestions, kept the annotation as a finding with file, line, trigger, and impact, and said notes go to the coordinator. The old-text coordinator answer already passed everything to the worker without asking the user, from the existing correction rule; both new-text answers quoted the new sentence and gave a reason for each note. The regression answers kept their decisions, and three of them volunteered the new rule: no notes-only commit, and settling notes as routine.

## Limits

The coordinator scenario does not discriminate on Sonnet. The real-run behavior it targets, a Qwen coordinator reading Decisions and still asking the user, did not appear in a Sonnet sample on either text; the next local-model delivery is the test. One old-text sample per scenario. The grades are the author's.

## Checks

`make check` passed: the CLI and script tests, source and link checks, scenario-index validation, and whitespace checks.

```scenario-results
[
  {"scenario": "notes-commit-after-review", "date": "2026-10-12", "skill_commit": "fde3ed5", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Fail", "phase": "old text", "note": "Scratch baseline: main text with the updated criteria; planned a notes-only commit after ready.", "order": 1},
  {"scenario": "notes-commit-after-review", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "review-note-not-finding", "date": "2026-10-12", "skill_commit": "fde3ed5", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Fail", "phase": "old text", "note": "Scratch baseline: labeled the description wording a finding.", "order": 1},
  {"scenario": "review-note-not-finding", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "coordinator-settles-review-notes", "date": "2026-10-12", "skill_commit": "fde3ed5", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "old text", "note": "Scratch baseline: decided from the existing correction rule.", "order": 1},
  {"scenario": "coordinator-settles-review-notes", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "draft-pr-ready-transition", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "submit-pr-resume-ready-readback", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "express-complete-return", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "review-comments-unread", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "corrections-same-worker", "date": "2026-10-12", "skill_commit": "de884ff", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
