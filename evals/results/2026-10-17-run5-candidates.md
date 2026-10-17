# Fifth burndown candidates, decision samples, 2026-10-17

These samples check the changes from the [fifth burndown record](../../docs/research/trials/2026-10-17-unattended-burndown-5.md). The `handoff prepare-project-facts` operation and the ready-without-review text address the facts refresh that gained a review cycle. The implement-issue rule addresses the non-gate eval that took about 70 minutes. Two regressions cover the facts refresh and conditional reads. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-17-run5-candidates-answers.txt) preserve the graded output.

## Source and method

The changed commit is `a07fee3` on branch `run5-cli-candidates`. The later commit `569d976` adds only the `refresh` budget kind. The baseline commit is `48038fa` on the local scratch branch `baseline-run5-candidates`, which holds `main` at `4d95af5` plus the two scenarios. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner, and the eval scenario also ran on the local Qwen model under the OpenCode 2.0.29 runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| facts-refresh-ready-without-review | old text | claude-sonnet-5-5 | `48038fa` | `1a242e0c-7860-43d9-bc80-8852379f90aa` | Partial |
| facts-refresh-ready-without-review | new text | claude-sonnet-5-5 | `a07fee3` | `499723c0-b53c-4d2b-8790-ff1506ca2c80` | Pass |
| facts-refresh-ready-without-review | new text | claude-sonnet-5-5 | `a07fee3` | `ddac5744-b829-4818-af75-8a950741fa38` | Pass |
| non-gate-check-environment-failure | old text | claude-sonnet-5-5 | `48038fa` | `7ff49a77-06c7-4a93-9659-506c78184087` | Pass |
| non-gate-check-environment-failure | new text | claude-sonnet-5-5 | `a07fee3` | `c0a0aa50-5e4d-47fe-90ca-9de12f0150b1` | Pass |
| non-gate-check-environment-failure | new text | claude-sonnet-5-5 | `a07fee3` | `72ac0c6f-bf3c-491e-9291-f766ea95fbc0` | Pass |
| non-gate-check-environment-failure | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `48038fa` | `ses_eb53ff1caffenh6I6oDg6F6Ud9` | Pass |
| non-gate-check-environment-failure | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `a07fee3` | `ses_eb53cd050ffeP7NqE93Kq5PzqJ` | Pass |
| burndown-refreshes-stale-facts | regression | claude-sonnet-5-5 | `a07fee3` | `ed2ba1d9-7a4b-484c-b7b8-abce5395421f` | Pass |
| burndown-conditional-reads | regression | claude-sonnet-5-5 | `a07fee3` | `c5e37324-ab84-47d0-9666-4a6b19f57228` | Pass |

The old-text facts answer wrote the right handoff content by hand, so it scores Partial; both new-text answers used `handoff prepare-project-facts` and dispatched no review. All three answers noticed that `budget` had no kind for a refresh, which `569d976` adds.

The eval scenario does not separate the texts. The old text passed on both models by inference from "do not connect to live services" and the authorization limits. In the live run the worker drifted into the eval mid-task with a large context, which a single framed question does not reproduce. The new rule states the limit directly; whether it changes live behavior needs the next run.

## Limits

The CLI changes have unit tests and a live, read-only `handoff prepare-project-facts` run against the decafclaw checkout. The board guard has unit tests and subprocess tests with the fake `gh`, and has not run against the live board. The grades are the author's.

## Checks

`make check` passed on `569d976`.

```scenario-results
[
 {
  "scenario": "facts-refresh-ready-without-review",
  "date": "2026-10-17",
  "skill_commit": "48038fa",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Right content; handwritten handoff.",
  "order": 1
 },
 {
  "scenario": "facts-refresh-ready-without-review",
  "date": "2026-10-17",
  "skill_commit": "a07fee3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "non-gate-check-environment-failure",
  "date": "2026-10-17",
  "skill_commit": "48038fa",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": null,
  "order": 1
 },
 {
  "scenario": "non-gate-check-environment-failure",
  "date": "2026-10-17",
  "skill_commit": "a07fee3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "non-gate-check-environment-failure",
  "date": "2026-10-17",
  "skill_commit": "48038fa",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "old text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "non-gate-check-environment-failure",
  "date": "2026-10-17",
  "skill_commit": "a07fee3",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 4
 },
 {
  "scenario": "burndown-refreshes-stale-facts",
  "date": "2026-10-17",
  "skill_commit": "a07fee3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-17",
  "skill_commit": "a07fee3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
