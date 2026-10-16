# Queue select, queue summary, and budget, decision samples, 2026-10-16

`queue select` replaces the hand-run board traversal and its validation in the burndown and curation tasks. `queue summary` reads the GitHub facts for the delivery table. `budget` keeps measured durations in a log. In the [fourth burndown](../../docs/research/trials/2026-10-15-unattended-burndown-4.md), the coordinator measured a duration from a PR's `updatedAt`. One new scenario checks that a coordinator estimates from the budget log. Three regressions cover a failed traversal, the size order, and the deadline. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-16-queue-budget-answers.txt) preserve the graded output.

## Source and method

The changed commit is `0311599` on branch `cli-queue-budget`, stacked on #120. The baseline commit is `09fcf07` on the local scratch branch `baseline-cli-queue-budget`, which holds the #120 branch plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| budget-from-measured-marks | old text | claude-sonnet-5-5 | `09fcf07` | `6374e025-a002-4011-b3c0-19ebc402755f` | Partial |
| budget-from-measured-marks | new text | claude-sonnet-5-5 | `0311599` | `1bee3fc0-bf1d-4041-8890-de826e0960fa` | Pass |
| budget-from-measured-marks | new text | claude-sonnet-5-5 | `0311599` | `8f3c9f80-87db-4e52-917e-1a4cfc9f464b` | Pass |
| ready-queue-later-page-failure | regression | claude-sonnet-5-5 | `0311599` | `e4569f70-d450-4fb2-afe9-36cddf25d21c` | Pass |
| burndown-orders-by-size | regression | claude-sonnet-5-5 | `0311599` | `83d3d273-520e-460c-8e0e-5c9b954c36f1` | Pass |
| deadline-ready-step-finishes | regression | claude-sonnet-5-5 | `0311599` | `c13a27ee-fd86-4f23-ab52-e100a2505325` | Pass |

The old-text answer closed the review mark, declined to use `updatedAt`, and reached the right decision, but it added the durations by hand. It scores Partial. Both new-text answers ran `budget --end review:164` and `budget --need`, named the null `fits` for the unmeasured correction kind, and ignored `updatedAt` for timing. The failed-traversal regression retried `queue select` once and refused to report a clear queue. The size-order regression took the order from `selection`.

## Limits

The commands have unit tests with a fake `gh`. `queue select` and `queue summary` also ran live, read-only, against the decafclaw board. `queue select` read 2 pages and 199 items, and the In review column came back in size order. `queue summary` reported the PR, head, and board status for #1053, #165, #164, #929, and #947 as the trial records give them. `budget` has not run in a burndown. The grades are the author's.

## Checks

`make check` passed on `0311599`.

```scenario-results
[
 {
  "scenario": "budget-from-measured-marks",
  "date": "2026-10-16",
  "skill_commit": "09fcf07",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Right decision; hand arithmetic.",
  "order": 1
 },
 {
  "scenario": "budget-from-measured-marks",
  "date": "2026-10-16",
  "skill_commit": "0311599",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "ready-queue-later-page-failure",
  "date": "2026-10-16",
  "skill_commit": "0311599",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "burndown-orders-by-size",
  "date": "2026-10-16",
  "skill_commit": "0311599",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-16",
  "skill_commit": "0311599",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
