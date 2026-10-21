# Single-coordinator guard and a start floor, decision samples, 2026-10-21

These samples check the changes from the [seventh burndown record](../../docs/research/trials/2026-10-21-unattended-burndown-7.md). The launcher now refuses to start while an "Unattended burndown" session was active in the last 30 minutes, because an OpenCode run outlives its client; it also warns on low memory or a running virtual machine and disables OpenCode's auto-update at launch. Those launcher changes have unit tests with a fake `opencode`. The burndown's start-and-park rule now needs at least 30 minutes left. One new scenario covers the floor; two regressions cover start-and-park with time left and the ready step that finishes after the deadline. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-21-run7-candidates-answers.txt) preserve the graded output.

## Source and method

The changed commit is `f00d219` on branch `run7-candidates`. The baseline commit is `769fba0` on the local scratch branch `baseline-run7-candidates`, which holds `main` plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| start-floor-thirty-minutes | old text | claude-sonnet-5-5 | `769fba0` | `f56ba351-ebd5-4302-92fd-6a9b5da31ace` | Fail |
| start-floor-thirty-minutes | new text | claude-sonnet-5-5 | `f00d219` | `abc7d9e9-d12a-4807-993b-d1008e7b56e7` | Pass |
| start-floor-thirty-minutes | new text | claude-sonnet-5-5 | `f00d219` | `d229166d-1243-40b1-8fe5-bd58b0d29860` | Pass |
| start-and-park-when-it-will-not-fit | regression | claude-sonnet-5-5 | `f00d219` | `89f376df-e301-4bb9-9483-e174eb839fd7` | Pass |
| deadline-ready-step-finishes | regression | claude-sonnet-5-5 | `f00d219` | `89df8f78-d8ff-4c15-ad17-dbbf99087126` | Pass |

The old text started #1093 with 8 minutes left, as the seventh run did. Both new-text answers declined to start it and recorded the floor. With 111 minutes left, the start-and-park regression still starts the issue with the deadline in its handoff.

## Limits

The launcher guard ran against OpenCode's real session list on Les's laptop, read-only, and matched both seventh-run sessions in a widened window; it has not blocked a real launch. The grades are the author's.

## Checks

`make check` passed on `f00d219`.

```scenario-results
[
 {
  "scenario": "start-floor-thirty-minutes",
  "date": "2026-10-21",
  "skill_commit": "769fba0",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Started with 8 minutes left.",
  "order": 1
 },
 {
  "scenario": "start-floor-thirty-minutes",
  "date": "2026-10-21",
  "skill_commit": "f00d219",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "start-and-park-when-it-will-not-fit",
  "date": "2026-10-21",
  "skill_commit": "f00d219",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-21",
  "skill_commit": "f00d219",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
