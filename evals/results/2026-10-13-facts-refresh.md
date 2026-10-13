# Facts refresh at burndown start, decision samples, 2026-10-13

One new scenario covers the "Check the project facts" step in burndown-ready-queue. It ran on Claude Sonnet once against the old text, twice against the first changed text, and once against the final text, which adds the refresh-failure sentence. Four related scenarios ran once each as regression checks. The baseline failed as intended, and every changed-text and regression sample passed. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-13-facts-refresh-answers.txt) preserve the output used for grading. The source is the unattended burndown record in [PR #89](https://github.com/lmorchard/ghflow/pull/89): `facts` reported `AGENTS.md` and `CLAUDE.md` stale at the start, and the coordinator moved on. Les decided on 2026-10-13 that the refresh belongs in the burndown.

## Source and method

The first changed commit is `15d84e0` and the final commit is `e882a6e` on branch `facts-refresh-step`. The baseline commit is `ed6e9bc` on the local scratch branch `baseline-facts-refresh`, which holds main at `694e7f7` plus the new scenario. It is not for merge. Runs used the Claude Code runner `2.1.296 (Claude Code)` with the controls that earlier results record. The selected model was `claude-sonnet-5-5`. The author of the change is Claude Fable 5.1 and Claude Opus 5.5.

## Results

| Scenario | Phase | Commit | Session | Grade |
| --- | --- | --- | --- | --- |
| burndown-refreshes-stale-facts | old text | `ed6e9bc` | `56907f86-3021-4a4f-adb0-b442379edb20` | Fail |
| burndown-refreshes-stale-facts | new text | `15d84e0` | `f00aab3e-a4fa-4f24-970e-49ff8cc9d794` | Pass |
| burndown-refreshes-stale-facts | new text | `15d84e0` | `5984c12f-2e2f-400e-b587-abe4e1e89d41` | Pass |
| burndown-refreshes-stale-facts | final text | `e882a6e` | `a7f3e440-4572-4f28-9a48-3d82e7462da7` | Pass |
| project-facts-stale-source | regression | `15d84e0` | `35e2c14e-6831-4023-881e-9eecc0695799` | Pass |
| handoff-points-to-project-facts | regression | `15d84e0` | `2fd41ff9-fdcd-4e9e-8fc4-a3988c13610c` | Pass |
| unattended-parks-on-uncertainty | regression | `15d84e0` | `8cb5b491-f701-4f79-854e-6c3d3821b0e2` | Pass |
| unattended-takes-recommendation | regression | `15d84e0` | `391368ed-063a-4436-ad92-3fe21d8a6df4` | Pass |

The baseline answer dispatched the first worker with the stale file, named `Makefile` as stale, and refused the refresh as an unauthorized write in an unattended run, which is the first Not-acceptable answer. All three changed-text answers dispatched the refresh first, cited the queue request's authorization, kept the PR unmerged, and pointed every handoff at the refreshed copy in the refresh worktree. One answer noted that the text said nothing about a failed refresh; the final commit adds that sentence, and the final-text answer still passed. The single-issue regression kept its behavior: it named the stale source and did not refresh, which is the intended split between one issue and a queue.

## Limits

No sample ran on the local Qwen model. The step has not run in a real burndown. The grades are the author's.

## Checks

`make check` passed on `e882a6e`.

```scenario-results
[
  {"scenario": "burndown-refreshes-stale-facts", "date": "2026-10-13", "skill_commit": "ed6e9bc", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Fail", "phase": "old text", "note": "Scratch baseline: dispatched with the stale file and refused the refresh as unauthorized.", "order": 1},
  {"scenario": "burndown-refreshes-stale-facts", "date": "2026-10-13", "skill_commit": "15d84e0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "burndown-refreshes-stale-facts", "date": "2026-10-13", "skill_commit": "e882a6e", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "final text", "note": "Adds the refresh-failure sentence.", "order": 3},
  {"scenario": "project-facts-stale-source", "date": "2026-10-13", "skill_commit": "15d84e0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "handoff-points-to-project-facts", "date": "2026-10-13", "skill_commit": "15d84e0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "unattended-parks-on-uncertainty", "date": "2026-10-13", "skill_commit": "15d84e0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "unattended-takes-recommendation", "date": "2026-10-13", "skill_commit": "15d84e0", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
