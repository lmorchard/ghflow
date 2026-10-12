# Coordinator ceremony decision samples, 2026-10-12

Three new scenarios cover the second round of coordinator ceremony changes: conditional shared-reference reads, reporting the endpoint from the ready read-back, and recovering from a placeholder dispatch. Each ran on Claude Sonnet once against the old text with the new criteria and twice against the changed text, and on the local Qwen model once against each text. Three related scenarios ran once on Sonnet as regression checks. Every sample reached the expected decision; the two old-text placeholder answers were partial because they did not name the extra call. On Qwen the new text did not reduce time or tokens. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-coordinator-ceremony-2-answers.txt) preserve the output used for grading. The source is the issue #1054 delivery record in [PR #74](https://github.com/lmorchard/ghflow/pull/74), with the [issue #1012 record](../../docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md) for the second placeholder dispatch and the third full pre-read.

## Source and method

The changed source commit is `224e7ef9f0c58611125abfd973b116fb5fc4596d` on branch `coordinator-ceremony-2`. The baseline commit is `5d5e15e` on the local scratch branch `baseline-ceremony-2`, which holds the skill text of main at `6cc6f46` plus the three new scenario files. It is not for merge.

Sonnet runs used the Claude Code runner `2.1.296` with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. Qwen runs used the OpenCode runner with `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` at `http://127.0.0.1:9931/v1`, context and output limits 262144, one at a time with the server otherwise idle, as the worker bounds report on branch `worker-bounds` describes; OpenCode does not report the runtime model. The author of the change is Claude Fable 5.1. Raw provenance remains under `/tmp/ceremony-runs/c2[bcr]-*` and `/tmp/ceremony-runs/q[bc]-c2-*`.

## Results

Grades use the criteria at commit `224e7ef` for every phase.

| Scenario | Phase | Commit | Session | Seconds | Output tokens | Reads | Grade |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| placeholder-dispatch-recovery | Sonnet, old text | `5d5e15e` | `63ae6604-8bae-4279-8df5-6d20bfd2c47a` | 11 | - | - | Partial |
| placeholder-dispatch-recovery | Sonnet, new text | `224e7ef` | `e1e1dc51-5946-487b-8cdb-4727ae6ea450` | 12 | - | - | Pass |
| placeholder-dispatch-recovery | Sonnet, new text | `224e7ef` | `d7c592a9-cafa-4df8-aa78-9183b6339606` | 11 | - | - | Pass |
| endpoint-report-from-readback | Sonnet, old text | `5d5e15e` | `1af2a3d2-1d68-4c42-884f-5a786ef348bc` | 11 | - | - | Pass |
| endpoint-report-from-readback | Sonnet, new text | `224e7ef` | `865782bb-2c33-4ec9-943f-33c32f02e58b` | 8 | - | - | Pass |
| endpoint-report-from-readback | Sonnet, new text | `224e7ef` | `a73692d5-48f8-4aef-89e2-e0f4ede66cb5` | 8 | - | - | Pass |
| shared-references-on-condition | Sonnet, old text | `5d5e15e` | `f2274b28-67ee-4125-be19-3a4e3b4fccd3` | 16 | - | - | Pass |
| shared-references-on-condition | Sonnet, new text | `224e7ef` | `d47ba224-5dff-4028-9d67-fd56b0a0ecf1` | 12 | - | - | Pass |
| shared-references-on-condition | Sonnet, new text | `224e7ef` | `2209a542-27f3-490d-a48a-a8797de34a8b` | 11 | - | - | Pass |
| coordinator-ready-to-dispatch | Sonnet, regression | `224e7ef` | `61831011-caef-42b5-8277-983d428fb5a0` | 15 | - | - | Pass |
| express-complete-return | Sonnet, regression | `224e7ef` | `3c05cd10-bd1f-4996-b4c4-f8080440088d` | 12 | - | - | Pass |
| followup-already-green | Sonnet, regression | `224e7ef` | `858bc592-6c19-4285-8c9b-3a1d04d10bc8` | 9 | - | - | Pass |
| placeholder-dispatch-recovery | Qwen, old text | `5d5e15e` | `ses_eced7b0ceffe75et9SO4WGRrzg` | 204 | 2881 | express-issue.md, coordination.md | Partial |
| placeholder-dispatch-recovery | Qwen, new text | `224e7ef` | `ses_eced47de0ffeGNGmolGt4LLfmg` | 224 | 3650 | express-issue.md, coordination.md | Pass |
| endpoint-report-from-readback | Qwen, old text | `5d5e15e` | `ses_eced1021cffe8XmSj6JVjuXv7e` | 253 | 4352 | express-issue.md | Pass |
| endpoint-report-from-readback | Qwen, new text | `224e7ef` | `ses_ececd1b44ffeczG3T0blAMseG0` | 281 | 4861 | express-issue.md, coordination.md | Pass |
| shared-references-on-condition | Qwen, old text | `5d5e15e` | `ses_ecec8c6a0ffe3lF61V26V2jR1v` | 259 | 3226 | SKILL.md, express-issue.md, two unknown | Pass |
| shared-references-on-condition | Qwen, new text | `224e7ef` | `ses_ecec4c315ffe4jD7oxiaN0RPDq` | 316 | 5435 | SKILL.md, express-issue.md | Pass |

Both old-text placeholder answers resumed the same worker from the worker-reuse rule and did not say they would name the extra call in the report; both new-text answers quoted the new sentence and named it. The old-text endpoint answers decided from the coordinator's role line and the read-back line; the new-text answers quoted the new sentence. The old-text pre-read answers decided from "load only the task and shared rules needed now" and from reading "locate" as confirming a path; the Qwen old-text answer said it would still read context.md first and bring the other references in "as each phase approaches", and it made two reads outside the snapshot. The new-text answers named Handoffs as the one reference to read before the first dispatch and quoted the condition list. The regression answers kept their decisions, and the coordinator-ready-to-dispatch answer added, unprompted, that it sends the handoff in the dispatch call and never with a placeholder.

### Qwen, old versus new

| Scenario | Old s / tokens | New s / tokens |
| --- | ---: | ---: |
| placeholder-dispatch-recovery | 204 / 2,881 | 224 / 3,650 |
| endpoint-report-from-readback | 253 / 4,352 | 281 / 4,861 |
| shared-references-on-condition | 259 / 3,226 | 316 / 5,435 |
| Total | 716 / 10,459 | 821 / 13,946 |

The new text cost more time and tokens on every scenario, the opposite of the worker bounds comparison on branch `worker-bounds`. The new-text answers quoted the added sentences at length and, for the pre-read scenario, listed the condition for each reference. The added cost is in the answer, not in a wrong turn.

## Limits

The scenarios do not discriminate old from new text on either model for the endpoint and pre-read decisions; both models reached them from the existing general rules. Only the placeholder scenario discriminates, and only on the report detail. The real-run behavior that motivated the pre-read change, three coordinators reading fifteen files before the first dispatch, did not appear in any decision sample on either text, so a scenario cannot show that the conditions change it; the next real delivery can. One sample per Qwen phase. The grades are the author's.

## Checks

`make check` passed: the CLI and script tests, source and link checks, scenario-index validation, and whitespace checks.

```scenario-results
[
  {"scenario": "placeholder-dispatch-recovery", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Partial", "phase": "Sonnet, old text", "note": "Scratch baseline: main text with the new criteria; did not name the extra call.", "order": 1},
  {"scenario": "placeholder-dispatch-recovery", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "Sonnet, new text", "note": null, "order": 2},
  {"scenario": "placeholder-dispatch-recovery", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Partial", "phase": "Qwen, old text", "note": "Runtime model not reported by OpenCode; did not name the extra call.", "order": 1},
  {"scenario": "placeholder-dispatch-recovery", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Pass", "phase": "Qwen, new text", "note": "Runtime model not reported by OpenCode.", "order": 2},
  {"scenario": "endpoint-report-from-readback", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "Sonnet, old text", "note": "Scratch baseline: main text with the new criteria.", "order": 1},
  {"scenario": "endpoint-report-from-readback", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "Sonnet, new text", "note": null, "order": 2},
  {"scenario": "endpoint-report-from-readback", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Pass", "phase": "Qwen, old text", "note": "Runtime model not reported by OpenCode.", "order": 1},
  {"scenario": "endpoint-report-from-readback", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Pass", "phase": "Qwen, new text", "note": "Runtime model not reported by OpenCode.", "order": 2},
  {"scenario": "shared-references-on-condition", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "Sonnet, old text", "note": "Scratch baseline: main text with the new criteria.", "order": 1},
  {"scenario": "shared-references-on-condition", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "Sonnet, new text", "note": null, "order": 2},
  {"scenario": "shared-references-on-condition", "date": "2026-10-12", "skill_commit": "5d5e15e", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Pass", "phase": "Qwen, old text", "note": "Runtime model not reported by OpenCode; two reads outside the snapshot.", "order": 1},
  {"scenario": "shared-references-on-condition", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "opencode", "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M", "grade": "Pass", "phase": "Qwen, new text", "note": "Runtime model not reported by OpenCode.", "order": 2},
  {"scenario": "coordinator-ready-to-dispatch", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "express-complete-return", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "followup-already-green", "date": "2026-10-12", "skill_commit": "224e7ef", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
