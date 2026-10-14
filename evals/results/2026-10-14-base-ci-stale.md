# Stale base CI from facts, decision samples, 2026-10-14

In the [second burndown](../../docs/research/trials/2026-10-14-unattended-burndown-2.md), the first `facts` call reported green base CI on the default branch head as of the checkout's last fetch, while the real head had moved. `facts` stays read-only, so `base_ci` now reports `fetch_age_seconds` and `stale`, and the burndown's facts step fetches first and rereads when the result is stale. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-base-ci-stale-answers.txt) preserve the graded output.

## Source and method

The changed commit is `9176ab6` on branch `base-ci-stale`. The baseline commit is `7ecda11` on the local scratch branch `baseline-base-ci-stale`, which holds main plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| base-ci-stale-fetch | old text | claude-sonnet-5-5 | `7ecda11` | `0e8e5521-7606-46c5-8ad1-0790219caaec` | Fail |
| base-ci-stale-fetch | new text | claude-sonnet-5-5 | `9176ab6` | `b25ea2a0-8af8-47be-b74e-9579fe186f98` | Pass |
| base-ci-stale-fetch | new text | claude-sonnet-5-5 | `9176ab6` | `3281424b-f97b-4adb-89bd-c7b8709e5b64` | Pass |
| coordinator-uses-session-facts | regression | claude-sonnet-5-5 | `9176ab6` | `dd92e8a5-234a-42d1-a35e-33a06b948339` | Pass |
| burndown-refreshes-stale-facts | regression | claude-sonnet-5-5 | `9176ab6` | `090bcb72-14ba-4206-b022-31fa13e73894` | Pass |

The old-text answer treated the green summary as current and continued without fetching, although the situation gives an eight-hour-old fetch. The new-text answers fetched, reread `facts`, and used the new result for the halt check. Both regressions passed.

## Limits

The ten-minute threshold is the author's choice. A live read against decafclaw reported `stale: true` with a fetch about eight and a half hours old. No Qwen sample ran. The grades are the author's.

## Checks

`make check` passed on `9176ab6`, including a new test for the stale flag.

```scenario-results
[
 {
  "scenario": "base-ci-stale-fetch",
  "date": "2026-10-14",
  "skill_commit": "7ecda11",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Treated the last-fetched green as current.",
  "order": 1
 },
 {
  "scenario": "base-ci-stale-fetch",
  "date": "2026-10-14",
  "skill_commit": "9176ab6",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "coordinator-uses-session-facts",
  "date": "2026-10-14",
  "skill_commit": "9176ab6",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "burndown-refreshes-stale-facts",
  "date": "2026-10-14",
  "skill_commit": "9176ab6",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
