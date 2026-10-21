# Foreground dispatch for queue workers, decision samples, 2026-10-20

The seventh burndown ended after 43 minutes. OpenCode 2.0.32, installed by auto-update on 2026-10-19, added a `background` option to its `subagent` tool. The coordinator dispatched the facts refresh with `background: true`, prepared the next issues, and ended its turn to wait for the promised notification; in `opencode run`, the run ended and the worker with it. Coordination and the burndown now require foreground dispatch for workers whose result decides the next step and forbid ending the turn on a running worker. One new scenario covers the case; one regression covers the facts refresh. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-20-foreground-dispatch-answers.txt) preserve the graded output.

## Source and method

The changed commit is `70d154e` on branch `foreground-dispatch`. The baseline commit is `19d6aee` on the local scratch branch `baseline-foreground-dispatch`, which holds `main` plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner and the local Qwen model under the OpenCode 2.0.32 runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| burndown-foreground-dispatch | old text | claude-sonnet-5-5 | `19d6aee` | `9b4d97db-2acc-47c2-b864-2a42ab63f44a` | Fail |
| burndown-foreground-dispatch | new text | claude-sonnet-5-5 | `70d154e` | `e2464335-1aa6-4b30-a939-46f287678bdf` | Pass |
| burndown-foreground-dispatch | new text | claude-sonnet-5-5 | `70d154e` | `200e297a-b688-4a6b-b3f6-4bb6095c4cd2` | Pass |
| burndown-foreground-dispatch | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `19d6aee` | `ses_ea37c3210ffe83FIQRn4Ab27U1` | Pass |
| burndown-foreground-dispatch | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `70d154e` | `ses_ea35a684fffeBKyDazd33tEvQ1` | Pass |
| burndown-refreshes-stale-facts | regression | claude-sonnet-5-5 | `70d154e` | `1fb86d6c-e605-4ab3-9a49-7ae9123d821d` | Pass |

On the old text, Sonnet kept issue work waiting for the refresh but allowed dispatching it "in the background if I like", which the scenario does not accept. Qwen chose foreground dispatch on both texts when asked directly, although the live coordinator chose background; a single framed question does not reproduce the live choice, which came while the coordinator saw useful waiting work. On the new text, every answer cited the foreground rule.

## Limits

No live run has used the rule. The grades are the author's.

## Checks

`make check` passed on `70d154e`.

```scenario-results
[
 {
  "scenario": "burndown-foreground-dispatch",
  "date": "2026-10-20",
  "skill_commit": "19d6aee",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Allowed background dispatch.",
  "order": 1
 },
 {
  "scenario": "burndown-foreground-dispatch",
  "date": "2026-10-20",
  "skill_commit": "70d154e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "burndown-foreground-dispatch",
  "date": "2026-10-20",
  "skill_commit": "19d6aee",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "old text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "burndown-foreground-dispatch",
  "date": "2026-10-20",
  "skill_commit": "70d154e",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 4
 },
 {
  "scenario": "burndown-refreshes-stale-facts",
  "date": "2026-10-20",
  "skill_commit": "70d154e",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
