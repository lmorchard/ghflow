# Issue 231: monitor the queue runner

## Resume here

- Issue: https://github.com/lmorchard/ghflow/issues/231
- Worktree: /Users/lmorchard/devel/mine/gh-project-workflow/.claude/worktrees/feat/runner-monitor
- Branch: feat/runner-monitor
- Base: origin/main at fa52c0194c9ca96cf2702b9700e2077125715a49
- Endpoint: through PR review follow-up, without merge.

## Decisions

The issue left five questions open. Settled them from the existing runner:

1. Check interval: `--monitor-interval`, default 300 seconds. A session samples on that interval and at its start and end.
2. Stop versus alert: the write identity and base CI are stop-level. Every other check records an alert and lets the runner's existing abort, retry, and park rules act. A stop-level failure stops the run.
3. Report schema: `ghflow-monitor/1`. Top-level phase, issue, step, head, CI, review, remaining minutes, counts, alerts, checks, events, and report paths. Each check has a name, phase, level, state, message, evidence, and time.
4. Placement: `scripts/monitor.py`, imported by the runner. The runner calls it; it does not become a new CLI subcommand.
5. CI and review reads: reuse the runner's `observe_issue` result at the next step. No extra GitHub read. Session health comes from the existing event stream.

## Changes

- `scripts/monitor.py`: preflight, session, post-step, phase, and final checks; JSON and Markdown reports; status line; weekend replay.
- `scripts/run_queue.py`: create the monitor, run preflight, sample sessions, record post-step checks, and include the report in the run summary.
- `scripts/test_monitor.py` and `scripts/fixtures/weekend-2026-11-21.json`: unit tests and the weekend replay.
- `scripts/test_run_queue.py`: integration test for report files and the status line.
- `docs/setup.md`, `references/tasks/burndown-ready-queue.md`, `docs/research/queue-runner.md`: document the report and the new flags.

## Evidence

- `python3 -m unittest discover -s scripts`: 258 tests pass (before the final docs edit).
- `make check`: passed at the commit before the rebase.
- Replay: `test_replay_reproduces_the_findings_the_coordinator_made_by_hand` asserts the stale facts, #1707 missing CI, #1755 and #1759 drafts, #1379 not started, and the 1.15 to 1.90 hour throughput regression.
- Limits: no live queue run exercises the monitor. The tests use fake GitHub reads and fake sessions.

## Remaining

- Rebase onto current `origin/main`.
- Rerun `make check`.
- Same-model self-review in this session, then publish and mark ready.
