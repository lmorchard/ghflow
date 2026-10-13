# Unattended Ready-queue burndown on the local model, 2026-10-12 to 2026-10-13

This record covers the first live unattended run of [burndown-ready-queue](../../../references/tasks/burndown-ready-queue.md) on the local Qwen model, with the skill text at `694e7f7`, after PRs #84 through #88 merged: reviewer notes as notes, the one-line worker reply to a placeholder prompt, the unattended decision and parking rules, the launcher script, and the session export script. It is the first run with more than one issue, the first with a time budget, and the first with nobody watching the agent. Les launched it at 18:04 and went to bed. The parent session watched the log and the subject repository and wrote this record from the exported sessions.

## Setup

In the afternoon a ghflow subagent audited board 6 of `lmorchard/decafclaw` under [curate-ready-queue](../../../references/tasks/curate-ready-queue.md) and proposed small Python issues with settled scope. Les chose #142, #688, and #1006, set them to P1, and moved #24, #149, and #931 back to Backlog. A second subagent made the board changes under the MokaGnome identity. The curation audit found gaps in the curate task text, listed under [Candidate changes](#candidate-changes).

Les ran `scripts/unattended-burndown.sh --owner lmorchard --project 6 --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception` from the decafclaw checkout. The first launch at 17:58 failed: the script passed the whole `SKILL.md` as the message, and its `---` frontmatter line made `opencode run` print its help and exit. PR #88 strips the frontmatter and reports the exit status. The second launch at 18:04 worked. The model was `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on a llama server with four slots and no other workload. The deadline in the request was 02:04.

Sources: the eight session exports and the launcher log, copied to `~/.local/share/ghflow-trials/2026-10-13-unattended-burndown/` on Les's laptop and not committed. `scripts/export-opencode-sessions.py` wrote them from the coordinator session `ses_ecd3623edffex4SlEr4mFAQBlO`. The exports carry per-turn durations and token counts. The parent also kept a live watch on the log, the decafclaw worktrees, and the bot's PRs during the run.

## Result

Two of three issues reached the endpoint and the third was parked at the deadline. The run made 11 task calls over 8 hours and 57 minutes and ended with a delivery summary table. No question tool call, no halt, and no merge.

| Issue | PR and head | Review | Board | Outcome |
| --- | --- | --- | --- | --- |
| #142 `mcp_get_prompt` arguments as object | [#1065](https://github.com/lmorchard/decafclaw/pull/1065) `eec518b`, ready | approve, three notes declined | In review | endpoint, 1 h 48 min |
| #688 vault_search tag-filter empty message | [#1066](https://github.com/lmorchard/decafclaw/pull/1066) `f22ce4c`, ready | approve with one accepted note, correction, re-review approve | In review | endpoint, 3 h 06 min |
| #1006 vault_write broken wiki-link check | [#1067](https://github.com/lmorchard/decafclaw/pull/1067) `a988e5c`, draft | approve with two accepted notes, correction, re-review not run | In progress | parked under `triage:needs-input` at 02:52 |

Code sizes without notes files: #142 18 lines changed in the tool and skill doc plus 91 test lines; #688 21 code lines plus 97 test lines and one doc line; #1006 36 code lines plus 93 test lines and one doc line. Each PR carries a session notes file of 69 to 126 lines.

| | #1053 run | This run, whole | #142 | #688 | #1006 |
| --- | --- | --- | --- | --- | --- |
| Skill text | `678509e` | `694e7f7` | | | |
| Server | alone, unverified | alone | | | |
| Wall clock | 4 h 22 min | 8 h 57 min | 1 h 48 min | 3 h 06 min | 3 h 05 min to park |
| Task calls | 7, of which 6 did work | 11, all did work | 3 | 5 | 3 |
| Coordinator preparation before first dispatch | 15 min, 5 reference files | 23 min, 19 reference files | | | |
| Coordinator time between a worker's return and the next dispatch | 3 min after the final report | | 11 min before #688 | 15 min before #1006 | 12 min before the correction |
| Implementation handoff | 4,365 chars | | 6,192 chars | 7,806 chars | 8,045 chars |
| Implementation worker turns | 72 min | | 61 min | 114 min | 99 min |
| Early draft checkpoint | yes | | yes, 34 min after dispatch | yes, 48 min | yes, 40 min |
| Review | 38 min plus 14 min re-review | | 35 min | 30 min plus 16 min re-review | 28 min |
| Placeholder dispatch | yes | none in 11 calls | | | |
| Correction cycle | yes, one annotation | | no | yes, one wording note | yes, a doc line and one test |
| User decisions during the run | 3 | 0 | | | |
| Ready submission | 36 min, one `pr ready` call | | 20 min, one call | 27 min, one call | not reached |
| Notes-only commits | 3, one after ready | | 0 | 1, before review | 1, before review |
| Head moved after ready | yes, follow-up dispatch | no | no | no | |
| Workers read the project facts file | reviewer and follow-up | | implementer | implementer | none, `facts` run twice |
| Coordinator context at the end | not recorded | 167,000 tokens | 86,000 | 121,000 | 166,000 |

## Timeline

Local times come from the session timestamps. Coordinator turn durations include the time a dispatched worker ran.

| Local time | Event |
| --- | --- |
| 18:04 to 18:14 | Coordinator read 19 reference files in ten minutes: the burndown task, its six "apply throughout" shared references, the three task references the queue would need, pr-lifecycle, address-pr-review, and the CLI reference. Then the facts file, identity, `facts`, which reported the facts file present and two source files changed since it was written, the base-branch CI, and the board through `--paginate --slurp`, validated as two pages and 199 items. |
| 18:14 to 18:27 | Per-issue facts for the three issues, the clock against the deadline, a 7.8-minute turn that wrote a 5,300-token plan, a notes file in the decafclaw main checkout, and a prerequisite check for `.env` and `uv`. |
| 18:27 | #142 implementation worker dispatched with a 6,192-character handoff. Worktree, `uv sync`, board In progress, baseline tests, the change, tests, one commit, draft PR #1065 at 19:05, amend and force push, notes inside the same commit. Back at 19:16 after 61 minutes of turns. |
| 19:16 to 19:18 | Coordinator confirmed CI green from `pr-state` in two short turns. |
| 19:18 to 19:55 | Reviewer: three reference reads, 73 tests in the changed test file, two call sites traced, schema validated. Approve with three notes labeled routine. 35 minutes. |
| 19:55 to 19:59 | Coordinator declined all three notes with a reason each and resumed the implementation session for the ready step. |
| 19:59 to 20:15 | Ready step: body file, one `pr ready` call with `--expect-head`, board In review, `verify-commit --pr-head` true. Head unchanged. 20 minutes. |
| 20:15 to 20:26 | Coordinator read `vault_search` code and its tests itself for 11 minutes to scope the #688 handoff, checked the clock, and edited its notes. |
| 20:26 | #688 implementation worker dispatched with a 7,806-character handoff. Code commit at 21:12, draft PR #1066 at 21:17, notes-only commit at 21:19. Back at 21:25 after 114 minutes of turns across the whole session. |
| 21:25 to 21:33 | Coordinator confirmed CI green. The first turn after the worker's return took 7.9 minutes for 1,300 output tokens. |
| 21:35 to 22:05 | Reviewer: 166 tests, the revert check, AND semantics confirmed unchanged. Approve with a wording note for a sub-case where the query itself matches nothing, plus an optional eval question. 30 minutes. |
| 22:05 to 22:12 | Coordinator accepted the wording note as a real sub-case and declined the eval. The turn took 41 minutes in total because it included the correction worker. |
| 22:12 to 22:46 | Correction: eight lines in the tool, 41 in tests, one doc line, commit `f22ce4c`. The worker ran 34 minutes for that delta. |
| 22:47 to 23:05 | Re-review in a fresh session: approve, no outstanding findings. 16 minutes. |
| 23:05 to 23:32 | Coordinator declined the two remaining notes. Ready step: one `pr ready` call, board In review, head unchanged. PR body with "Owner's decision" and "Decisions taken unattended" sections. 27 minutes. |
| 23:32 to 23:47 | Coordinator checked the clock, 2 h 23 min left, read `backlinks.py` and `tools.py` for #1006, and edited its notes. The first turn took 8.2 minutes for 540 output tokens. |
| 23:47 | #1006 implementation worker dispatched with an 8,045-character handoff. Code commit at 00:32, draft PR #1067, notes-only commit at 00:44. Back at 00:49 after 99 minutes of turns across the session. |
| 00:49 to 00:58 | Coordinator confirmed CI green. 9.3 minutes for 730 output tokens. |
| 00:58 to 01:29 | Reviewer: five reads, self-link cases run directly against an isolated copy and found not to fire. Approve with four notes: a doc line, a self-link test, and two it called consistent or handled at ready. 28 minutes. |
| 01:29 to 01:41 | Three coordinator turns on the deadline: 35 minutes left, a correction cycle "risks missing the deadline", then recent CI durations of 2 min 06 s and 41 s, then "that makes a correction affordable". 12 minutes of deliberation. |
| 01:41 | Correction worker dispatched with 19 minutes left. Commit `a988e5c` at 02:18. Back at 02:25 after 44 minutes. |
| 02:25 to 02:36 | Coordinator confirmed the corrected head green locally and on CI, 11 minutes for 720 output tokens, then checked the clock. |
| 02:36 to 02:52 | "Past the 02:04 hard stop. #1006 was in progress at the deadline, so per the explicit budget rule I must park it." PR body rewritten with a "PARKED" section, label swapped to `triage:needs-input`, issue comment posted with the state and the two remaining steps, each write read back. Board left In progress, worktree and branch preserved. |
| 02:52 to 03:01 | `facts --issue` for all three, notes finalized, delivery summary table with the review evidence column and the parked row. |

## What held

- **The unattended rules held without a human.** No question tool call in nine hours. Reviewer notes were settled by the coordinator every time, with a reason recorded in the PR body. The two ready PRs carry a plain `Closes` line, and #1066 carries a "Decisions taken unattended" section.
- **The deadline rule held.** The coordinator checked the clock before every dispatch and after the last worker returned. It parked #1006 when it found the deadline passed, and it did not start a fourth issue.
- **The parking procedure held on first live use.** PR body section, label swap, issue comment with state and remaining steps, board left In progress, each write read back. Sixteen minutes.
- **No placeholder dispatch in 11 task calls**, including four resumes of an existing worker session. The 1053 run had one in seven calls, and the three earlier runs had one each.
- **The early draft checkpoint held three times**, 34 to 48 minutes after dispatch.
- **`pr ready` was one call** on both ready submissions, 20 and 27 minutes for the whole step against 36 in the 1053 run.
- **No notes commit after ready.** Both ready heads stayed put, so no follow-up dispatch was needed. The task-notes change from PR #84 did what it was meant to do.
- **The #688 decision comment was honored.** The worker branched as `tag-filter-empty`, changed the message, added no fallback, and the reviewer confirmed the AND semantics unchanged. The decision was in the last issue comment, not in the request.
- **The board traversal was validated** as the task asks: two pages, 199 items, project ID matched, final page `hasNextPage` false.
- **Workers used the facts file or `facts`.** The #142 and #688 implementers read the file. The #1006 implementer ran `facts` twice and did not read the file. No reviewer read it this time.

## What recurred or is new

- **The coordinator read 19 reference files before the first dispatch**, against five in the 1053 run. The burndown task text says "Apply Authorization, Evidence, Review, Board status, and Agent identity throughout" and "apply GitHub writes", which the coordinator obeyed by reading all six, then read the three task references it would dispatch, then two more. The coordinator ceremony change in PR #77 rewrote that sentence as conditions in `SKILL.md` and express-issue, not in the burndown task.
- **Coordinator turns slowed with context.** The first turn after a worker returned took 1.5 minutes at 79,000 tokens, 7.9 at 105,000, 8.2 at 121,000, 9.3 at 134,000, and 11.1 at 150,000, each for under 1,400 output tokens. Generation ran at about 11 tokens per second throughout, so the growth is prompt processing after a worker's turn displaced the coordinator's cache on the server. Over the run these turns cost about an hour. The context reached 167,000 tokens.
- **The coordinator researched code itself between issues.** It read `vault_search` and its tests for 11 minutes before dispatching #688 and `backlinks.py` and `tools.py` for 15 minutes before #1006, to write a "precise scope" into the handoff. The handoffs grew from 6,192 to 8,045 characters. The 1053 handoff was 4,365 characters and pointed to the facts file.
- **Accepted reviewer notes cost two correction cycles.** No note went to the user, which was the goal of PR #84. But the coordinator accepted one of three notes on #688 and two of four on #1006, each for a sub-case or convention the reviewer called optional, and each accepted note cost a correction worker run of 34 to 44 minutes plus a re-review. The #688 cycle added about 70 minutes. The #1006 cycle overran the deadline.
- **The deadline estimate counted CI time and nothing else.** With 35 minutes left, the coordinator measured CI at 2 minutes and judged a correction "affordable". The worker took 44 minutes for a doc line and one test, and the coordinator's own turns around it took 20 minutes. The rule to park at the deadline then worked, but a re-review and a ready step that could have finished #1006 were traded for two optional notes.
- **Notes-only commits before review recurred** on #688 and #1006, one each. They cost a CI run on markdown but did not move a reviewed head.
- **The coordinator wrote its notes file in the decafclaw main checkout**, as an untracked file under `docs/dev-sessions/`, not in a worktree or a branch.
- **`facts` reported stale sources** at the start: `AGENTS.md` and `CLAUDE.md` changed since the facts file was written. Nobody refreshed it. The stale-source scenario in PR #76 covers the signal, not what an unattended coordinator should do with it.
- **The first launch failed silently.** The launcher had been dry-run tested only. PR #88 fixed the frontmatter parse and the silent exit, and added three tests through a fake `opencode`.

## Candidate changes

1. burndown-ready-queue: rewrite "Apply ... throughout" as conditions, as PR #77 did for `SKILL.md` and express-issue, so the queue coordinator reads a shared reference when its condition arrives. Measure the pre-dispatch reads on the next run.
2. decisions or review-changes, unattended flow with a time budget: a reviewer note the reviewer labels optional is declined and recorded in the PR body, not corrected, unless the coordinator can show the full cycle fits: worker time, re-review, ready step, and its own turns. Alternatively, record accepted notes as follow-up items on the issue.
3. burndown-ready-queue, deadline estimate: before dispatching work near the deadline, the coordinator budgets the worker's last measured duration and its own recent turn durations, not only CI time.
4. coordination or express-issue: the queue coordinator does not read the subject code to scope a handoff. The handoff names the issue, the decisions, and the facts file, and the worker does the research. This is the 1053 handoff shape.
5. Coordinator context growth: with three issues the coordinator reached 167,000 tokens and paid about an hour in prompt processing. Options are a delegated queue coordinator per issue that relays to the parent, as the task already allows, or a shorter worker report. Measure before choosing.
6. task-notes: the coordinator's own notes go in a branch or a worktree, not as an untracked file in the main checkout.
7. prepare-project-facts and burndown: say what an unattended coordinator does when `facts` reports stale sources. The default from Les is to refresh only when stale, which was the case here.
8. curate-ready-queue, from the afternoon audit: give the board query command or link to the validated traversal in burndown; say that the user's stated criterion overrides the P0 and P1 default; name `--allow-backward` and its reason requirement for a swap back to Backlog; cover authorized Priority and Size field writes in the CLI or a shared reference, since the subagent used raw `gh project item-edit`; and have `set-status` print the item node ID.

None of these is decided.

## Evidence limits

This is one run on one queue and one model. Wall clock is from the first coordinator event to the delivery summary. Turn durations for the coordinator include dispatched worker time, so per-step coordinator costs are read from turns without a task call. The prompt-processing explanation for the slow coordinator turns comes from output token counts and a constant generation rate, not from server logs. Whether the server was unshared is Les's report, not a measurement. Review times are for same-model reviews under the approved exception. The parent read the exports with scripts and the PRs directly, and no independent reviewer checked this record.
