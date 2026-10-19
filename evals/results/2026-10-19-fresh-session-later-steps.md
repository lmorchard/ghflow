# New sessions for corrections, re-reviews, and the ready step, decision samples, 2026-10-19

On 2026-10-19 the coordinator resuming #994 tried to resume the implementation worker's session for a correction. That session had ended at 222,000 tokens, and the local server's 262,144-token cache is shared between slots, so every attempt failed with "Context size has been exceeded". Les approved dispatching later steps fresh. express-issue and Coordination now give corrections, re-reviews, and the ready step a new session from a `handoff` file. One new scenario covers the case; four existing scenarios that expected resumed workers were updated, and one that expects implementation and draft publication in one session is a regression. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-19-fresh-session-later-steps-answers.txt) preserve the graded output.

## Source and method

The changed commits are `37278c9` and `cbeb970` on branch `fresh-session-later-steps`; `cbeb970` updates the four scenarios. The baseline commit is `810cb95` on the local scratch branch `baseline-fresh-session`, which holds `main` at `cbc2654` plus the new scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| correction-goes-to-fresh-session | old text | claude-sonnet-5-5 | `810cb95` | `3445b8ee-855e-4be3-97a8-75cb0fcb45be` | Fail |
| correction-goes-to-fresh-session | new text | claude-sonnet-5-5 | `cbeb970` | `973977f1-c058-42f7-a2e7-a49f751c2a32` | Pass |
| correction-goes-to-fresh-session | new text | claude-sonnet-5-5 | `cbeb970` | `0f3ee284-d0b7-4728-b027-938bdb801054` | Pass |
| corrections-same-worker | updated | claude-sonnet-5-5 | `cbeb970` | `60174c35-e51d-4080-a840-42ae71dee9df` | Pass |
| draft-pr-ready-transition | updated | claude-sonnet-5-5 | `cbeb970` | `2b08bbc6-52a7-4c66-ad05-42eeaa413292` | Pass |
| placeholder-dispatch-recovery | updated | claude-sonnet-5-5 | `cbeb970` | `d3a87b65-86dd-45cf-8697-98a00eae2868` | Pass |
| coordinator-settles-review-notes | updated | claude-sonnet-5-5 | `cbeb970` | `b289a73a-05b8-417a-ab9a-5ac04b416805` | Pass |
| implementation-handoff-operation-scope | regression | claude-sonnet-5-5 | `cbeb970` | `46dcaccb-dd94-4fdb-bab3-a62a5c63eea3` | Pass |

The old text resumed the long implementation session, citing the rule that one worker carries corrections and the ready step. Both new-text answers wrote the correction handoff with `handoff address-pr-review`, dispatched a new session, and planned a new reviewer and a new ready worker. The updated scenarios passed on the new text, and the implementation handoff still names draft publication in the same session.

## Limits

No live run has used the new rule yet. The decision samples cannot show whether the coordinator follows it under a long context. The grades are the author's.

## Checks

`make check` passed on `cbeb970`.

```scenario-results
[
 {
  "scenario": "correction-goes-to-fresh-session",
  "date": "2026-10-19",
  "skill_commit": "810cb95",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Resumed the long implementation session.",
  "order": 1
 },
 {
  "scenario": "correction-goes-to-fresh-session",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "corrections-same-worker",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "updated",
  "note": null,
  "order": null
 },
 {
  "scenario": "draft-pr-ready-transition",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "updated",
  "note": null,
  "order": null
 },
 {
  "scenario": "placeholder-dispatch-recovery",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "updated",
  "note": null,
  "order": null
 },
 {
  "scenario": "coordinator-settles-review-notes",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "updated",
  "note": null,
  "order": null
 },
 {
  "scenario": "implementation-handoff-operation-scope",
  "date": "2026-10-19",
  "skill_commit": "cbeb970",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
