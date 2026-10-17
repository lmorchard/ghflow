# Fifth unattended Ready-queue burndown on the local model, 2026-10-16 to 2026-10-17

This record covers the fifth live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, at skills `2a912ac`. It is the first run after PRs #118 through #122, which moved repeated procedures into the CLI: `facts` staleness against `origin`, `worktree create`, `pr body`, `handoff`, `review prepare` and `review cleanup`, `park`, `queue select` and `queue summary`, `budget`, and `scripts/trial_stats.py`. The question was whether those commands are used and whether they cut model output.

## Curation

The OpenCode curation used the short request "for tonight's unattended burndown, two or three issues". It made no board write before approval: a one-minute poll of the board during curation saw no move to Ready, and the session export has no board write. It read all 18 P0/P1 Backlog candidates, found the facts file stale from the gate line, flagged #930 as In review with its PR merged, and said that the pool was thin. Les approved #1049 (S) and #994 (M, the optional last pick) and set both to P1.

## Setup

Les launched `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout at 23:42. The deadline was 07:42. Workers branched from `origin/main` at `b47262d`. OpenCode was 2.0.29.

Sources: the five session exports and the launcher log in `~/.local/share/ghflow-trials/2026-10-16-unattended-burndown-5/` on Les's laptop, not committed, exported from coordinator session `ses_eb7670cb8ffepaNqiYmkig4QPb` after it ended. The figures below come from `scripts/trial_stats.py` on that directory and from the coordinator's `budget.jsonl`. The parent also polled the board, the worktrees, and the bot's PRs every minute.

## Result

One issue reached ready. The second was not started because it did not fit the remaining time, and a facts refresh ran first. The run made 6 dispatches in 7 hours 23 minutes and ended 40 minutes before the deadline. There was no park, no halt, no question tool call, and no merge.

| Item | PR and head | Size | Review | Dispatch to endpoint |
| --- | --- | --- | --- | --- |
| facts refresh | [#1082](https://github.com/lmorchard/decafclaw/pull/1082) `026f9fb`, ready | 13 / 15 | approve, two notes declined | 1 h 53 min |
| #1049 pre-emptive matcher input | [#1083](https://github.com/lmorchard/decafclaw/pull/1083) `e6a2b87`, ready | 214 / 179 | approve, three notes declined | 4 h 55 min |
| #994 memory cap for subagent children | none | | | not started; stays in Ready |

#1083 records two decisions taken unattended: the matcher input is the raw user message only, which removes the previous-assistant continuity heuristic, and the eval ran on `gpt-4o-mini` because the default model's endpoint was not reachable.

| | Run 3 | Run 4 | Run 5 |
| --- | --- | --- | --- |
| Skill text | `cb5d864` | `f7f075f` | `2a912ac` |
| Issues at the endpoint | 2 of 3 | 3 of 3 | 1 of 2 |
| Wall clock | 8 h 18 min | 8 h 13 min | 7 h 23 min |
| Dispatches | 10 | 9 | 6 |
| Coordinator reference reads | 12 | 9 | 14 |
| Coordinator output tokens | 39,948 | 39,463 | 43,382 |
| Coordinator largest context, tokens | 121,000 | 102,000 | 108,000 |
| Dispatch prompt length, characters | 2,129 to 6,397 | 2,192 to 5,296 | 292 to 514 |
| Implementation output tokens | 32,000 to 73,000 | 39,000 to 61,000 | 130,000 |
| Review output tokens | 22,000 to 38,000 | 19,000 to 40,000 | 14,500 and 34,000 |
| Worker reference reads before the worktree | 10, 5, 11 | 4, 10, 3 | 1 |
| Notes amends or force pushes | 0 | 0 | 0 |

All token, context, and prompt figures, and the run 3 counts of references before the worktree, come from `trial_stats.py`; the largest context differs from the run 3 record's 116,000 at the end. The run 3 record gives 11, 5, 10, with the #600 and #947 counts exchanged.

## Timeline

Local times come from session timestamps and the `budget` log.

| Local time | Event |
| --- | --- |
| 23:42 to 00:03 | Coordinator read 14 references, checked identity, fetched, ran `facts`, which reported the facts file stale on `origin`, ran `queue select`, recorded the deadline with `budget`, and wrote a facts-refresh handoff by hand, because `handoff` has no prepare-project-facts operation. |
| 00:03 to 01:55 | Facts refresh. The handwritten handoff told the worker to publish a draft and not mark it ready, because a review would follow. The worker published draft #1082 at 00:45. The coordinator then dispatched a review, 49 minutes, and a ready step, 9 minutes. |
| 02:01 to 05:57 | #1049 implementation, from a `handoff implement-issue` file. The worker read one reference before its worktree but researched code for 50 minutes, and created the worktree at 02:51 with `worktree create`, which moved the board and started notes. It implemented and tested from about 02:50 to 04:30, then spent about 70 minutes on the project's real-LLM eval, which is not a gate. The default eval model's endpoint failed, and the worker switched to `gpt-4o-mini`. It committed at about 05:00 and published draft #1083 at 05:34 with `pr body`. |
| 05:53 to 06:01 | The worker moved #1049 to In review with `board set-status` while #1083 was still a draft. The coordinator found the conflict and moved it back to In progress with `--allow-backward`, citing the rule. |
| 06:02 to 06:11 | `budget --need review,ready` estimated 66 minutes against 95 left, so the coordinator dispatched the review and held #994. It added the refreshed facts path and the scope decision to the generated review handoff by hand. |
| 06:11 to 06:49 | #1049 review, 23 minutes, with `review prepare` and `review cleanup`. Ready step with `pr ready`, which moved the board to In review, 12 minutes. |
| 06:57 to 07:05 | `budget --need implement,review,ready` reported 315.5 minutes against 45 left, `fits` false. Summary with `queue summary` and a clock read, "07:02, before the 07:42 deadline". |

## What held

- **The new commands were used where the text names them.** The coordinator ran `queue select`, `budget` 12 times, `handoff` for the implementation and the review, and `queue summary`. The implementer ran `worktree create` with the board and notes options, `pr body`, and `pr ready`. The #1049 reviewer ran `review prepare` and `review cleanup`. `park` was read with `--help` but not needed.
- **`budget` decided the end of the run correctly.** Both estimates came from the run's own marks, the second held #994, and nothing used a PR timestamp.
- **Dispatch prompts fell to under 520 characters,** from 2,000 to 6,400, because each prompt named a handoff file.
- **The refresh fired from the `origin` check** on a real gate change, and every handoff named the refreshed copy.
- **The implementer read one reference before its worktree.**
- **The unattended decision rule held** for a scope reading that removed a heuristic. The PR records the question, evidence, and tradeoff.
- **The coordinator corrected a board rule violation** within the run, and the end time came from a clock read.
- **No notes amends or force pushes,** and no reads of a configured default model as an identity.

## What recurred or is new

- **A handwritten handoff added a review cycle to the facts refresh.** prepare-project-facts and the burndown both say the refresh publishes a ready PR without review. The coordinator's own handoff applied the express-issue draft, review, and ready cycle instead. The refresh took 1 h 53 min against 18 min in run 3. The cause is that `handoff` has no operation for prepare-project-facts, so the coordinator improvised.
- **A non-gate eval took about 70 minutes of the implementation.** The worker debugged an unreachable model endpoint and then ran the eval on a paid cloud model. The eval does not gate the change. The implementation used 130,000 output tokens and reached a context of 235,000 tokens of a 262,144-token window.
- **The implementer moved its issue to In review while the PR was a draft.** The board rule is clear in the text; the coordinator caught it.
- **`handoff review-changes` left out the refreshed facts path and the recorded decisions,** which the coordinator added by hand.
- **Coordinator reference reads rose to 14,** with Triage labels, Authorization, and GitHub writes read before their conditions applied. Coordinator output rose to 43,000 tokens with 57 turns, against 37 turns in run 4, partly from 12 `budget` calls and several `--help` reads.
- **Sizes ran above estimates again.** #1049 was estimated at 50 to 100 lines and came to 214 / 179, which includes deleted tests and docs.

## Candidate changes

1. `handoff`: add a `prepare-project-facts` operation whose scope says to publish a ready PR with no review, as the burndown states.
2. `handoff review-changes`: carry the facts path and the decisions file into the review handoff as it does for implementation.
3. `board set-status`: refuse In review while the issue's open linked PR is a draft, and say why.
4. implement-issue: a check that is not a gate and fails because of the environment is an evidence limit to report, not a problem to debug. Do not switch a check to another model or a paid service without authorization. Whether workers may use a paid cloud model at all is a decision for Les.
5. Burndown: name the conditions for Triage labels, Authorization, and GitHub writes so that the coordinator does not read them before its first dispatch.

None of these is decided.

## Evidence limits

This is one run on one queue and one model. Only one issue was implemented, so the implementation figures are one sample, and #1049's eval detour makes it an outlier. The runs used different issues, so per-issue times are not like-for-like. The time split of the #1049 implementation comes from bucketing its tool calls by ten-minute windows and by command text. The parent read the exports with `trial_stats.py` and scripts and read the PRs directly, and no independent reviewer checked this record.
