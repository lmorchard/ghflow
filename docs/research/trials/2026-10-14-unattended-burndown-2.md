# Second unattended Ready-queue burndown on the local model, 2026-10-13 to 2026-10-14

This record covers the second live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, with the skill text at `1faac0b`. It is the first run after PRs #90 through #97, which came from the [first burndown record](2026-10-13-unattended-burndown.md): the facts refresh step, coordinator notes outside the checkout, the curation gaps and `board set-field`, conditional reads and no code research for the queue coordinator, the time-budget estimate, model identity under the same-model waiver, the session facts in `facts`, and the OpenCode permission snippet. The question was whether those changes shortened coordinator work and let a third issue finish.

## Setup

An OpenCode session curated the Ready column in the afternoon with a request that spelled out an unattended-fit criterion. Les approved #27, #90, and #540 and set them to P1. Les launched `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout at 20:09. The deadline in the request was 04:09. The model was `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on the local llama server with no other workload.

Sources: the eight session exports and the launcher log in `~/.local/share/ghflow-trials/2026-10-14-unattended-burndown-2/` on Les's laptop, not committed, written by `scripts/export-opencode-sessions.py` from coordinator session `ses_ec79d11b9ffeXvt2we0lSPLf7X`. The parent also polled the log, the worktrees, and the bot's PRs during the run.

## Result

All three issues reached the endpoint, and a facts refresh PR was published first. The run made 10 task calls in 8 hours 16 minutes and ended with a delivery summary table. There was no question tool call, no park, no halt, and no merge.

| Issue | PR and head | Review | Board | Dispatch to endpoint |
| --- | --- | --- | --- | --- |
| facts refresh | [#1068](https://github.com/lmorchard/decafclaw/pull/1068) `8d0df11`, ready | none required | - | 16 min |
| #27 Tabstack tool parameters | [#1069](https://github.com/lmorchard/decafclaw/pull/1069) `50f8d2b`, ready | approve, three notes declined | In review | 1 h 42 min |
| #90 shell confirmation reason | [#1070](https://github.com/lmorchard/decafclaw/pull/1070) `32709e2`, ready | approve, one note declined | In review | 1 h 43 min |
| #540 prune resolved errors | [#1071](https://github.com/lmorchard/decafclaw/pull/1071) `f5a1e74`, ready about 04:11 | approve, four notes declined | In review | 4 h 2 min |

PR sizes including notes files: #1069 182 / 5, #1070 173 / 3, #1071 414 / 25. #1071 carries one decision taken unattended: `cleanup.prune_resolved_errors` defaults to true, with the evidence and the tradeoff in the description.

| | First run, 2026-10-12 | Second run, 2026-10-13 |
| --- | --- | --- |
| Skill text | `694e7f7` | `1faac0b` |
| Issues at the endpoint | 2 of 3, one parked | 3 of 3 |
| Wall clock | 8 h 57 min | 8 h 16 min |
| Task calls | 11 | 10, one of them the facts refresh |
| Reference reads before the first dispatch | 19 | 9 |
| Coordinator reads of subject code | 2 sessions, 11 and 15 min | 0 |
| Coordinator reads of OpenCode configuration | 0 in this run, 3 min in the #1053 run | 0 |
| Coordinator context at the end | 167,000 tokens | 97,000 tokens |
| Coordinator time between a worker's return and the next dispatch | 11 to 15 min | 2 to 8 min |
| Placeholder dispatch | 0 | 0 |
| Correction cycles | 2 | 0 |
| Reviewer notes accepted as corrections | 3 | 0 of 8 |
| Head moved after ready | no | no |
| Facts refresh | none; stale sources ignored | one hash-only PR before the first issue |
| Coordinator notes | untracked in the main checkout | `~/.local/state/ghflow/notes/` |

## Timeline

Local times come from session timestamps. A coordinator turn that contains a task call includes the worker's time.

| Local time | Event |
| --- | --- |
| 20:09 to 20:29 | Coordinator read the burndown task and Working context, ran `facts`, which reported `AGENTS.md` and `CLAUDE.md` stale, base CI green, OpenCode with nested dispatch false, and the skill clone current. It validated the board traversal at two pages and 196 items, read identity, express-issue, Coordination, Review, Decisions, prepare-project-facts, and Task notes, checked identity with `gh api user`, read the three issues, and wrote its notes under `~/.local/state/ghflow/notes/`. Nine references in 20 minutes. |
| 20:29 to 20:45 | Facts refresh worker: hash-only update, PR #1068 opened ready, no merge. |
| 20:45 to 20:49 | Coordinator found that `origin/main` had moved since the checkout's last fetch, because Les merged #1067 before the launch, fetched, and re-checked base CI on `e3d3183`. |
| 20:49 to 21:39 | #27 implementation: commit, draft PR #1069 at 21:27, 4,544 tests. Handoff 4,677 characters, pointing at the refreshed facts copy and naming the source revision. |
| 21:39 to 22:11 | #27 review: approve, three notes. |
| 22:11 to 22:31 | Coordinator declined all three notes, because a notes-only commit would move the head. One `pr ready` call. |
| 22:31 to 23:22 | #90 implementation: commit at 23:09, amended to fold the notes in, draft PR #1070. |
| 23:22 to 23:50 | #90 review, dispatched without waiting for CI on the amended head: approve, one note about a pre-existing quirk, declined and recorded as a follow-up. |
| 23:50 to 00:14 | #90 ready. |
| 00:14 to 02:49 | #540 implementation, with one decision taken unattended in the handoff. Code commit at 02:01, docs and notes commit amended and force-pushed three times between 02:15 and 02:42 for notes edits. The worker's context reached 215,000 tokens. |
| 02:49 to 03:37 | #540 review: approve, four notes. 41 minutes. |
| 03:37 to 04:16 | Coordinator declined all four notes and dispatched the ready step with 30 minutes left. PR #1071 turned ready about 04:11 and the worker returned at 04:16. |
| 04:16 to 04:25 | `facts --issue` reads, notes, and the delivery summary. |

## What held

- **Conditional reads held.** Nine references before the first dispatch instead of 19. The coordinator confirmed the worker task paths with `ls` and did not read them.
- **The coordinator did not research subject code.** Zero subject reads in the coordinator session. The handoffs named the issue, the decisions, the refreshed facts copy, and the source revision.
- **Coordinator context stayed under 100,000 tokens** across three issues. Turns between dispatches took 2 to 8 minutes instead of 8 to 15.
- **The facts refresh step held on first use.** It ran after the traversal, published a ready hash-only PR, and every implementation and review handoff pointed at the refreshed copy.
- **`facts` replaced the ad-hoc session commands.** No `gh run list` from the coordinator, no configuration reads, and the source revision came from `skill_source`.
- **The time-budget rule held.** With 32 minutes left, the coordinator declined four optional notes and dispatched the ready step instead of a correction. All eight notes in the run were declined and recorded.
- **The unattended decision rule held** for the #540 default, recorded in the PR description with evidence and tradeoff.
- **No placeholder dispatch and no head moved after ready**, for the second run in a row.
- **The curation criterion picked issues that finished**, though #540 took twice as long as the others.

## What recurred or is new

- **The final report gave a wrong end time.** At 04:23 the coordinator wrote "RUN COMPLETE (2026-10-13 ~23:35 PDT, well before the 04:09 deadline)" in its notes and "ended ~23:35 PDT" in the summary, without running a clock command. The run ended at 04:24, and #540 turned ready a few minutes after the deadline. A report time that no command read is a fabricated fact.
- **#95's identity rule cannot be followed inside OpenCode.** OpenCode stores each worker's model in the task result's metadata, but the text the coordinator receives contains no model. The coordinator therefore reported the implementer's identity as unobservable, which is the rule's fallback. The rule's premise was wrong; the parent read the metadata from the export, not from what the agent sees.
- **Implementers recorded the configured default as their model.** All three implementation sessions mention `ollama/qwen3-coder:30b`, which is `facts` `runtime.config_default_model`, next to their own `llama.cpp/llama`. The `subagent_model_rule` text did not stop that. Reviewers reported the identity from their own system prompt.
- **Notes edits caused repeated amends and force pushes.** The #540 worker amended its docs commit three times in 27 minutes to change one or two lines of notes, and each push restarted CI. #90 amended once. The task-notes rule bans notes-only commits after review, not notes churn before it.
- **The ready step finished just past the deadline.** The coordinator dispatched it with 30 minutes left, which was a reasonable estimate from the run's 20- and 24-minute ready steps. That step took about 34 minutes. The rule says to park an issue in progress at the deadline, and nobody stopped a write sequence that was already under way.
- **`base_ci` read the last-fetched head.** The first `facts` call reported green CI on `4eaef9e`, the default branch head as of the checkout's last fetch, while the real head was `e3d3183`. The coordinator noticed and re-checked. `facts` reports `fetch_head_age_seconds`, but `base_ci` does not refer to it.
- **The largest issue needed the largest worker context.** The #540 worker reached 215,000 tokens of a 262,144-token window in 185 minutes of turns. A larger issue could exhaust it.

## Candidate changes

1. Reports: a time in a summary or notes comes from a clock command run at that point, as other facts come from evidence. The burndown summary states the actual end time and whether any step finished after the deadline.
2. review and coordination: replace #95's dispatch-metadata sentence with something the agent can do. Each handoff asks the worker to state the model ID its own runtime reports to it. The coordinator records that self-report with the limit that it is a self-report. The export or another post-run tool can confirm it from metadata.
3. implement-issue or task-notes: a worker never records a configured model as its own identity. If `facts` is kept as is, consider moving `config_default_model` out of the default output, or renaming it so it does not read as an identity.
4. task-notes: update notes in the working tree during a task and commit them once with the final code or at the end of the operation; do not amend and force-push for notes edits alone.
5. burndown deadline handling: say whether a ready step dispatched before the deadline may finish after it, or whether the coordinator parks at the deadline regardless. The first reading matches what happened and avoids half-written PR state.
6. `facts`: fetch before reading `base_ci`, or mark `base_ci` stale when `fetch_head_age_seconds` exceeds a threshold.
7. curate-ready-queue, the unattended-fit criterion agreed on 2026-10-13: write it from this run. A manual acceptance check disqualifies an issue even when unit tests exist, as the curation agent missed for #149. An estimate near the top of the size range doubled the cycle time, as #540 showed. The gate commands come from the facts file.

None of these is decided.

## Evidence limits

This is one run on one queue and one model. The comparison with the first run is between different issues, so per-issue times are not like-for-like. Turn durations for the coordinator include worker time where a turn holds a task call. The ready time of #1071 comes from a poll at one-minute intervals. Whether the server was unshared is Les's report. The parent read the exports with scripts and the PRs directly, and no independent reviewer checked this record.
