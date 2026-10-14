# Worker model as a runtime self-report, decision samples, 2026-10-14

The [second burndown record](../../docs/research/trials/2026-10-14-unattended-burndown-2.md) found two identity problems. #95 told the coordinator to take each worker's model from dispatch-result metadata, but OpenCode keeps that metadata out of the text the coordinator receives. Implementers also recorded the configured default model from `facts` as their own identity. The change asks each worker for the model ID its runtime states to it and records that as a self-report. It never records a configured model, and it removes the configured default fields from `facts` runtime. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-identity-self-report-answers.txt) preserve the graded output.

## Source and method

The changed commits are `b5e4e31` and `6066701` on branch `identity-self-report`. The second puts the rule in implement-issue's return line, which the worker reads. The baseline commit is `466a426` on the local scratch branch `baseline-identity-self-report`, which holds main at the PR #98 merge plus the scenario criteria. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| worker-reports-own-model | old text | claude-sonnet-5-5 | `466a426` | `ccb9f591-1fa0-4361-85aa-a65027c43260` | Partial |
| worker-reports-own-model | new text | claude-sonnet-5-5 | `b5e4e31` | `56020d76-3ffa-4fc5-b286-be31584298ac` | Partial |
| worker-reports-own-model | new text | claude-sonnet-5-5 | `b5e4e31` | `e4b06029-240e-4817-afe6-d05e3d703589` | Partial |
| worker-reports-own-model | final text | claude-sonnet-5-5 | `6066701` | `95370a5f-8133-4b64-87c8-538048fde226` | Pass |
| worker-reports-own-model | final text | claude-sonnet-5-5 | `6066701` | `3e4630a2-2d1c-459b-9c7f-b515b6946e15` | Pass |
| waiver-skips-config-reads | old text | claude-sonnet-5-5 | `466a426` | `37ff36d0-9480-468b-8144-35e009a5b8be` | Fail |
| waiver-skips-config-reads | new text | claude-sonnet-5-5 | `b5e4e31` | `39c19480-620a-451b-9e4b-fbc6fd327122` | Pass |
| same-model-request-identity-gap | regression | claude-sonnet-5-5 | `b5e4e31` | `eb2fc676-1505-480a-b324-82587ce972cc` | Pass |
| coordinator-uses-session-facts | regression | claude-sonnet-5-5 | `b5e4e31` | `80fa6f60-7203-4a6b-ad5d-e7d071443d66` | Pass |

On the old text, the worker reported `llama.cpp/llama` but planned to note the configured default beside it as an unreconciled observation. That is the ambiguity the run showed, so it scores Partial. The first changed commit put the rule only in Review and Handoffs, and both samples still noted the configured value, also Partial. With the rule in implement-issue's return line, both samples left the configured value out. On the old text, the waiver scenario planned to read dispatch metadata, which OpenCode does not show to the agent, so it scores Fail. On the new text it asked for self-reports. Both regressions passed.

## Limits

No Qwen sample ran. A self-report is only as good as the runtime's statement to the worker. The grades are the author's.

## Checks

`make check` passed on `6066701`.

```scenario-results
[
 {
  "scenario": "worker-reports-own-model",
  "date": "2026-10-14",
  "skill_commit": "466a426",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Planned to note the configured default beside its model.",
  "order": 1
 },
 {
  "scenario": "worker-reports-own-model",
  "date": "2026-10-14",
  "skill_commit": "b5e4e31",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial / Partial",
  "phase": "new text",
  "note": "Rule not yet in implement-issue; led to 6066701.",
  "order": 2
 },
 {
  "scenario": "worker-reports-own-model",
  "date": "2026-10-14",
  "skill_commit": "6066701",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "waiver-skips-config-reads",
  "date": "2026-10-14",
  "skill_commit": "466a426",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Planned to read dispatch metadata the agent cannot see.",
  "order": 1
 },
 {
  "scenario": "waiver-skips-config-reads",
  "date": "2026-10-14",
  "skill_commit": "b5e4e31",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "same-model-request-identity-gap",
  "date": "2026-10-14",
  "skill_commit": "b5e4e31",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "coordinator-uses-session-facts",
  "date": "2026-10-14",
  "skill_commit": "b5e4e31",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
