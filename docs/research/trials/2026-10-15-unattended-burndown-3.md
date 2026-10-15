# Third unattended Ready-queue burndown on the local model, 2026-10-14 to 2026-10-15

This record covers the third live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, at skills `cb5d864`. It is the first run after PRs #99 through #111, which came from the [second burndown record](2026-10-14-unattended-burndown-2.md) and from the curation that preceded this run:

- worker model as a runtime self-report;
- clock-read report times, local notes edits, and a started ready step that may finish;
- a stale flag on `base_ci` and a fetch before `facts`;
- the unattended-fit criterion, the thin-pool rule, and the fit table template;
- the priority-tier convention;
- `sweep-prioritize` as the promotion path.

## Curation

Curation ran in OpenCode on 2026-10-14 in three rounds. The first round used the short request that #102 made possible. It applied the fit conditions correctly for rejections, but it filled three slots with issues estimated at 100 to 350 lines, led by the two largest. It also moved them to Ready without Les's approval, although curate-ready-queue requires approval before any board change. #109 added the thin-pool rule and the table template after this round.

The second round, with a reconsideration request, produced a per-condition table, waited for approval, and proposed #947, #600, and #930. Les approved with the order #947, #600, #930. The agent then said its list was "the recorded selection order for the burndown", which was false: the burndown sorts by priority. It also offered a merge endpoint, which the launcher does not allow. Les set the three issues to P1 under the priority-tier convention that #110 records. The burndown then took them in ascending number, #600, #930, #947.

## Setup

Les launched `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout at 16:59, after pulling decafclaw main. The deadline was 00:59. The model was `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on the local llama server.

Sources: the eight session exports and the launcher log in `~/.local/share/ghflow-trials/2026-10-15-unattended-burndown-3/` on Les's laptop, not committed, written by `scripts/export-opencode-sessions.py` from coordinator session `ses_ec324f7a6ffe5beStWZLQ1oq4A`. The parent also polled the worktrees, the bot's PRs, and the log's task returns every minute during the run.

## Result

Two issues reached ready. The third was parked at the deadline with a real review finding outstanding, and a facts refresh ran first. The run made 10 task calls in 8 hours 18 minutes. There was no question tool call, no halt, and no merge.

| Issue | PR and head | Size | Review | Outcome |
| --- | --- | --- | --- | --- |
| facts refresh | [#1075](https://github.com/lmorchard/decafclaw/pull/1075) `efdb167`, ready | 2 / 2 | none required | hash-only update for `docs/config.md` |
| #600 config.json load test | [#1076](https://github.com/lmorchard/decafclaw/pull/1076) `7a59cde`, ready | 47 / 0 | approve, one note declined | In review, 1 h 44 min from dispatch |
| #930 npm install policy and pinning | [#1077](https://github.com/lmorchard/decafclaw/pull/1077) `c0cd58f`, ready | 537 / 86 | approve, five notes declined or deferred | In review, 3 h 0 min |
| #947 asyncio loop-leak guard | [#1078](https://github.com/lmorchard/decafclaw/pull/1078) `f7cb4f2`, draft | 79 / 1 | approve with one actionable finding: a committed test is vacuous | parked at 00:59 under `triage:needs-input` |

| | First run | Second run | Third run |
| --- | --- | --- | --- |
| Skill text | `694e7f7` | `1faac0b` | `cb5d864` |
| Issues at the endpoint | 2 of 3 | 3 of 3 | 2 of 3, one parked with a finding |
| Wall clock | 8 h 57 min | 8 h 16 min | 8 h 18 min |
| Task calls | 11 | 10 | 10 |
| Coordinator reference reads | 19 | 9 | 12 |
| Coordinator reads of subject code or configuration | 2 code sessions | 0 | 0 |
| Coordinator context at the end | 167,000 tokens | 97,000 | 116,000 |
| Worker reference reads per implementation | not counted | 4 to 8 | 8 to 13 |
| Workers recording the configured default model | not checked | 3 of 3 | 0 of 3 |
| Notes-only amends or force pushes | not counted | 4 | 0 |
| End time in the summary | not stated | fabricated, 23:35 for 04:24 | 01:14, from a clock read |

## Timeline

Local times come from session timestamps. A coordinator turn that contains a task call includes the worker's time.

| Local time | Event |
| --- | --- |
| 16:59 to 17:12 | Coordinator read the burndown task and its references, ran the board traversal, `git fetch origin`, and `facts`. `facts` reported `docs/config.md` stale, base CI green on `ff32a84` and not stale, OpenCode with nested dispatch false. It verified identity and wrote notes under `~/.local/state/ghflow/notes/`. |
| 17:12 to 17:31 | Facts refresh worker: PR #1075, a hash-only update, ready and unmerged. |
| 17:35 to 18:24 | #600 implementation. The worker read 13 files under the skill, including 11 references, before its worktree at about 17:53. It committed at 18:08, opened draft PR #1076 at 18:15, and reported its model as `llama.cpp/llama`. |
| 18:25 to 18:59 | #600 review: approve, no actionable findings, both identities reported as self-reports. |
| 18:59 to 19:20 | #600 ready step, one `pr ready` call. |
| 19:23 to 21:13 | #930 implementation. A new policy script, pinned `package.json` and lockfile pairs, `.npmrc` and allowlist files, and a docs page. Two plain commits at 20:58, draft PR #1077 at 21:05. |
| 21:13 to 22:00 | #930 review: approve, five notes. It verified on macOS only and relied on hosted CI for the full suite. |
| 22:02 to 22:23 | #930 ready step. Notes declined or deferred with reasons in the PR. |
| 22:30 to 23:38 | #947 implementation. Two plain commits at 23:13 and 23:21, draft PR #1078. |
| 23:38 to 00:34 | The coordinator read the clock at 23:38 and dispatched the review with 81 minutes left. The review found one actionable defect: the committed clear-before-fail test is vacuous, which the reviewer showed by mutation. 56 minutes. |
| 00:34 to 00:47 | At 00:43 the coordinator read 16 minutes left and judged that a fix, a re-review, and the ready step would not fit. It dispatched no correction. |
| 00:47 to 01:13 | Park under the time-budget procedure: a "Parked (time budget)" section in the PR and an issue comment listing the remaining steps, `triage:needs-input`, and board In progress. The park worker was dispatched at 00:47, before the deadline, and its writes landed at 01:08. |
| 01:13 to 01:17 | Summary from a clock read: "actual end 2026-10-15 01:14 PDT", naming the park record as the one sequence that finished after the deadline. |

## What held

- **Worker identity reports were self-reports.** The implementers reported `llama.cpp/llama` with no configured default in any session. The reviewers labeled both identities as self-reports.
- **Report times came from clock reads.** The coordinator ran `date` eight times, the workers ran it too, and the summary's end time matches the run.
- **No notes amends or force pushes.** Every new head was a plain commit, and both `--force` uses were review worktree removals.
- **The coordinator fetched before `facts`,** and `base_ci` was fresh.
- **The facts refresh fired on a real change,** and its PR was hash-only.
- **The deadline rules held.** The coordinator dispatched no correction it could not finish, parked #947 with its remaining steps, and named the one sequence that finished after the deadline.
- **The priority tie-break and the P1 tier held:** the selection was #600, #930, #947.
- **No coordinator reads of subject code or configuration.**

## What recurred or is new

- **Workers read many references before starting.** The #600 and #947 implementers each read 11 or 12 references. implement-issue opens with "Apply Authorization and Evidence throughout" and "Before changing GitHub records, apply GitHub writes", the pattern that #93 fixed for the burndown. The #600 worker took about 18 minutes from dispatch to its worktree for a two-test change.
- **The #930 size estimate was far off.** Curation estimated 120 to 200 lines, and the PR is 537 / 86. Most of the excess is lockfile churn and an 84-line docs page. The fit criterion counts lines including tests but says nothing about generated lockfiles. The issue took three hours, the longest of the night.
- **A real defect cost the third issue.** The #947 reviewer found a vacuous test, the first actionable finding in two runs. Its correction did not fit. The order had put the smallest issue last only because of issue-number tie-breaking.
- **Coordinator context grew to 116,000 tokens,** against 97,000 in the second run, with three more reference reads and the park. The turns between dispatches stayed short.
- **The curation agent skipped the approval gate once,** claimed a false burndown order, and offered a merge endpoint. The approval gate and the burndown's ordering are both in the text, and no CLI guard exists.

## Candidate changes

1. implement-issue, submit-pr, and review-changes: rewrite each "Apply ... throughout" opening as conditions, as #77 and #93 did for the coordinators. Count the worker's reads on the next run.
2. curate-ready-queue, unattended fit: estimate size excluding generated lockfiles and vendored files, and flag an issue whose change regenerates lockfiles as likely to run long.
3. burndown or curation: order the selection so the smallest fitting issue runs first within a priority. One option is that curation proposes Size values for Les to set, and the burndown breaks ties by Size before issue number.
4. curate-ready-queue: restate in the procedure's own step that no board write happens before the user approves, since one curation skipped it. If it recurs, consider a CLI guard.
5. Reports from curation: a claim about another task's behavior, such as the burndown's order, must come from that task's text, not from the curator's plan.

None of these is decided.

## Evidence limits

This is one run on one queue and one model. The three runs used different issues, so per-issue times are not like-for-like. The coordinator's turn durations include worker time where a turn holds a task call. Worktree and PR times come from one-minute polls. The parent read the exports with scripts and the PRs directly, and no independent reviewer checked this record.
