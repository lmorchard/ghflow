# Session facts from the CLI, decision samples, 2026-10-13

`facts` now reports `base_ci`, `runtime`, and `skill_source`, so coordinators no longer rediscover them with `gh run list`, reads of the OpenCode configuration, and `git` in the skill checkout, as they did in the [unattended burndown](../../docs/research/trials/2026-10-13-unattended-burndown.md). One new scenario gives a coordinator that output and a plan to run the old commands. It ran on Claude Sonnet once against the old text and twice against the new text. Two regressions ran once. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-13-session-facts-answers.txt) preserve the graded output.

## Source and method

The changed commit is `ca2ea3e` on branch `facts-runtime`. The baseline commit is `f517490` on the local scratch branch `baseline-facts-runtime`, which holds main at `1dca824` plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner. The local server was serving the #1006 run, so no Qwen samples ran.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| coordinator-uses-session-facts | old text | claude-sonnet-5-5 | `f517490` | `33a2022c-a24e-4906-85fa-f6f60c93d65b` | Pass |
| coordinator-uses-session-facts | new text | claude-sonnet-5-5 | `ca2ea3e` | `9a87b7dc-221d-4ff9-8b0c-daded3cb11c7` | Pass |
| coordinator-uses-session-facts | new text | claude-sonnet-5-5 | `ca2ea3e` | `192beea9-416c-4eea-9fcf-965a531e0cc0` | Pass |
| burndown-refreshes-stale-facts | regression | claude-sonnet-5-5 | `ca2ea3e` | `2ce0afdb-dbe4-4861-b9b4-10fd08c8cb4e` | Pass |
| handoff-points-to-project-facts | regression | claude-sonnet-5-5 | `ca2ea3e` | `c3cff570-43bc-4647-aa6c-7241bf117175` | Pass |

The baseline also skipped the three commands and coordinated each issue itself. The situation supplies the output, and #93's text on main already covers the no-nesting path. So the scenario does not separate old text from new on Sonnet. The new-text answers cited the new burndown paragraph and put `1dca824` on the handoff's source line. No answer treated the configured default model as the workers' model. No answer said to record each worker's model from its dispatch result either. That rule is in PR #95, which this branch does not contain, so the grades rest on the listed failures.

## Limits

The CLI parts have unit tests and one live read against decafclaw and the installed skill clone. That read reported green base CI, OpenCode detected with nested dispatch false, and the skill clone up to date. OpenCode detection rests on the variables observed on a child process of a running OpenCode session. Claude Code detection rests on `CLAUDECODE=1` in this session. Codex is not detected. The grades are the author's.

## Checks

`make check` passed on `ca2ea3e`, including eleven new CLI tests.

```scenario-results
[
 {
  "scenario": "coordinator-uses-session-facts",
  "date": "2026-10-13",
  "skill_commit": "f517490",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "The situation supplies the output; #93 covers the no-nesting path.",
  "order": 1
 },
 {
  "scenario": "coordinator-uses-session-facts",
  "date": "2026-10-13",
  "skill_commit": "ca2ea3e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "burndown-refreshes-stale-facts",
  "date": "2026-10-13",
  "skill_commit": "ca2ea3e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "handoff-points-to-project-facts",
  "date": "2026-10-13",
  "skill_commit": "ca2ea3e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
