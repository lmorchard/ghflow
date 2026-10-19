# Resume time parks, and start and park, decision samples, 2026-10-18

On 2026-10-18 Les decided that a delivery that does not fit the time left is started and parked so that its progress is kept, and that the burndown resumes it. `queue select` now lists time-parked deliveries under `parked`, the burndown selects them before Ready issues, and `handoff --deadline` tells the worker to commit and publish at the deadline. Two new scenarios cover the resume and the start; two regressions cover the deadline and budget rules. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-18-resume-time-parks-answers.txt) preserve the graded output.

## Source and method

The changed commits are `a25494c` and `6f52632` on branch `resume-time-parks`. `6f52632` adds the label restore after the first resume samples missed it. The baseline commit is `b1c6d08` on the local scratch branch `baseline-resume-time-parks`, which holds `main` plus the two scenarios. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| burndown-resumes-time-parks | old text | claude-sonnet-5-5 | `b1c6d08` | `e8a331c5-f223-4344-8582-56f9693d4229` | Fail |
| burndown-resumes-time-parks | first change | claude-sonnet-5-5 | `a25494c` | `52ef6198-2a9a-49a8-9f25-2cc5c7197c6f` | Partial |
| burndown-resumes-time-parks | first change | claude-sonnet-5-5 | `a25494c` | `8be996fb-f4ad-4264-a59a-b3d30938c945` | Partial |
| burndown-resumes-time-parks | new text | claude-sonnet-5-5 | `6f52632` | `3e036ddd-d81b-40ed-ba2f-8ee7984befc4` | Pass |
| burndown-resumes-time-parks | new text | claude-sonnet-5-5 | `6f52632` | `49b7044d-8cbf-42e3-b986-9eba6e7d49c5` | Pass |
| start-and-park-when-it-will-not-fit | old text | claude-sonnet-5-5 | `b1c6d08` | `24126e5b-1b9f-484f-a8b5-af25e292713c` | Partial |
| start-and-park-when-it-will-not-fit | new text | claude-sonnet-5-5 | `a25494c` | `b2fa035e-eaf8-433c-a8bd-5c234a448876` | Pass |
| start-and-park-when-it-will-not-fit | new text | claude-sonnet-5-5 | `a25494c` | `8c7882c5-ab86-4909-bdc8-cdfe49cb89b7` | Pass |
| deadline-ready-step-finishes | regression | claude-sonnet-5-5 | `a25494c` | `9e0ba46c-79d1-4900-96e0-a238c94d7f75` | Pass |
| budget-from-measured-marks | regression | claude-sonnet-5-5 | `a25494c` | `c3bf8a81-f3fa-4372-b990-5819108137c1` | Pass |

The old text left the parked delivery out of the selection, and started the delivery that did not fit but with no deadline in the worker's handoff. On `a25494c`, both resume answers put #994 first but left its `triage:needs-input` label in place, and one said that it would not edit the label; the restore was only in express-issue. `6f52632` states it in the burndown, and both answers then restored the label before the first dispatch. Both start-and-park answers recorded the estimate, started #994, passed `--deadline`, and planned `park --kind time`.

## Limits

The CLI changes have unit tests with a fake `gh`, and `queue select` ran live, read-only, on the decafclaw board, where `parked` is empty because #994 was cut off before any park. No live run has parked and resumed a delivery through these steps. The grades are the author's.

## Checks

`make check` passed on `6f52632`.

```scenario-results
[
 {
  "scenario": "burndown-resumes-time-parks",
  "date": "2026-10-18",
  "skill_commit": "b1c6d08",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Left the parked delivery out.",
  "order": 1
 },
 {
  "scenario": "burndown-resumes-time-parks",
  "date": "2026-10-18",
  "skill_commit": "a25494c",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial (2/2)",
  "phase": "first change",
  "note": "Resumed first; label not restored.",
  "order": 2
 },
 {
  "scenario": "burndown-resumes-time-parks",
  "date": "2026-10-18",
  "skill_commit": "6f52632",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "start-and-park-when-it-will-not-fit",
  "date": "2026-10-18",
  "skill_commit": "b1c6d08",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Started; no deadline in the handoff.",
  "order": 1
 },
 {
  "scenario": "start-and-park-when-it-will-not-fit",
  "date": "2026-10-18",
  "skill_commit": "a25494c",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-18",
  "skill_commit": "a25494c",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "budget-from-measured-marks",
  "date": "2026-10-18",
  "skill_commit": "a25494c",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
