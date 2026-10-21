# Seventh unattended Ready-queue burndown on the local model, 2026-10-20 to 2026-10-21

This record covers the seventh unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model. It was the first run with start-and-park and the resume of time parks (#127), new sessions for later steps (#128), and, after a relaunch, foreground dispatch (#129). It is also the first run on OpenCode 2.0.32, which OpenCode installed by auto-update on 2026-10-19. Two coordinators ended up working the same queue.

## Setup

Les filled the Ready column by hand with eight P1 issues, mostly small web UI bugs, and set their Size with sweep-prioritize. He filed and prioritized #1096 (`make run-dev`, P0) the same evening, after #1097 replaced the facts file's "Never run" rule with a rule for running the app from a worktree without Mattermost, email, DMs, or heartbeat. Both launches used `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` on llama.cpp. Docker Desktop's VM (32 GB) ran throughout, and a TrOCR training job shared the GPU from 20:12 to about 01:20.

Sources: the session exports and launcher logs in `~/.local/share/ghflow-trials/2026-10-20-unattended-burndown-7a/` (first launch) and `-7b/` (relaunch), not committed; `~/.local/share/opencode/log/opencode.log`; the llama.cpp slot status during the night; and the parent's one-minute board, PR, and worktree polls.

## Result

| Item | PR and head | Outcome |
| --- | --- | --- |
| facts refresh | [#1098](https://github.com/lmorchard/decafclaw/pull/1098) `bd9249e`, ready | published ready with no review by the first launch; the relaunch verified and reused it |
| #1096 `make run-dev` (P0, S) | [#1102](https://github.com/lmorchard/decafclaw/pull/1102) `858038e`, draft | first launch: implemented, reviewed with no actionable findings; the ready step stalled and never marked it ready; In progress, not parked |
| #1073 entry box alignment (XS) | [#1108](https://github.com/lmorchard/decafclaw/pull/1108) `d67e507`, ready | relaunch: fixed with a Playwright browser test that fails without the fix; In review |
| #1093 theme menu offset (XS) | [#1109](https://github.com/lmorchard/decafclaw/pull/1109) `34b966c`, draft | relaunch: started 8 minutes before the deadline, one-line fix published unverified, parked with `park --kind time` |
| six other Ready issues | none | not started |

## Timeline

| Local time | Event |
| --- | --- |
| 19:44 | First launch. The coordinator wrote the refresh handoff with `handoff prepare-project-facts` and marked a `refresh` budget span. |
| 19:54 | It dispatched the refresh with the `subagent` tool's new `background: true`, which returned at once with "You will be notified automatically when it finishes". It read the first issues, wrote a status message, and ended its turn. |
| 20:27 | The `opencode run` client exited. The parent read this as the end of the run and wrote #129. |
| 20:58 to 03:44 | The first launch's session kept running on OpenCode's background service with no client: the refresh finished and the notification woke the coordinator, which dispatched #1096 at 21:09, its review at 00:07, and its ready step at 02:03, all in the background. Draft #1102 opened at 22:41. |
| 23:01 | Relaunch, with #129. Its coordinator found #1098 and #1102, reused #1098 without a new refresh, and dispatched #1073 in the foreground with `handoff --deadline`. |
| 23:58 to 04:52 | #1073's first worker wrote a browser test and the fix in `chat-input.js`. From about 02:00 three sessions shared llama.cpp's 262,144-token cache, and decode fell to about 3 tokens per 20 seconds per slot. At 04:52 the #1073 worker died with "Context size has been exceeded", and the first launch's ready worker ended the same minute with 259 output tokens in 169 minutes. |
| 05:23 to 06:50 | The relaunch resumed #1073 in a new session from the uncommitted work: draft #1108 in 25 minutes, review 38 minutes, ready 16 minutes. |
| 06:53 to 07:13 | With 7.9 minutes left and `budget --need` at 378 minutes, the coordinator started #1093 under the start-and-park rule. The worker created its worktree at 07:05, after the deadline, published the one-line fix as draft #1109 marked unverified, and returned at 07:08; the coordinator parked it at 07:13. |
| 07:20 | Relaunch client exited after its summary. |

## What held

- **Foreground dispatch held after #129.** Every relaunch dispatch lasted as long as its worker; the first launch's background dispatches returned in under half a minute.
- **The refresh went straight to a ready PR with no review,** and the relaunch reused it after checking it, without a second refresh.
- **Start-and-park and the deadline handoff worked end to end** for #1093: a draft with the change, the remaining steps in the issue and PR, and `parked` will list it first next run.
- **A new session recovered a dead worker.** After the context error, the relaunch resumed #1073 from the uncommitted worktree in 25 minutes.
- **A visual bug got a gated check.** #1073's browser test asserts that the row, textarea, and buttons share one height, and the worker showed it fails without the fix.
- **Budget decisions came from the run's marks,** and the relaunch's summary named every step that finished after the deadline.

## What recurred or is new

- **An `opencode run` session outlives its client.** The client exits when the coordinator's turn ends, but the session continues on OpenCode's background service and wakes on worker notifications. The launcher's exit is therefore not the run's end, and a relaunch put a second coordinator on the same queue.
- **Two coordinators overloaded the shared cache.** Three concurrent sessions did not fit llama.cpp's 262,144-token cache, decode collapsed, one worker died of a context error, and another stalled for nearly three hours without marking #1102 ready.
- **OpenCode changed under the trial.** Auto-update to 2.0.32 added background subagents between runs 6 and 7.
- **Start-and-park has no floor.** Starting #1093 with 8 minutes left produced an unverified one-line change and a park; a worker needs enough time to reach a first checkpoint.
- **#1096 is stranded.** Reviewed with no actionable findings, but its ready step never ran and it is not a recorded park, so no burndown will resume it.
- **The llama.cpp provider allows 262,144 output tokens,** so a looping generation has no cap.

## Candidate changes

1. Launcher: before launching, refuse if a session titled "Unattended burndown" is still active in OpenCode, and print how to stop it. Document that stopping a run means deleting its session (`opencode session delete`), not killing the client.
2. Burndown: start a new issue under a time budget only when the remaining time covers the shortest measured implementation-to-draft span in this run, or a fixed floor such as 30 minutes when none is measured.
3. Les's environment: set `"autoupdate": false` in OpenCode's config during trials, cap the llama.cpp provider's output limit, and keep Docker and GPU jobs off during a run.
4. #1096: mark #1102 ready through a submit-pr resume, or move it to a time park so the next burndown resumes it.

None of these is decided.

## Evidence limits

Two coordinators, a training job, and Docker shared the machine, so no timing here compares with earlier runs. The first launch's session ran without a client log; its timeline comes from its export. The cause of the 04:52 context error is inferred from the cache overload and the coincident end of the first launch's worker. The parent read the exports with `trial_stats.py` and scripts, and no independent reviewer checked this record.
