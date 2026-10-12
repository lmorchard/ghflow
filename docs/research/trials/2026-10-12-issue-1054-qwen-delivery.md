# Issue #1054 delivery on the local model, concurrent with #1012, 2026-10-12

This record covers a delivery run of [decafclaw issue #1054](https://github.com/lmorchard/decafclaw/issues/1054) on the local Qwen model with the skill text at `62972b3`, the same text as the [issue #1012 delivery](2026-10-12-issue-1012-qwen-delivery.md). The two runs shared the llama server for all but the first eight minutes of this one. Each run was the other's "second workload". This record is the second sample of the merged text on this model, and it was selected as the first measurement for the overnight burndown plan.

## Setup

Les selected the issue from candidates that the parent had checked against `origin/main`. The parent rejected #1012 for this measurement because its premise was stale after PR #1041, and Les ran #1012 in a separate session anyway. The parent chose #1054 as a Python-only, one-line fix with one new test and no browser check.

Les started an interactive OpenCode session in the decafclaw root on `llama.cpp/llama` and pasted a reference to the prompt file `/tmp/ghflow-1054-prompt.txt`, which the ghflow skill invocation preceded:

```text
deliver issue 1054 https://github.com/lmorchard/decafclaw/issues/1054 through PR review follow-up, without merge. Use the same local model for implementation and review under my approved exception for OpenCode with the local model on this laptop. Decision: use the clear-on-next-usage approach from the issue, not the recompute approach.
```

The decision sentence settled the issue's "pick one of two approaches" before dispatch. The model is `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` at `http://127.0.0.1:9931/v1` with the user's configured limits. The installed skill clone was at `62972b3`. The decafclaw `opencode.json` from the #1012 setup was present. Sources: exported transcripts `session-ses_ed20.md` (coordinator, `ses_ed200bed0ffePd1qQ2UpJ6a6fG`), `session-ses_ed1e.md` (implementation worker, `ses_ed1eff4aeffe6fKFk4tlp6g8iC`), and `session-ses_ed19.md` (reviewer) in the decafclaw root, not copied into this repository. The exports carry per-turn durations and no token counts.

## Result

[PR #1061](https://github.com/lmorchard/decafclaw/pull/1061) ended ready for review at head `42e9a74`, with three hosted checks passed, the issue In review, and no merge. One commit holds the change: six files, 77 insertions, 3 deletions. The new test failed before the fix with `assert 5000 is None` and passed after it. An independent review in a fresh session covered `42e9a74` and found no actionable defects. The coordinator applied the conditional follow-up and stopped without an address-pr-review dispatch.

| | #997 run | #1012 run | #1054 run |
| --- | --- | --- | --- |
| Skill text | `ddd342e` | `62972b3` | `62972b3` |
| Change size | about 60 lines | 99 insertions, 7 deletions | 77 insertions, 3 deletions |
| Server | alone | shared with #1054 | shared with #1012 |
| Wall clock | 3 h 50 min | 7 h 7 min | 4 h 39 min |
| Task calls | 7 | 4, of which 3 did work | 4, of which 3 did work |
| Placeholder dispatch at the ready step | no | yes, new session, "placeholder" | yes, correct session, "x" |
| Coordinator preparation before first dispatch | 23 min | 27 min | 15 min, 15 reference files |
| Coordinator reviewed the diff itself | yes | no | no |
| Worker read shared references | no | yes, all named | yes, all ten named |
| Implementation to draft PR | two dispatches | one worker, 4 h 31 min | one worker, 1 h 38 min |
| Code commits on the PR | 2 | 1, plus 5 notes-only commits | 1 |
| Review time | 47 min | 28 min | 88 min |
| Review ran the new test against the pre-fix code | no | yes | yes, in a temporary copy |
| Final follow-up dispatch | yes | no | no |
| Coordinator work after the ready report | - | 6 min | 21 min |

## Timeline

Local times come from the session's created time, 19:44:25, plus the recorded turn durations. The sum matches the session's updated time within one second. The #1012 session started at 19:52 and ended at 03:00.

| Local time | Event |
| --- | --- |
| 19:44 | Session start. The coordinator read the prompt file, loaded the skill, and read express-issue, ten shared references, implement-issue, submit-pr, board-status, and the CLI reference. It checked identity, read the issue, and found no existing branch, worktree, or PR. It fetched `origin/main` and noted that local `main` was behind. |
| 19:59 | First dispatch, 7,028 characters: implement-issue, then submit-pr for the draft, in one session. The handoff named the confirmed decision, the exact worktree and branch, the project's worktree setup, the board command, the identity gate, both `verify-commit` forms, the notes path, and a return list. It told the worker to leave the notes directory untracked. |
| 20:06 | Worker had read the entry skill, both task references, all ten shared references named, and the CLI reference. Two commands failed because `GHFLOW_CLI` was not set in the new shell; the worker exported it in each later command. |
| 20:09 | Worktree created from `origin/main` at `cbe2442`. |
| 20:09 to 20:33 | Code investigation: the single usage-recording site, the reactive path, the meter reader, the existing reactive test harness, and the root `conftest.py` fixtures. One turn of 9.6 minutes read `agent.py` and `test_compaction.py`. |
| 20:33 to 20:43 | `.env` copied with an `HTTP_PORT` line, `uv sync`, identity confirmed as `MokaGnome`, board transition. The board was already In progress; the write returned `unchanged` with a matching read-back. The transcripts do not show who moved it. Notes file created. Baseline `make test`: 4,507 passed, 2 skipped, in 19 seconds. |
| 20:43 to 20:58 | Test written first and run red for the stated reason. One-line fix, field comment, and a sentence in `docs/conversations.md`. The worker also hand-edited `docs/websocket-messages.md`. Targeted run: 47 passed. |
| 20:58 to 21:19 | `make fmt`, then `make check` and `make test` in parallel, twice. The generated doc edit vanished, because `check-message-types` regenerates it. The worker found the manifest, edited the description there, regenerated, confirmed idempotence, and re-ran the gate in the staged state. About 14 minutes. Commit `42e9a74` under `MokaGnome` at 21:19. |
| 21:19 to 21:37 | Notes updated, `origin/main` re-fetched and unchanged, no PR template, push, `verify-commit --on`, body file in the notes directory, draft PR #1061 at 21:28, read-back of body and draft state, `verify-commit --pr-head`, and `pr-state` already green on all three checks. Worker returned after 1 h 38 min. |
| 21:37 | Coordinator read review-changes, then dispatched the reviewer in a fresh session, 5,508 characters, with the issue, base and head, the worktree, the read-only limit, the same-model exception as a user approval, and a focus list. It did not read the diff. |
| 21:42 to 23:10 | Reviewer: six reference reads in two minutes; local and remote verification of base and head; `pr-state` with an empty comments list; diff read; 34 minutes tracing every writer and reader of the field, every `compact_history` call site, per-turn context creation, and the tool-call fork; `make check-message-types`; 45 targeted tests; a temporary copy of the worktree with the fix hunk reverted, where the new test failed exactly at the expected assertion; the two #1005 meter tests; then a 13-minute report. Three notes labeled not defects or pre-existing. Returned after 88 minutes. |
| 23:10 | Coordinator resumed the implementation worker with the prompt `x`. The worker spent 16 minutes generating a two-sentence reply that asked what was meant. The coordinator named the slip itself. 22 minutes in total. |
| 23:32 | Resume with the real handoff, 2,954 characters: ready submission on the existing draft, with the review outcome text, the five ordered steps, and a return list. The worker confirmed the local head equaled the published head, ran `verify-commit --pr-head`, rewrote the body file, updated the description and read it back, ran `gh pr ready` as a separate command and read back `isDraft: false`, moved the board to In review with a matching read-back, and ran a final `pr-state`. PR ready at 23:55. Returned after 30 minutes. |
| 00:02 to 00:23 | Coordinator read the worker's notes, one turn of 15.7 minutes, edited the notes' status line to "ENDPOINT REACHED", updated its todo list, and reported: PR and head, the change, test and CI evidence, the same-model review with the exception named, the board state, and the merge left with Les. It cited the ready report against the three conditions of the conditional follow-up. |

## What held from the merged text

- **One worker carried implementation and draft publication**, with corrections and ready submission in the same session. No correction cycle was needed.
- **The coordinator did not review the diff.** It read review-changes between the worker's return and the reviewer dispatch, and nothing from the subject repository.
- **Test-first with a specific assertion.** The worker ran the new test red before the fix, and the failure was the reported behavior. The reviewer repeated that check independently on a pre-fix copy.
- **The reviewer read the PR comments before saying there were none**, through `pr-state` after PR #71.
- **Each GitHub write had its own read-back.** Description update, `gh pr ready`, and the board move were separate commands with read-backs, as submit-pr requires after PR #67.
- **The conditional follow-up stopped the flow.** The coordinator quoted the three conditions from the ready report and did not dispatch address-pr-review.
- **The worker kept its notes untracked**, as the handoff said. No notes-only commit moved the head, so the loop that the #1012 run hit did not occur. The decafclaw history commits session docs, so this handoff diverged from the project's practice.

## What recurred or is new

- **The placeholder dispatch at the ready step recurred.** Two runs on the merged text, two placeholder prompts at the same point, after the review report and before the ready submission. This run sent it to the correct session and recovered by resuming the same session; the #1012 run sent it to a new session first. The slip cost 22 minutes here. The #1012 record called it a model fault. Two of two is a pattern.
- **The coordinator still read every reference first.** Fifteen files in 15 minutes before the first dispatch, including three task references it would only dispatch. Three of three runs on this model. The #1012 record's candidate 4 stands.
- **Coordinator wrap-up after the endpoint cost 21 minutes.** The ready report already satisfied the conditional follow-up. The coordinator then read the worker's notes for 15.7 minutes and edited them. express-issue tells the coordinator to report from the worker's read-back, not its own reads; the notes edit was a write in the subject worktree outside the coordinator's role.
- **`GHFLOW_CLI` did not persist across bash calls.** The handoff gave `GHFLOW_CLI="..."` and the worker assumed a persistent shell. Two commands failed before it exported the variable in every command. The entry skill says to set the variable; it does not say that each command may run in a new shell.
- **Two full gates ran in parallel twice without a failure.** `make check` and `make test` ran together before and after the generated-file fix. The suite took 45 to 59 seconds instead of the baseline 19. This is the pattern that the worker-bounds change forbids; in this project and at this suite size it caused slowness, not deaths.
- **A hand edit to a generated file cost 14 minutes.** decafclaw's AGENTS.md states the manifest rule and the drift check. The handoff told the worker to read AGENTS.md fully, and the worker still edited the generated file first. It recovered from the gate failure and recorded the gotcha in its notes. No skill change.
- **The review was the longest phase.** 88 minutes for a one-line change, against 28 minutes for #1012. Two thirds went to tracing call sites and running checks, and the report alone took 13 minutes at shared-server speed. The trace was thorough and found no defect; nothing in review-changes bounds it.
- **The draft was published once, after completion.** The first significant checkpoint and the final commit were the same commit, as in both earlier runs. The early-draft path remains unexercised.

## Candidate changes

1. express-issue or coordination: name the recovery for a malformed dispatch. If a dispatch goes out with an empty or placeholder prompt, resume the same session with the full handoff and report the slip. Text may not prevent the slip; it can fix the recovery, which the two runs did differently.
2. SKILL.md: state that `GHFLOW_CLI` may need to be set in each command when the agent's shell does not persist, and show the `export` form.
3. express-issue: after a ready report that meets the three conditions, report from that read-back; do not read or edit the worker's notes to record the endpoint.
4. The #1012 record's candidate 4, coordinator pre-reading, now has a third sample.

None of these is decided. The worker-bounds change on branch `worker-bounds` already covers the concurrent-suite and notes-commit observations.

## Evidence limits

This is one run on one issue and one model. The llama server was shared with the #1012 delivery from 19:52 to the end of this run, so wall-clock figures are not comparable to the #997 run and the per-phase minutes overstate solo-server costs by an unmeasured factor. Les reports that the second workload roughly halved the tokens per second available to each run. The 16-minute reply to `x` is one indication of that speed. The exports carry no token counts. The author read the three transcripts directly and verified the PR, commits, checks, board state, and skill commit with `gh` and `git`; no subagent analyzed the transcripts, and no independent reviewer checked this record. The run did not exercise the correction cycle or the early-draft checkpoint. The transcripts do not show who moved the issue to In progress before the worker's write. Together with the #1012 run, two deliveries sharing one server produced two ready PRs in 7 hours 7 minutes.
