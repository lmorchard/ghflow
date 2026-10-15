# Worker conditional reads, decision samples, 2026-10-15

In the [third burndown](../../docs/research/trials/2026-10-15-unattended-burndown-3.md), implementation workers read 11 or 12 references before starting. implement-issue, submit-pr, and review-changes opened with "Apply ... throughout", the pattern that #77 and #93 replaced for the coordinators. Each now names its shared references with the condition that calls for them. One new scenario ran on Claude Sonnet and on the local Qwen model against the old and new text, and two regressions ran on Sonnet. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-15-worker-conditional-reads-answers.txt) preserve the graded output.

## Source and method

The changed commit is `eadcca3` on branch `worker-conditional-reads`. The baseline commit is `37d4082` on the local scratch branch `baseline-worker-reads`, which holds main at the PR #112 merge plus the scenario. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| worker-conditional-reads | old text | claude-sonnet-5-5 | `37d4082` | `9fcbd73f-02e2-4b14-8418-3543c8f7f739` | Pass |
| worker-conditional-reads | new text | claude-sonnet-5-5 | `eadcca3` | `29e9b710-2bff-4e4f-a393-c8b60eb03049` | Pass |
| worker-conditional-reads | new text | claude-sonnet-5-5 | `eadcca3` | `065dcabe-9c28-4809-a7b1-6b6a3b545de2` | Pass |
| worker-conditional-reads | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `37d4082` | `ses_ebfeddeb9ffekbNTESMcWfcme5` | Pass |
| worker-conditional-reads | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `eadcca3` | `ses_ebfebbaefffeLmVEfgqORIPPSx` | Pass |
| worker-reports-own-model | regression | claude-sonnet-5-5 | `eadcca3` | `55e76d00-e772-4fa0-9270-7acd4b54b69a` | Pass |
| notes-edit-without-amend | regression | claude-sonnet-5-5 | `eadcca3` | `2daf481c-ff67-454e-bb04-173affd03f47` | Pass |

Every answer declined the bulk read, including both baselines. Given an explicit plan to read ten references, both models reject it from the general rule in Working context. The live failure happened in a real worker session, where no such plan was stated. The Qwen runs read two files on the old text and one on the new. The new-text answers cited the conditions in implement-issue's opening and named Agent identity as the first reference to read, before the first Git command.

## Limits

The scenario does not separate old text from new on either model, so it guards the rule rather than proving it. The same change to the coordinators in #93 cut their reference reads from 19 to 9 in the next live run. The next run is the real test of this change. The grades are the author's.

## Checks

`make check` passed on `eadcca3`.

```scenario-results
[
 {
  "scenario": "worker-conditional-reads",
  "date": "2026-10-15",
  "skill_commit": "37d4082",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "Declined from the general Working context rule.",
  "order": 1
 },
 {
  "scenario": "worker-conditional-reads",
  "date": "2026-10-15",
  "skill_commit": "eadcca3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "worker-conditional-reads",
  "date": "2026-10-15",
  "skill_commit": "37d4082",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "old text",
  "note": "Two reads.",
  "order": 1
 },
 {
  "scenario": "worker-conditional-reads",
  "date": "2026-10-15",
  "skill_commit": "eadcca3",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": "One read.",
  "order": 2
 },
 {
  "scenario": "worker-reports-own-model",
  "date": "2026-10-15",
  "skill_commit": "eadcca3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "notes-edit-without-amend",
  "date": "2026-10-15",
  "skill_commit": "eadcca3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
