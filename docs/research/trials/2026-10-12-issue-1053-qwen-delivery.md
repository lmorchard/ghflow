# Issue #1053 delivery on the local model with pr ready and project facts, 2026-10-12

This record covers a delivery run of [decafclaw issue #1053](https://github.com/lmorchard/decafclaw/issues/1053) on the local Qwen model with the skill text at `678509e`, after PRs #73 through #77 merged: worker bounds, the [#1054 record](2026-10-12-issue-1054-qwen-delivery.md), `pr ready`, the project facts file and `facts`, and the coordinator ceremony changes. It is the third sample on this model and the first with the decafclaw [project facts file](https://github.com/lmorchard/decafclaw/pull/1063) in place. It is also the first run on the merged text that exercised the correction cycle, because the reviewer raised findings.

## Setup

The parent chose #1053 as a Python refactor one step larger than #1054: a new module, two call sites, and per-transport tests. Les pulled the installed skill clone to `678509e` and the decafclaw main to include the facts file, then started an OpenCode session on `llama.cpp/llama` with this request:

```text
deliver issue 1053 https://github.com/lmorchard/decafclaw/issues/1053 through PR review follow-up, without merge. Use the same local model for implementation and review under my approved exception for OpenCode with the local model on this laptop. Decisions: put the helper in a new module src/decafclaw/compaction_display.py with one function compaction_notice(success, ...) that returns the notice text; route the Mattermost compaction_end handler and interactive_terminal.py through it, keeping any transport-specific prefix such as the Mattermost emoji outside the helper; leave the web store and TUI unchanged.
```

The decision sentences settled the issue's open choice of a home for the helper. The parent asked for the llama server to be unshared this time; nobody verified that during the run. Sources: exported transcripts `session-ses_ece9-coordinator.md` (coordinator, `ses_ece9f3d25ffeE3BWCZl3BolhxH`), `session-ses_ece9.md` (implementation worker, `ses_ece91581bffeDz9DzrMTVOM0rq`), `session-ses_ece3.md` (reviewer, `ses_ece3a0453ffeZysbowR19gLiJH`), and `session-ses_ecdb.md` (follow-up worker, `ses_ecdb91e2effeoZLS2KngLJqV4l`) in the decafclaw root, not copied into this repository. The implementation export begins in the middle of a turn, after the worker had read the code, so its early reads are not in the record; its handoff is in the coordinator transcript. The exports carry per-turn durations and no token counts.

## Result

[PR #1064](https://github.com/lmorchard/decafclaw/pull/1064) ended ready for review at head `4e22f7e`, with three hosted checks passed, the issue In review, and no merge. Four code commits hold the change: 294 insertions and 43 deletions across the new module, the two transports, three test files, `docs/conversations.md`, and one line in the project's `CLAUDE.md` module list. Three notes-only commits sit between and after them. The reviewer approved the first head with three findings it labeled disputed; the coordinator returned all three to Les, who decided one annotation change, accepted the notes-only session directory, and required a plain `Closes #1053` line at ready time. The reviewer re-reviewed the one-line delta and approved. The ready submission ran as one `pr ready` call. A notes-only commit after it moved the head, so the conditional follow-up did not apply and the parent dispatched address-pr-review, which confirmed the checks on the new head.

| | #997 run | #1012 run | #1054 run | #1053 run |
| --- | --- | --- | --- | --- |
| Skill text | `ddd342e` | `62972b3` | `62972b3` | `678509e` |
| Change size | about 60 lines | 99 / 7 | 77 / 3 | 294 / 43 |
| Server | alone | shared | shared | alone, unverified |
| Wall clock | 3 h 50 min | 7 h 7 min | 4 h 39 min | 4 h 22 min |
| Task calls | 7 | 4, of which 3 did work | 4, of which 3 did work | 7, of which 6 did work |
| Coordinator preparation before first dispatch | 23 min | 27 min | 15 min, 15 reference files | 15 min, 5 reference files plus `facts --issue` and the facts file |
| Implementation handoff | - | 8,509 chars | 7,028 chars, conventions restated | 4,365 chars, pointing to the facts file |
| Coordinator work after the endpoint report | - | 6 min | 21 min, notes read and edited | 3 min, from the read-back |
| Placeholder dispatch | no | yes, new session | yes, same session | yes, same session, at the corrections step |
| Early draft checkpoint before the final commit | no | no | no | yes |
| Correction cycle | yes | no | no | yes, one annotation |
| User decisions during the run | 0 | 0 | 0 | 3, all from reviewer notes |
| Ready submission | separate dispatch | 50 min across two sessions | 30 min, twelve turns | 36 min, one `pr ready` call of 73 s inside it |
| Notes-only commits | 0 | 5 | 0 | 3 |
| Final follow-up dispatch | yes | no | no | yes, 8 min, because the last notes commit moved the head |
| Workers read the project facts file | - | - | - | reviewer and follow-up yes; implementation unknown |

## Timeline

Local times come from the session timestamps and the commit times. Worker minutes are summed turn durations.

| Local time | Event |
| --- | --- |
| 11:29 to 11:44 | Coordinator loaded the entry skill through the skill tool, and with it the user's own dev-session skill, two minutes. Read express-issue, Coordination, and Review; listed the task directory and the CLI help; read the issue; fetched; ran `facts --issue`, which reported no existing work and the facts file present; read the facts file; read Task notes and Working context. Then three minutes on the OpenCode configuration files to establish that subagents inherit the session's model, for the same-model exception. Five references in 15 minutes. |
| 11:44 | Implementation worker dispatched with a 4,365-character handoff that named the facts file, said nothing differed for this task except the five decisions, gave the branch name, the review plan, and the flow limits, and asked for a draft after the first significant checkpoint. Its early turns are not in the export; the first exported turn, 12 minutes long, plans the module, the Mattermost test seam, and the call-site changes from code it had already read. |
| 12:0x to 12:36 | Worktree, `.env` copy with a port, `uv sync`, board In progress, notes file, baseline `make test`. New module, Mattermost route, two test files, targeted tests, `make fmt`, `make lint`. Commit `602d055` at 12:36. |
| 12:42 | Identity confirmed, `gh pr list` found no PR, push, `verify-commit --on`, body file in a temporary directory, draft PR #1064. The first early draft checkpoint in these trials; the terminal route was still to do. |
| 12:42 to 13:00 | Terminal route and its tests; the worker reverted its change to see the new tests fail, and drifted the Mattermost prefix to see the pinning test fail. Commit `e86c633`. `docs/conversations.md` and the `CLAUDE.md` module list updated, commit `60f4fe0`. `make check` and `make test` run one after the other. |
| 13:00 to 13:13 | Push, description refreshed, `verify-commit`, notes updated, notes-only commit `5532a48`, push, final `pr-state`. Worker returned after 72 minutes of turns. |
| 13:20 to 13:58 | Reviewer: six reference reads, the facts file, `facts --issue`, local and remote verification, a detached review worktree with its own `uv sync`, the diff, both call sites traced, a byte-for-byte parity check of the Mattermost text with a scratch script, the new tests run, the terminal change reverted to see its tests fail, the prefix drifted to see the pinning test fail, `make check`, `make test`, and cleanup. Approve; three findings labeled disputed: a backticked `Closes #1053` sentence in the body, a session directory with only `notes.md`, and a `success: bool` annotation that the tests exercise with `None`. 38 minutes. |
| 13:58 to 14:1x | The coordinator read Decisions, then asked Les two questions in one call, each with a recommended answer: accept the notes-only session directory, and change the annotation to `bool \| None`. Les took both recommendations. The coordinator decided the third finding itself: a plain `Closes #1053` line at ready time. The question turn took 11 minutes including the wait. |
| 14:1x | Coordinator resumed the implementation worker with the prompt `placeholder`. The worker spent 11 minutes generating a reply that asked what was meant. The coordinator then resumed the same session with the full corrections handoff, which named the earlier call as a placeholder. |
| 14:2x to 14:38 | Annotation change, `make fmt`, targeted tests, `make check`, `make test`, commit `031fdbf`, notes commit `ac29b75`, push, `verify-commit`, `pr-state`. 16 minutes. |
| 14:4x to 14:59 | Re-review of the delta in a fresh detached worktree: annotation checked against body, docstring, callers, tests, ruff, and pyright. Approve. 14 minutes. |
| 15:0x to 15:37 | Ready submission. The first turn ran for 19 minutes before its first command, then identity and `pr-state`. Body file with the plain `Closes` line, then one `pr ready` call with the body file, `--expect-head ac29b75`, and the board target: description matched, ready read back, board In review, final `pr-state` green. Notes updated across six turns, notes-only commit `4e22f7e` pushed, final `pr-state` with `lint-and-test` pending on the new head. 36 minutes. |
| 15:41 to 15:49 | address-pr-review dispatched for the pending check. The worker read the facts file, ran `pr-state`, `verify-commit --pr-head`, and the check-runs API, confirmed all three checks passed on `4e22f7e`, and confirmed from the commit's file list that the delta was notes only. 8 minutes. |
| 15:49 to 15:52 | Coordinator report from the follow-up read-back, three minutes, with no notes read: PR, heads, checks, the review labeled waived under the exception with its coverage limit at `ac29b75`, and the extra placeholder call named. |

## What held

- **Conditional reads held.** Five references before the first dispatch, against fifteen in #1054, plus the facts command and the facts file; preparation took the same 15 minutes because three went to the OpenCode configuration and two to the user's dev-session skill.
- **The handoff pointed to the facts file** instead of restating setup, gates, and conventions, and was 38 percent shorter than the #1054 handoff.
- **The endpoint report came from the read-back.** Three minutes after the follow-up returned, with no notes read or edited, against 21 minutes in #1054.
- **The decisions in the request held.** Both workers judged the change against the five settled scope points; nobody reopened the home of the helper.
- **The early draft checkpoint worked.** The worker published after its first commit and kept implementing on the same branch, as pr-lifecycle asks. The three earlier runs published once at the end.
- **Test-first and the specific-assertion rule held twice.** The worker reverted its own change and drifted the prefix to see the new tests fail. The reviewer repeated both checks independently and added a parity script.
- **One suite at a time.** `make check` and `make test` ran in separate turns or in sequence, never in parallel.
- **`pr ready` did the ready submission in one call** of 73 seconds, with the description, ready state, board, and final checks read back. In #1054 the same writes took twelve turns and 24 minutes.
- **The placeholder recovery rule was followed.** The coordinator resumed the same session with the full handoff and named the earlier call in it.
- **The facts file was read** by the reviewer and the follow-up worker, and the reviewer ran `facts --issue`. The review and follow-up handoffs pointed to the file and named its required-checks line instead of restating setup.
- **The reviewer read the PR comments** through `pr-state` and said the list was empty.

## What recurred or is new

- **The placeholder dispatch is now three of three** on the merged text, and it survived the new recovery sentence, which fixes the recovery, not the slip. It cost 11 minutes of worker time plus the coordinator's. The slip happens on a resume call after the coordinator has read a long report; text has not prevented it in any run.
- **A notes-only commit after ready caused a follow-up dispatch.** The task-notes rule from PR #73 asks for the ready result to be recorded in one commit after the PR is marked ready. That commit moves the head, `lint-and-test` restarts, and the conditional follow-up in express-issue requires every check passed on the current head, so the parent dispatched address-pr-review to wait for a check on a markdown change. The two rules conflict on any project that commits notes.
- **Reviewer notes became user decisions.** The reviewer labeled a body wording nit, a session-directory convention question, and a type annotation as disputed findings. The coordinator read Decisions and still returned two of them to Les with recommended answers, which Les took; it decided the third itself. In an unattended run that is a hard stop for three nits. The code finding was real but one line; the other two were not about the code.
- **The ready step still took 36 minutes** with the four writes down to one call. Nineteen minutes were one thinking turn before the first command, after a handoff that restated the submit-pr procedure and the notes rule in detail; ten minutes were notes edits and the notes commit; the body file took two.
- **The worker edited the project's `CLAUDE.md`.** It added the new module to the hot-files list, which is the project's convention for new modules, and the reviewer accepted it. An agent editing the instruction file is a project decision the facts file could state either way.
- **The coordinator loaded the user's dev-session skill** alongside ghflow, because the OpenCode session exposes the user's global skills; two minutes, no effect on the run.
- **Review was thorough and long.** 38 minutes plus 14 for the re-review, with a scratch parity script and two efficacy checks. The 1054 review took 88 minutes for a one-line change with the server shared, so these two runs do not settle a review-time pattern.

## Candidate changes

1. task-notes, express-issue, or coordination: resolve the notes-after-ready conflict. Either the notes commit after ready does not reopen follow-up when the reviewed head's checks passed and the only later commits change notes files, with `verify-commit` or `pr-state` supplying that fact deterministically, or notes are not committed after ready. The first keeps the project's convention; the second avoids the head move.
2. review-changes and express-issue: a style preference, a documentation convention question, or a wording nit is a note, not a disputed finding. The coordinator settles notes as routine choices under Decisions and returns to the user only disputes about intended behavior or scope.
3. Placeholder dispatch: text has not prevented it in three runs. A runtime check that refuses a dispatch or resume whose prompt is shorter than a handoff could, if OpenCode's tool hooks allow one; otherwise the recovery rule is the floor.
4. prepare-project-facts: the facts file could state whether agents may edit the instruction files and the module list, since this run did and nothing said yes or no.

None of these is decided.

## Evidence limits

This is one run on one issue and one model. The implementation export starts mid-run, so the worker's early reads, including whether it read the facts file, are not in the record. Wall clock is 4 hours 22 minutes from the coordinator's first turn to its report. Whether the server was unshared is Les's setup, not a measurement. The change is three to four times the size of #1054, so the times are not a like-for-like comparison with that run. The author read the three transcripts and the PR directly; no independent reviewer checked this record.
