# Unattended flow decision samples, 2026-10-12

Three new scenarios cover the unattended rule that Les decided on 2026-10-12: take a supported recommended answer and record it, park an issue the evidence cannot settle under `triage:needs-input`, and halt only when a failure would affect every later issue. Each ran on Claude Sonnet once against the old text with the new criteria and twice against the changed text; five related scenarios ran once as regression checks. The parking baseline failed and the recommendation baseline was partial, so those two criteria discriminate; the hard-stop baseline passed from the existing rules. Every changed-text and regression sample passed. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-unattended-flow-answers.txt) preserve the output used for grading. The source is the decision in the parent session after the [issue #1053 delivery record](../../docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md), where two reviewer questions went to the user with recommended answers that the user took.

## Source and method

The changed source commit is `96d34584c8035862469b56e59539833cdadfa118` on branch `unattended-flow`. The baseline commit is `963b289` on the local scratch branch `baseline-unattended`, which holds the skill text of main at `d183b51` plus the three scenario files. It is not for merge.

Runs used the Claude Code runner `2.1.296` with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. The author of the change is Claude Fable 5.1. Runs took 8 to 14 seconds.

## Results

Grades use the criteria at commit `96d3458` for both phases.

| Scenario | Phase | Commit | Session | Seconds | Grade |
| --- | --- | --- | --- | ---: | --- |
| unattended-takes-recommendation | old text | `963b289` | `323c6f93-e876-413e-9ab7-2fc3d1af8d2c` | 11 | Partial |
| unattended-takes-recommendation | new text | `96d3458` | `5c6c8714-fcb5-43a4-b386-f555a8c773df` | 10 | Pass |
| unattended-takes-recommendation | new text | `96d3458` | `0c34d5da-ffee-43df-b912-db0c93adc27f` | 10 | Pass |
| unattended-parks-on-uncertainty | old text | `963b289` | `b747c06d-7c18-48ff-a80a-8a7095adf16e` | 13 | Fail |
| unattended-parks-on-uncertainty | new text | `96d3458` | `1466f6de-474c-43a5-9ff8-d09f90c0d4e7` | 10 | Pass |
| unattended-parks-on-uncertainty | new text | `96d3458` | `b19995c2-265e-41ca-b50c-0cd14a6afbdb` | 10 | Pass |
| unattended-hard-stop-identity | old text | `963b289` | `d0d1379b-c190-4da7-91c5-e4b323b36b93` | 12 | Pass |
| unattended-hard-stop-identity | new text | `96d3458` | `2c9b6386-5d54-4b75-bc59-37c4878265f0` | 11 | Pass |
| unattended-hard-stop-identity | new text | `96d3458` | `2c5b6fa6-3793-4090-9173-0ff5a9bcbab6` | 9 | Pass |
| sweep-material-choice | regression | `96d3458` | `c88f552f-511d-4ca3-999a-9eb087a13a5b` | 12 | Pass |
| blocked-child-independent-work | regression | `96d3458` | `9ac86859-c708-4f10-9e2f-63bcb2998a8a` | 8 | Pass |
| ready-queue-resume-preserves-scope | regression | `96d3458` | `991f1fe9-0acb-48ac-945c-fe4281b6fc63` | 8 | Pass |
| express-complete-return | regression | `96d3458` | `e9abd1c6-5287-49d5-9b9d-d09f736f2818` | 11 | Pass |
| coordinator-settles-review-notes | regression | `96d3458` | `5d713c6b-8769-4394-9734-4217d292361e` | 10 | Pass |

The old-text recommendation answer took `max_tokens` from the routine-choice rule and noted it "as an assumption in the handoff", without the PR description record the new criteria require. Both new-text answers quoted the unattended rule, listed the three parking conditions and showed that none applied, and recorded the decision in the notes and the PR description. The old-text parking answer stopped and returned the decision to the parent as a blocker, with no label, no comment, and the run halted; both new-text answers parked under the four steps, named the `triage:needs-input` label and the issue comment, and said `sweep-needs-input` resumes it. All three hard-stop answers halted from the identity rules; the new-text answers quoted the unattended exception list and said the deadline does not change the decision. The regression answers kept their decisions; the sweep and blocked-child answers still return material questions in interactive flows.

## Limits

No sample ran on the local Qwen model, and no unattended run has happened; the launcher script was dry-run only. The scenarios test the decision, not whether a worker executes the four parking steps with read-backs. One old-text sample per scenario. The grades are the author's.

## Checks

`make check` passed.

```scenario-results
[
  {"scenario": "unattended-takes-recommendation", "date": "2026-10-12", "skill_commit": "963b289", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Partial", "phase": "old text", "note": "Scratch baseline: took the recommendation but did not record it in the PR description.", "order": 1},
  {"scenario": "unattended-takes-recommendation", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "unattended-parks-on-uncertainty", "date": "2026-10-12", "skill_commit": "963b289", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Fail", "phase": "old text", "note": "Scratch baseline: halted and returned the decision without label or comment.", "order": 1},
  {"scenario": "unattended-parks-on-uncertainty", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "unattended-hard-stop-identity", "date": "2026-10-12", "skill_commit": "963b289", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "old text", "note": "Scratch baseline: decided from the identity and hard-stop rules.", "order": 1},
  {"scenario": "unattended-hard-stop-identity", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "sweep-material-choice", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "blocked-child-independent-work", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "ready-queue-resume-preserves-scope", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "express-complete-return", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "coordinator-settles-review-notes", "date": "2026-10-12", "skill_commit": "96d3458", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
