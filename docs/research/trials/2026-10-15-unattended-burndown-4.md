# Fourth unattended Ready-queue burndown on the local model, 2026-10-15

This record covers the fourth live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, at skills `f7f075f`. It is the first run after PRs #113 through #115 from the [third burndown record](2026-10-15-unattended-burndown-3.md): conditional reads for the worker tasks, size-first ordering and lockfile-aware estimates, and attended curation. It is also the first run on OpenCode 2.0.29, which was installed earlier that day.

## Curation

The OpenCode curation used the short request "for tonight's unattended burndown, two or three issues". It made no board change before Les approved, which held the attended-curation rule from #115. It stayed in P1 and presented all 21 P0/P1 Backlog items in the per-condition table. It proposed Size values and stated the burndown order from the burndown's own sort. Its rejections cited real gates. It named one oversized issue as an optional last pick and recommended leaving it out. Les approved #165 (XS), #164 (S), and #929 (M). He then merged the facts refresh #1075 and #1076 before launch, and #1077 one minute before launch, against the parent's advice to hold it.

## Setup

Les launched `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout at 12:40. The deadline was 20:40. Workers branched from `origin/main` at `9173771`, which includes #1077's npm policy gate in `make check`.

Sources: the seven session exports and the launcher log in `~/.local/share/ghflow-trials/2026-10-15-unattended-burndown-4/` on Les's laptop, not committed. `scripts/export-opencode-sessions.py` wrote them after PR #116 taught it the OpenCode 2.x commands and schema, starting from coordinator session `ses_ebeeb9b9effe4BNzjnpVjd3N3D`.

## Result

All three issues reached ready, in the size order. The run made 9 dispatches in 8 hours 13 minutes. There was no park, no halt, no question tool call, and no merge.

| Issue | PR and head | Size | Review | Dispatch to endpoint |
| --- | --- | --- | --- | --- |
| #165 type hints | [#1079](https://github.com/lmorchard/decafclaw/pull/1079) `7c24b7b` | 122 / 17 | approve, no actionable findings | 1 h 44 min |
| #164 exception handling | [#1080](https://github.com/lmorchard/decafclaw/pull/1080) `f692135` | 291 / 14 | approve, two routine notes | 3 h 18 min |
| #929 skill shutdown | [#1081](https://github.com/lmorchard/decafclaw/pull/1081) `eb14c24` | 453 / 1 | approve, four routine notes | 2 h 46 min, ready at 20:47 |

Each PR records its unattended decisions: four for #165, five for #164, and three for #929. One of #164's is how it handled the target that no longer exists.

| | Run 2 | Run 3 | Run 4 |
| --- | --- | --- | --- |
| Skill text | `1faac0b` | `cb5d864` | `f7f075f` |
| OpenCode | 1.x | 1.x | 2.0.29 |
| Issues at the endpoint | 3 of 3 | 2 of 3 | 3 of 3 |
| Wall clock | 8 h 16 min | 8 h 18 min | 8 h 13 min |
| Dispatches | 10 | 10 | 9 |
| Coordinator reference reads | 9 | 12 | 9 |
| Worker reference reads before the worktree | not counted | 11, 5, 10 | 4, 10, 3 |
| Coordinator context at the end | 97,000 tokens | 116,000 | 102,000 |
| Facts refresh | hash-only PR | hash-only PR | none, see below |
| Workers recording the configured default model | 3 of 3 | 0 of 3 | 0 of 3 |
| Notes amends or force pushes | 4 | 0 | 0 |
| End time in the summary | fabricated | from a clock read | from a clock read, "ended 20:49" |

## Timeline

Local times come from session timestamps and the parent's one-minute polls.

| Local time | Event |
| --- | --- |
| 12:40 to 12:53 | Coordinator read nine references, ran the traversal, `git fetch`, and `facts`, and selected #165, #164, #929 by Size. No facts refresh: `facts` reported no stale source. |
| 12:53 to 14:37 | #165: implementation 53 minutes, with four references before its worktree, which it created after 2 minutes. Three code commits and one notes commit, then review 29 minutes, then ready 19 minutes. |
| 14:39 to 17:57 | #164: implementation 1 h 35 min, with ten references before its worktree. Two code commits and two notes-only commits, the second pushed after the draft was published. Review 55 minutes. A 14-minute coordinator turn at 17:10, then ready 33 minutes. |
| 17:12 to 17:22 | The coordinator read the clock, found its notes' time estimate behind, and measured actual durations from PR and commit timestamps. It read #1079's ready time from `updatedAt`, which gave 15:52 instead of the 14:34 the parent's poll saw. The error made its estimate more cautious. |
| 18:02 to 20:48 | #929: dispatched at 17:58 with 2 h 42 min left and "explicit time-budget instructions". The coordinator read the parking procedure first. Implementation 1 h 22 min with three references before its worktree, review 61 minutes, then the ready step dispatched at 20:29 and finished at 20:48. |
| 20:49 to 20:53 | Summary from a clock read. It named the #929 ready sequence as the one step that finished after the deadline, dispatched before it. |

## What held

- **Size-first order held.** XS, then S, then M, and the largest issue was the one the deadline approached.
- **Curation stayed attended and in P1, and proposed sizes,** on the local model, with the short request.
- **Worker reads fell for two of three workers.** The #165 and #929 workers read three or four references before the worktree, the ones whose conditions applied. The #165 worker reached its worktree in 2 minutes.
- **The deadline rules held.** The last ready step was dispatched before the deadline and allowed to finish, nothing was dispatched after it, and the summary said so with clock-read times.
- **Self-reported model identity held** with no configured default, for the second run in a row.
- **No notes amends or force pushes.**
- **#1077's new gate did not break the worktrees.** `make check` passed in all three.
- **Unattended decisions were recorded in each PR,** including #164's stale target.

## What recurred or is new

- **One worker still read ten references before starting.** The #164 worker read Task notes, Decisions, Evidence, GitHub writes, pr-lifecycle, Working context, and submit-pr before its worktree. The conditional text helps, but it does not bind every sample.
- **`facts` did not see that the gates changed.** #1077 changed the Makefile on `origin/main` a minute before launch. `facts` compares the facts file against the working copy, which Les had pulled before that merge, so it reported no stale source. The burndown fetches but does not pull, so no refresh ran even though the gates changed.
- **The coordinator measured a duration from the wrong field.** It used `updatedAt` as the ready time. The rule to estimate from measured durations held, but nothing says which timestamps are durations.
- **A notes-only commit after draft publication.** The #164 worker pushed a second notes commit only to record that the draft was published. It came before review, so it moved no reviewed head, but it restarted CI.
- **OpenCode 2.0.29 changed the tools under the run.** The export command, the dispatch tool name, and the export schema changed, which broke the export script until #116. `facts` runtime detection, the "nested dispatch false" fact, and the scenario runner's OpenCode mode are still unverified on 2.x.
- **Sizes ran above the estimates again,** by about one size step each: #165 at 122 / 17 against an XS estimate of 25 to 40 lines, #164 at 291 / 14 against 100 to 170, and #929 at 453 / 1 against 180 to 270. The counts include tests and notes. The order still came out right, because each estimate grew by about the same factor.

## Candidate changes

1. `facts`: compare the facts file's recorded hashes against `origin`'s default branch, not only the working copy, or report both. Otherwise a merge just before launch hides a gate change.
2. task-notes or submit-pr: the draft publication is not the end of an operation for notes purposes. Record publication in the notes at the next code commit or at the end of the implementation operation.
3. burndown time estimates: name the evidence for durations, such as task start and return times in the coordinator's own session or notes, and not a PR's `updatedAt`.
4. OpenCode 2.x: re-verify `facts` runtime detection and nested dispatch, and update the scenario runner's OpenCode mode before the next local-model scenario run.
5. Curation size estimates: compare the estimates with the actual PR sizes over the four runs and recalibrate, or estimate from comparable merged PRs.

None of these is decided.

## Evidence limits

This is one run on one queue and one model, on a different OpenCode major version than the earlier runs. The four runs used different issues, so per-issue times are not like-for-like. Reference-read counts before the worktree come from the exports and count reads under `references/`. The parent read the exports with scripts and the PRs directly, and no independent reviewer checked this record.
