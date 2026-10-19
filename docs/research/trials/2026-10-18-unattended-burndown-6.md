# Sixth unattended Ready-queue burndown on the local model, 2026-10-18

This record covers the sixth live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, at skills `1d93227`. It is the first run after PR #125, which acted on the [fifth burndown record](2026-10-17-unattended-burndown-5.md): `handoff prepare-project-facts`, handoff defaults, the board guard for draft PRs, the implement-issue rule for non-gate checks, and conditional reads for the coordinator. The run ended early when the OpenCode client exited with status 1.

## Curation

The OpenCode curation used the short request "for tonight's unattended burndown, two or three issues". It asked for approval with the question tool at 16:24 and moved #24 to Ready at 18:57, after the answer, through a subagent and `board set-status`. A board poll from 15:58 to 17:28 saw no change. #994 was already in Ready from run 5. Curation proposed #962 as an optional third pick and said it fit all four conditions; the run 5 curation had rejected it because its acceptance includes a live Mattermost check. Les did not add it.

## Setup

Les launched `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout at 14:31. The deadline was 22:31. Workers branched from `origin/main` at `288fa05`. The facts file was current on `origin`, so no refresh ran. OpenCode was 2.0.29.

Sources: the four session exports and the launcher log in `~/.local/share/ghflow-trials/2026-10-18-unattended-burndown-6/` on Les's laptop, not committed, exported from coordinator session `ses_eaf13036affeAOo2sqDQjJbXyP` after the exit; the coordinator's `budget.jsonl`; `~/.local/share/opencode/log/opencode.log`; and the macOS power log. Figures come from `scripts/trial_stats.py`.

## Result

#24 reached ready after one correction cycle. #994 was started at 20:49 and was in implementation when the OpenCode client exited at 21:56:14 with status 1, 35 minutes before the deadline. The coordinator wrote no summary and parked nothing. There was no question tool call, no halt, and no merge.

| Issue | PR and head | Size | Review | Outcome |
| --- | --- | --- | --- | --- |
| #24 system prompt as a living document | [#1084](https://github.com/lmorchard/decafclaw/pull/1084) `a9fd683`, ready | 1,123 / 22, 15 files | one actionable defect, corrected; re-review favorable | In review, 5 h 52 min from dispatch |
| #994 memory cap for subagent children | none | | | In progress with a notes file only, after the client exit |

The review defect was real. The recovery handler read the section from a `section` key, but persistence saved it under `path`, so every approval restored after a restart was cancelled and its update lost. The reviewer showed it with a round-trip test; the committed recovery test had passed because it built its input by hand in a shape the code never produces.

| | Run 4 | Run 5 | Run 6 |
| --- | --- | --- | --- |
| Skill text | `f7f075f` | `2a912ac` | `1d93227` |
| Issues at the endpoint | 3 of 3 | 1 of 2 | 1 of 2, one cut off |
| Wall clock | 8 h 13 min | 7 h 23 min | 7 h 25 min, client exit |
| Dispatches | 9 | 6 | 6 |
| Coordinator reference reads | 9 | 14 | 9 |
| Coordinator output tokens | 39,463 | 43,382 | 34,548 |
| Coordinator largest context, tokens | 102,000 | 108,000 | 112,000 |
| Dispatch prompt length, characters | 2,192 to 5,296 | 292 to 514 | 282 to 363 |
| Implementer largest context, tokens | 111,000 to 157,000 | 235,000 | 234,000 |
| Actionable review findings | 0 | 0 | 1 |
| Notes amends or force pushes | 0 | 0 | 0 |

## Timeline

Local times come from session timestamps and the `budget` log.

| Local time | Event |
| --- | --- |
| 14:31 to 14:48 | Coordinator read 9 references, checked identity, ran `queue select` and `facts`, found the facts current, recorded the deadline, and dispatched #24 from a `handoff implement-issue` file. |
| 14:48 to 17:19 | #24 implementation. The worker ran the new eval cases once at 16:43; they failed with "All connection attempts failed", and it committed at 16:51 and recorded the eval as not executed. Draft #1084 with 25 new tests and green CI. |
| 17:27 to 18:18 | Review: one actionable defect, shown by a round-trip test. The coordinator had not marked the review's start, so `budget` could not measure it; it noted the gap. |
| 18:24 to 19:47 | Correction, 85 minutes, then `a9fd683` pushed. |
| 19:50 to 20:13 | Re-review, favorable. The reviewer reran its reproduction. |
| 20:17 to 20:40 | Ready step with `pr ready`, which moved the board to In review. |
| 20:40 to 20:49 | The coordinator read #994, checked base CI, and dispatched its implementation with 102 minutes left. It did not run `budget --need`; its notes cite only the rule not to start an issue after the deadline. |
| 20:49 to 21:56 | #994 implementation, in research and notes, no commit. |
| 21:56:14 | The OpenCode client exited with status 1. The #994 worker's step ended with "Step interrupted", and the coordinator's dispatch call with "Tool execution interrupted". The run log has no stderr line, and `opencode.log` has no error, only the run's location evicted after its event stream closed. The power log shows no sleep; `caffeinate` ended because its child exited. |

## What held

- **The non-gate rule held in its first live test.** The worker tried the eval once, recorded the environment failure as an evidence limit, and moved on in 8 minutes, against about 70 minutes in run 5.
- **Local review caught a data-loss defect** by running the code, and the correction cycle fixed it before ready.
- **Coordinator reads fell back to 9** and its output to 34,548 tokens, the lowest of the six runs. Dispatch prompts stayed under 365 characters.
- **`budget` measured the correction, re-review, and ready step,** and each estimate before those dispatches came from the run's marks.
- **No facts refresh was dispatched,** because the `origin` check found the file current.
- **No board rule violation, no notes amends or force pushes,** and the implementer used `worktree create`, `pr body`, and `pr ready`; the reviewer used `review prepare` and `review cleanup`.

## What recurred or is new

- **The OpenCode client exited with status 1 and no error.** The cause is not in any local log. The exit left #994 In progress with no PR and no park, and no summary.
- **The coordinator started an issue that did not fit.** With 102 minutes left and a measured implementation of 158 minutes, it dispatched #994 without `budget --need`. The run 5 coordinator held the same issue after `--need`. The text asks for an estimate before dispatching work, but its example is a correction, and the deadline rule only forbids starting after the deadline.
- **A missed start mark left the first review unmeasured.** Each span needs a separate start and end call.
- **Size estimates missed by a factor of four.** Curation estimated #24 at 200 to 280 lines; the PR is 1,123 / 22, mostly tests and docs.
- **Implementer context reached 234,000 tokens of 262,144 for the second run in a row.** One session carries implementation, correction, and the ready step.
- **Curation contradicted an earlier curation** on #962's fit without naming the change.

## Candidate changes

1. Burndown: before starting a new issue under a time budget, run `budget --need implement,review,ready`. Whether to start an issue that does not fit, so that a park preserves progress, or to hold it in Ready, is a decision for Les.
2. `budget --next KIND:ID`: end the open span and start the next in one call, so a missed mark cannot leave a span unmeasured.
3. Launcher: when the agent exits non-zero, print the board's In progress items with `queue select --status "In progress"`, so the morning shows work that nothing parked.
4. Curation size estimates: estimate from comparable merged PRs, counting tests and docs, as run 4's record also proposed.
5. Implementer context: consider a fresh session for a correction after a long implementation, with the handoff carrying the finding and the head.

None of these is decided.

## Evidence limits

This is one run on one queue and one model. The client exit has no recorded cause, and the record cannot say whether it would recur. Only one issue reached the endpoint, so per-issue figures are one sample. The parent read the exports with `trial_stats.py` and scripts and read the PR directly, and no independent reviewer checked this record.
