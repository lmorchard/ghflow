# Unattended time budget, decision samples, 2026-10-13

One new scenario covers the time-budget change from the [unattended burndown record](../../docs/research/trials/2026-10-13-unattended-burndown.md). With 19 minutes left, the coordinator judged a correction for two optional reviewer notes affordable because CI ran in two minutes. The correction took 44 minutes, and the issue was parked mid-correction. The scenario ran on Claude Sonnet and on the local Qwen model against the old and new text. Two regressions ran on Sonnet. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-13-unattended-budget-answers.txt) preserve the graded output.

## Source and method

The changed commit is `8e97ff9` on branch `unattended-budget-b`. The baseline commit is `5fb3819` on the local scratch branch `baseline-unattended-budget-b`, which holds main at `acbaeb1` plus the scenario. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server, with the controls that earlier results record.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| deadline-declines-optional-notes | old text | claude-sonnet-5-5 | `5fb3819` | `93af7264-27a7-437c-8cd2-4b8ea7903cd1` | Pass |
| deadline-declines-optional-notes | new text | claude-sonnet-5-5 | `8e97ff9` | `eea619fa-9c70-4921-a88d-6f9407c7515b` | Pass |
| deadline-declines-optional-notes | new text | claude-sonnet-5-5 | `8e97ff9` | `c8e6ae92-7359-419b-9d13-c22157cf9fba` | Pass |
| deadline-declines-optional-notes | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `5fb3819` | `ses_ec9b156a7ffe7JISfPuDuygOqX` | Pass |
| deadline-declines-optional-notes | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `8e97ff9` | `ses_ec9ac8c12ffeuhUY9Ktw2K60jK` | Pass |
| coordinator-settles-review-notes | regression | claude-sonnet-5-5 | `8e97ff9` | `2e33958b-17a8-4605-96d1-8c4195a78ff9` | Pass |
| burndown-refreshes-stale-facts | regression | claude-sonnet-5-5 | `8e97ff9` | `d1f839f1-f95b-4b94-8716-24ce62a2cf37` | Pass |

Every answer declined both notes and dispatched the ready step, including both baselines. Given measured durations in the prompt, both models do the arithmetic from the general note-settling rule. The new-text answers cited the new rule and estimated from the measured worker, review, and turn durations. They also said that two-minute CI is not an estimate. The scenario does not separate old text from new on either model. Last night's failure happened when those durations sat in hours of the coordinator's own history, not in a prompt, and the new text names that estimate explicitly.

## Limits

The scenario does not discriminate on either model, so it guards the new rule against regression rather than proving its effect. The next unattended run is the real test. The grades are the author's.

```scenario-results
[
 {
  "scenario": "deadline-declines-optional-notes",
  "date": "2026-10-13",
  "skill_commit": "5fb3819",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "Decided from the general note-settling rule with durations given.",
  "order": 1
 },
 {
  "scenario": "deadline-declines-optional-notes",
  "date": "2026-10-13",
  "skill_commit": "8e97ff9",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "deadline-declines-optional-notes",
  "date": "2026-10-13",
  "skill_commit": "5fb3819",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "old text",
  "note": "Same as Sonnet's baseline.",
  "order": 1
 },
 {
  "scenario": "deadline-declines-optional-notes",
  "date": "2026-10-13",
  "skill_commit": "8e97ff9",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "coordinator-settles-review-notes",
  "date": "2026-10-13",
  "skill_commit": "8e97ff9",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "burndown-refreshes-stale-facts",
  "date": "2026-10-13",
  "skill_commit": "8e97ff9",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
