# Burndown conditional reads and coordinator code research, decision samples, 2026-10-13

Two new scenarios cover two changes from the [unattended burndown record](../../docs/research/trials/2026-10-13-unattended-burndown.md). First, the burndown coordinator read 19 references before its first dispatch. Second, it read subject code for 11 and 15 minutes to scope handoffs. A related fact was verified the same day: an OpenCode subagent has no task tool, so the queue coordinator coordinates every issue itself. Each scenario ran on Claude Sonnet and on the local Qwen model against the old and new text. Two regressions ran on Sonnet. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-13-coordinator-discipline-answers.txt) preserve the graded output.

## Source and method

The changed commits are `836c20e` and `7bca605` on branch `coordinator-discipline-a`; the second names express-issue as the coordinator's own procedure after the first Qwen sample grouped it with the worker references. The baseline commit is `27b1a2d` on the local scratch branch `baseline-coordinator-discipline-a`, which holds main at `acbaeb1` plus the scenarios. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server, with the controls that earlier results record.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| burndown-conditional-reads | old text | claude-sonnet-5-5 | `27b1a2d` | `2d94d21a-da08-4173-91b0-484925467725` | Partial |
| burndown-conditional-reads | new text | claude-sonnet-5-5 | `836c20e` | `08ef016f-6588-4592-b179-a3dbf4b1aef9` | Pass |
| burndown-conditional-reads | new text | claude-sonnet-5-5 | `836c20e` | `7db35ac7-acc0-4d7a-8b09-f87c60c9d92b` | Pass |
| burndown-conditional-reads | final text | claude-sonnet-5-5 | `7bca605` | `dcfe00dc-f56b-4457-805e-d12416524ed3` | Pass |
| burndown-conditional-reads | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `27b1a2d` | `ses_ec9a877a6ffeQtIKhM5CWTMckq` | Partial |
| burndown-conditional-reads | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `836c20e` | `ses_ec9a3840fffekjKjwp4ivFYNgI` | Partial |
| burndown-conditional-reads | final text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `7bca605` | `ses_ec9974218ffelsJTlUsXBfMriB` | Pass |
| burndown-no-code-research | old text | claude-sonnet-5-5 | `27b1a2d` | `281bb519-1632-4677-9194-c31a308594b1` | Pass |
| burndown-no-code-research | new text | claude-sonnet-5-5 | `836c20e` | `601b0c83-82f0-4519-9d1c-6e1da313b461` | Pass |
| burndown-no-code-research | new text | claude-sonnet-5-5 | `836c20e` | `ef4ff4a3-a630-4de3-9c9c-438fad22a4ff` | Pass |
| burndown-no-code-research | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `27b1a2d` | `ses_ec99d166affep687f5hfjefwtR` | Pass |
| burndown-no-code-research | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `836c20e` | `ses_ec999c094ffe89GEx4t5UluUKZ` | Pass |
| shared-references-on-condition | regression | claude-sonnet-5-5 | `836c20e` | `5c60f2ab-5084-480b-a43a-31897ba42593` | Pass |
| coordinator-ready-to-dispatch | regression | claude-sonnet-5-5 | `836c20e` | `d0a20493-dff9-4ddd-bf37-d68b8b68b4fd` | Pass |

On the old text, both models already declined to read everything first, citing the general rule in `SKILL.md`. Both still left express-issue to a dispatched worker, which OpenCode cannot do, so neither read express-issue or Handoffs before the first dispatch. Each scored Partial. The first new-text Qwen sample made the same grouping error, which led to the second commit; on that commit Qwen and Sonnet each read express-issue and Handoffs before the first dispatch. The code-research scenario passed on both models and both texts. In isolation the decision is easy, and last night's failure came after hours of accumulated context. The new text adds the explicit rule and the OpenCode path, which the new-text answers cited.

## Limits

These scenarios do not reproduce a long coordinator context, which is where the trial failures happened. The next unattended run is the real test of both changes. The grades are the author's.

```scenario-results
[
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "27b1a2d",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Left express-issue to a worker; no Handoffs read before dispatch.",
  "order": 1
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "7bca605",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "27b1a2d",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Partial",
  "phase": "old text",
  "note": "Same grouping as Sonnet's baseline.",
  "order": 1
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Partial",
  "phase": "new text",
  "note": "Grouped express-issue with the worker references; led to 7bca605.",
  "order": 2
 },
 {
  "scenario": "burndown-conditional-reads",
  "date": "2026-10-13",
  "skill_commit": "7bca605",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "burndown-no-code-research",
  "date": "2026-10-13",
  "skill_commit": "27b1a2d",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": null,
  "order": 1
 },
 {
  "scenario": "burndown-no-code-research",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "burndown-no-code-research",
  "date": "2026-10-13",
  "skill_commit": "27b1a2d",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "old text",
  "note": null,
  "order": 1
 },
 {
  "scenario": "burndown-no-code-research",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "shared-references-on-condition",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "coordinator-ready-to-dispatch",
  "date": "2026-10-13",
  "skill_commit": "836c20e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
