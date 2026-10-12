# Worker placeholder prompt decision samples, 2026-10-12

One new scenario covers the agent-neutral replacement for the OpenCode dispatch guard: a subagent that receives an empty or placeholder prompt returns one line asking for the handoff and stops. It ran on Claude Sonnet once against the old text with the new criteria and twice against the changed text; the coordinator-side recovery scenario ran once as a regression check. The old text was partial, the new text passed twice, and the regression passed. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-worker-placeholder-answers.txt) preserve the output used for grading. The source is the [issue #1053 delivery record](../../docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md): in three runs the cost of a placeholder dispatch was the worker's 11 to 16 minutes deliberating over a one-word message.

## Source and method

The changed source commit is `ceb01344d29d3f0f1f173a5a99a1b1a67f995c6d` on branch `replace-dispatch-guard`. The baseline commit is `ce28fea` on the local scratch branch `baseline-worker-placeholder`, which holds the skill text of main at `fa3d927` plus the new scenario file. It is not for merge.

Runs used the Claude Code runner `2.1.296` with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. The author of the change is Claude Fable 5.1. Runs took 9 to 10 seconds.

## Results

Grades use the criteria at commit `ceb0134` for both phases.

| Scenario | Phase | Commit | Session | Seconds | Grade |
| --- | --- | --- | --- | ---: | --- |
| worker-placeholder-prompt | old text | `ce28fea` | `d16a2910-f42b-40af-b24e-29f63088f6aa` | 10 | Partial |
| worker-placeholder-prompt | new text | `ceb0134` | `c28afd5a-801b-4648-b0ea-ff6624e9eaa0` | 10 | Pass |
| worker-placeholder-prompt | new text | `ceb0134` | `d88fb455-ead8-4ab3-87de-b1925a75a62a` | 9 | Pass |
| placeholder-dispatch-recovery | regression | `ceb0134` | `e262dc57-518a-4cb4-8e66-713f7d5e7b66` | 10 | Pass |

The old-text answer took no action and did not infer permission, from the Authorization rule against inferring a decision from silence, but it said it would send nothing, or at most a line restating that its earlier report stood; it did not ask for the handoff. Both new-text answers quoted the new sentence, replied with one line asking for the handoff, and listed what they would not do. The regression answer kept the coordinator-side recovery.

## Limits

A decision scenario cannot show the time saved; the real cost was a local model's long deliberation, and the next local-model run is the test. One old-text sample. The grades are the author's.

## Checks

`make check` passed.

```scenario-results
[
  {"scenario": "worker-placeholder-prompt", "date": "2026-10-12", "skill_commit": "ce28fea", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Partial", "phase": "old text", "note": "Scratch baseline: took no action but did not ask for the handoff.", "order": 1},
  {"scenario": "worker-placeholder-prompt", "date": "2026-10-12", "skill_commit": "ceb0134", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "placeholder-dispatch-recovery", "date": "2026-10-12", "skill_commit": "ceb0134", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
