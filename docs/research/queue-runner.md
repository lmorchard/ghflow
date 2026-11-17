# Proposal: a deterministic queue runner, 2026-11-15

This document records the design and trial findings for the deterministic queue runner (`scripts/run_queue.py`).

We propose a Python script, the runner, that runs an unattended delivery loop for issues curated on the project board. A model does one operation in each fresh session. The runner selects the next operation from the current GitHub state. It does not select issues from backlog, call a model to make a scheduling decision, or merge.

## Why a model coordinator is not sufficient

Les ran seven unattended Ready-queue burndowns with a local model. Workers usually completed their individual operations. Most failures came from the coordinator, the session that runs the loop.

| Failure | Run | Source |
| --- | --- | --- |
| The coordinator read 14 to 19 references before its first dispatch. | 1, 5 | [run 1](trials/2026-10-13-unattended-burndown.md), [run 5](trials/2026-10-17-unattended-burndown-5.md) |
| Coordinator context reached 167,000 tokens. Prompt processing cost about one hour. | 1 | [run 1](trials/2026-10-13-unattended-burndown.md) |
| The coordinator read subject code to write the scope of a handoff. | 1 | [run 1](trials/2026-10-13-unattended-burndown.md) |
| The coordinator accepted optional reviewer notes. Each note cost a correction and a re-review. | 1 | [run 1](trials/2026-10-13-unattended-burndown.md) |
| The final report gave an end time that no clock command supplied. | 2 | [run 2](trials/2026-10-14-unattended-burndown-2.md) |
| The coordinator wrote its own refresh handoff and added a review cycle. | 5 | [run 5](trials/2026-10-17-unattended-burndown-5.md) |
| The coordinator started an issue without the time estimate, or measured from `updatedAt`. | 4, 6 | [run 4](trials/2026-10-15-unattended-burndown-4.md), [run 6](trials/2026-10-18-unattended-burndown-6.md) |
| Background dispatch let a session continue after its client stopped. Two coordinators then shared one model cache. | 7 | [run 7](trials/2026-10-21-unattended-burndown-7.md) |
| A reviewed PR stayed a draft. Its ready step never ran, and nothing parked it. | 7 | [run 7](trials/2026-10-21-unattended-burndown-7.md) |

## Proposed loop

The runner is a reconciliation loop. It observes the board, selects one item, drives that item to its desired state one step at a time, and observes the board again.

```text
loop:
    board = observe_board(project)          # queue select for each column, pr-state for in-flight PRs
    issue = next_item(board, attempted)     # pure function, decision 9
    if issue is None: break                 # nothing actionable: exit
    attempted.add(issue)                    # one attempt for each issue in this run
    loop:
        state = observe(issue)              # facts --issue, pr-state, verdict
        step  = next_step(state)            # pure function
        if step in {DONE, PARKED, WAITING}: break
        if state == previous.get(issue): park(issue, "no progress"); break
        previous[issue] = state
        run_session(step, issue)            # ghflow handoff, then one opencode run
    if once: break
```

The desired state of an issue is one of two results:

1. A ready PR with green checks on the current head, and no pending review that the run can address.
2. A park with a recorded question or blocker under `triage:needs-input`.

Merge is not part of the desired state.

### Next step for each observed state

`next_step` is a pure function. It reads only the observed state, so unit tests can supply each state as a fixture.

| Observed state | Next step |
| --- | --- |
| The issue has `triage:needs-input`. | Stop with `PARKED`. |
| The issue has no open PR. | Implement with implement-issue. The runner publishes committed work as a draft PR when the session did not. |
| The PR is a draft and has no review verdict for its current head. | Review with review-changes. The reviewer posts a verdict. |
| The verdict for the current head has blocking findings, and earlier blocking verdicts are below the limit. | Fix with address-pr-review, with the blocking findings. |
| The verdict for the current head has blocking findings, and earlier blocking verdicts reached the limit. | Park with `park --kind blocker`. |
| The verdict for the current head is clean. | Mark ready with submit-pr. Non-blocking notes go in the PR description. |
| The PR is ready and its checks are pending. | Wait a fixed time, then observe again. |
| The PR is ready and a check failed or a review thread is unresolved. | Follow up with address-pr-review. |
| The PR is ready and a requested review is pending. | Stop with `WAITING`. The summary reports it. |
| The PR is ready, its checks are green, and nothing is pending. | Stop with `DONE`. |

### Review verdict

The runner reads every input of `next_step` from GitHub, so that a restart needs no local files. GitHub does not let the agent account approve or request changes on its own PR. The reviewer therefore posts its verdict as a PR comment with `pr comment`.

The comment starts with a fixed marker: `<!-- ghflow-review head=SHA verdict=clean|findings|blocked -->`. The body lists blocking findings and non-blocking notes separately. The runner ignores a verdict whose SHA differs from the current head. `pr-state` reports these verdicts under `review_verdicts`.

The count of earlier blocking verdicts on the PR gives the correction limit.

### Progress rule

If a step leaves the phase, the head, and the verdict unchanged, the runner parks the issue with the log path. If the session exited with an error, the runner retries once in a fresh session before parking.

### Time and sessions

The runner reads the clock and measures each step itself. It starts a new issue only when the time that remains covers the larger of a fixed floor (default 30 minutes) and the measured step times. The runner passes `--deadline` to `handoff`. At the deadline, it finishes the running step, starts no new step, and parks the current issue with `park --kind time`.

The runner runs one session at a time in single-session mode, without subagents. It deletes each OpenCode session after its step. It refuses to start when another run is active.

## Confirmed decisions

Les settled these on 2026-11-15:

1. Direction change approved. The runner selects work from the board in a fixed order (decision 9), within the columns that Les curates. It never selects from Backlog. It does not run on a schedule or poll. `docs/dev/direction.md` is updated to say so.
2. The reviewer posts its verdict as a PR comment with a head-SHA marker. `pr-state` reports these verdicts. A restart then needs only GitHub state.
3. If a session exits with an error, the runner retries the step once in a fresh session. If the state still does not change, the runner parks the issue.
4. At the deadline, the runner lets the running step finish within a hard timeout for each session. It starts no new step and parks the current issue with `park --kind time`.
5. One issue holds both slices. Slice 1 is `--once`: select the single next item, drive it to its desired state, and exit. Slice 2 loops until nothing actionable remains.
6. The runner is Python 3 with the standard library only.
7. Concurrency is out of scope. The runner runs one session at a time on one repository.
8. The runner calls `cli/ghflow.py` as a subprocess and reads its JSON output through `run_cli(*args)`.
9. Selection order:
   1. An In progress or In review issue that the runner can advance (no PR yet, draft without current-head verdict, blocking findings under limit, failed check, or unresolved review thread).
   2. A time-parked delivery (from `parked` list of `queue select`).
   3. The first issue in Ready, in `queue select` order: priority, then Size, then issue number.
   Skips issues with `triage:needs-input` (question/blocker park), and `WAITING` or `DONE`.
10. A ready PR with green checks that waits only for Les does not stop the runner. The runner marks it `DONE`/skips it and continues with Ready.
11. Project discovery: the runner uses the one open project linked to the repository via `gh repo view --json projectsV2`. If 0 or >1, it stops with the list unless `--project OWNER/NUMBER` is given.
12. No issue parameter required.

## Overnight use

During the day, Les stages work with `curate-ready-queue` and answers parked questions with `sweep-needs-input`. At night, the runner takes the in-flight and time-parked deliveries first, then the curated Ready column. In the morning, Les finds ready PRs, parked questions under `triage:needs-input`, and the summary table.

## Implementation

`scripts/run_queue.py` uses only Python standard library. It calls `cli/ghflow.py` as a subprocess and parses JSON output. It accepts command-line arguments:
- `--project OWNER/NUMBER` (project board mode)
- `--parent OWNER/REPO#NUMBER` (parent issue mode: burndowns native sub-issues with stacked PRs)
- `--hours N` (time budget)
- `--model MODEL`
- `--floor MINUTES`
- `--once`
- `--allow-concurrent`
- `--max-turns N` (turn ceiling per session, default 100)
- `--session-timeout SECONDS` (wall-clock ceiling per session, default 5400)

Tests use `unittest` in `scripts/test_run_queue.py` and `cli/test_ghflow.py`.

## Deterministic steps

The runner performs every mechanic that has one correct answer. A model session receives the facts it needs and does not rediscover them.

| Step | Owner | Evidence |
| --- | --- | --- |
| Select the next item (board or parent) | Runner | `next_item`, `next_item_for_parent` |
| Decide the step for an observed state | Runner | `next_step`, pure function |
| Choose the branch name and base revision | Runner | `prepare_worktree` calls `worktree create`, which fetches and branches from `origin/<default>` |
| Create the worktree | Runner | Same call, before the session starts; exit 3 reuses a resumed worktree |
| Move the issue In progress and In review | Runner | `set_board_status` |
| Detect no progress, failure, or a stall | Runner | Progress rule, session ceilings, reasoning-loop abort |
| Park an issue, with or without a PR | Runner | `park_issue` and `park` |
| Answer the issue: scope, design, code, tests | Session | The issue body and decisions |
| Prepare the project's worktree setup | Runner | `worktree create` applies the facts file's `worktree:` declaration before the session starts |
| Commit, push, and open the draft PR | Session for content and commits; Runner for push and draft creation | `publish_committed` after an implementation session, through `pr create` |

No row remains open. Issue #161 moved the last two into the runner after the epic #1434 trial showed their cost. Child #1380 spent 36 minutes and 42 turns without a worktree, branch, or PR, and child #1381 chose its own worktree path. The project facts file now supplies the setup as an executable declaration. The runner pushes committed work and opens the draft PR when a session leaves it unpublished.

## Limits

1. One process, one session at a time, one repository. No locks, worker pools, or multi-repository support.
2. The runner selects only from In progress, In review, time-parked deliveries, and Ready, in the order of decision 9. It never selects from Backlog.
3. Command-line inputs only. No configuration file or rule language.
4. GitHub holds the state. The runner never reads its own log back.
5. The runner never merges. It has no gate or trust mechanism.
6. Les starts each run. No cron, daemon, or event listener in the skill.
7. OpenCode only, behind one function.
8. A new step, state, or selection rule needs a trial record that shows the need.
9. Size checkpoint: keep `scripts/run_queue.py` under about 500 lines.

## Relation to agent-sessions

| agent-sessions mechanism | Cause | This proposal |
| --- | --- | --- |
| `locks.py` locks in `refs/locks/issue-N` | Parallel runs | One run at a time |
| `router.py` priority ladder, unpark on comment, attempt counts | The goal was the whole backlog | Board selection and the progress rule |
| Event-driven `reconciler.py`, cron, `wait_*` phases | Continuous operation | A bounded run that Les starts |
| Frozen checks, spec markers, read-only grader, `gate.py` | Unattended merge | No merge |
| `credentials.py`, write manifests | A separate writer program | `ghflow exec` and the agent identity |
| `run_progress.py`, `docs_check.py`, `doctor.py` | Supervision of a long-lived system | `queue summary` and the log |
