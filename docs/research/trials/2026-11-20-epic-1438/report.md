# Epic #1438 local-model burndown and compact-tags trial

This report covers the run that [index.md](index.md) records. It answers the three questions: the epic outcome, the compact-tags trial, and the operations and follow-ups.

## Epic #1438 outcome

### Per issue

| Issue | PR and head | CI | Review | Tests | Complete |
| --- | --- | --- | --- | --- | --- |
| #1423 Replace name-string fixture gating | [#1610](https://github.com/lmorchard/decafclaw/pull/1610) `0f20724` | green | clean at `0f20724`, same model | `make test` 6087 passed, 2 skipped, and the runner gate `make check` passed | Endpoint reached. The PR is ready. |
| #1424 Remove OTel private-internals reset | [#1611](https://github.com/lmorchard/decafclaw/pull/1611) `d936f35` | green | clean at `d936f35`, same model | `make test` 6101 passed, 2 skipped, and the runner gate passed | Endpoint reached. The PR is ready. |
| #1419 Split `tests/test_skills.py` | none | not run | not run | no edits | Not complete. Parked (blocker). |
| #1420 Split `tests/test_context_composer.py` | [#1614](https://github.com/lmorchard/decafclaw/pull/1614) `9b6d51f` | green | clean at `9b6d51f`, same model | `make test` 6101 passed, 2 skipped, and the runner gate passed | Endpoint reached. The PR is ready. |
| #1421 Split `tests/test_conversation_manager.py` | [#1619](https://github.com/lmorchard/decafclaw/pull/1619) `dcf16807` | green | clean at `dcf16807`, same model | focused 119 passed, and `make test` 6108 passed, 2 skipped, 1 pre-existing failure | Not complete. The PR is a draft. |
| #1422 Prefer behavior-level JS assertions | none | not run | not run | not started | Not started. |

The review verdicts are PR comments with the head SHA and model. The GitHub review state stays `none` because the verdict is a comment, not a native review.

### Test-split quality

**#1420.** The base file had 2,567 lines, 130 test methods, and 31 classes. The split keeps 5 foundational classes in the original file (109 lines) and moves the rest into `_assembly` (1,472 lines, 16 classes), `_retrieval` (977 lines, 7 classes), `_token_budget` (65 lines, 2 classes), and `_modes` (20 lines, 1 class). Collection parity holds: 134 items before and after. The reviewer compared 169 AST blocks and found them byte-identical. `make test` passed.

**#1421.** The reviewer measured 3,594 lines at the base and 1,105 lines at the head. The split adds `_confirmations` (1,493 lines) and `_enqueue` (1,181 lines). All 115 test functions are present once, byte-identical, for 119 collected items including one parametrize expansion. Focused tests passed 119 of 119. The full `make test` had one pre-existing contract-test failure at the base, not caused by the PR. `make check` passed.

The issue names four concerns: turn lifecycle, confirmation, enqueue, and side-question. No side-question tests existed in the base file. The split covers the concerns that have tests.

**`make test` and `make test-js`.** `make test` passed for #1420 and #1424, and passed apart from one pre-existing failure for #1421. `make test-js` was not exercised: #1420 and #1421 change Python tests only, and #1422, the JS issue, did not start. Hosted `js-test` passed on every PR.

**Coverage.** No review measured coverage. The test counts are preserved, but a coverage change cannot be ruled out.

**Conflicts and reruns.** No merge conflict occurred. #1420 needed one retry after a 5400-second timeout, and a second commit for a stale docstring. #1421 needed one retry, and the first commit failed the `ruff` I001 import-sort check.

### Local model quality

The model produced three ready PRs with clean same-model reviews. It found a stale issue target in #1423 and adapted. Its reviewers checked the split fidelity with AST comparisons and ran the full suite.

Defects and rework:

- **#1423:** The target fixture was removed by [PR #1520](https://github.com/lmorchard/decafclaw/pull/1520) before the run. The worker asked a question through the unattended `question` tool. The tool returned an error. The worker then added a regression guard. The review accepted it and flagged that the issue's literal result was already met and its "Tests" requirement no longer applies.
- **#1419:** Two implement sessions each timed out after 900 idle seconds with no edits. The model read the 3,138-line file and never wrote. It used `tags outline` three times in the first session. The runner parked the issue.
- **#1420:** The first session committed the split, then exceeded the 5400-second session timeout during verification. The retry committed a docstring pointer. The final head passed.
- **#1421:** The first session produced the split but exceeded the 5400-second timeout before it committed. The retry committed the split, failed `ruff` I001, and fixed it. The review posted clean. The runner hit the 30-minute floor before the ready step, so the PR stayed a draft.
- **#1424:** The worker replaced the private OTel reset with a public-API guard after confirming that opentelemetry-api 1.44.0 has no public reset. The review verified the guard and the full suite.

Time and size:

| Issue | Size | Implement | Review | Endpoint | Wall clock |
| --- | --- | --- | --- | --- | --- |
| #1423 | S | 44 turns, 59.8k context | 16 turns, 44.2k | DONE 18:17 | 46 min |
| #1424 | S | 66 turns, 91.7k context | 23 turns, 56.7k | DONE 19:30 | 73 min |
| #1419 | M | 2 sessions, no edits, 87.5k and 105.9k | not run | parked 20:46 | 75 min |
| #1420 | M | 61 turns, 137.5k, plus 29-turn retry | 34 turns, 60.3k | DONE 22:50 | 124 min |
| #1421 | M | 60 turns, 148.8k, plus 42-turn retry | 55 turns, 66.8k | draft, not ready | 145 min |
| #1422 | M | not started | not run | not started | 0 |

The two S issues were tractable. The three M test splits were not. The local model read the large files in chunks, grew context to 137k to 149k, and often timed out before or during the commit. The extraction script helped #1420 and #1421, but the model needed a retry to commit.

### Parked, stranded, and unstarted work

- **#1419 parked (blocker).** The issue is `triage:needs-input` and In progress. The park comment says "Session failed repeatedly: Session idle timeout (900s without events)". The worktree is preserved and clean at `01347796` with no commit.
- **#1421 stranded as a draft.** PR #1619 is a draft with a clean verdict at `dcf16807` and green CI. The board is In progress and the label is still `triage:ready`. The runner stopped at 01:16 with 14.3 minutes left, below the 30-minute floor, before the ready step.
- **#1422 not started.** The runner selected it at 01:16 and stopped at once with 14.2 minutes left. Its board status is Backlog and its label is `triage:ready`. No worktree or session exists.
- **Dirty worktrees.** #1421 and #1423 each hold four uncommitted files: `openapi.json`, `openapi.yaml`, `api-client/index.js`, and `api-client/services/DefaultService.ts`. They are gate-generated drift from `make check`. The commits do not include them.

## Compact-tags trial

### Per-session use

Counts come from the full session log. The runner debrief shows zero tags because it reads a truncated shell summary.

| Session | Step | Turns | Context | Tags | grep tool | read | shell grep |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `implement-20261120-173128` (#1423) | implement | 44 | 59.8k | 0 | 0 | 6 | 17 |
| `review-20261120-180014` (#1423) | review | 16 | 44.2k | 0 | 0 | 2 | 5 |
| `implement-20261120-181806` (#1424) | implement | 66 | 91.7k | 0 | 0 | 8 | 26 |
| `review-20261120-190752` (#1424) | review | 23 | 56.7k | 0 | 1 | 7 | 8 |
| `implement-20261120-193105` (#1419 #1) | implement | 22 | 87.5k | 3 | 0 | 8 | 3 |
| `implement-20261120-195904` (#1419 #2) | implement | 29 | 105.9k | 0 | 0 | 8 | 10 |
| `implement-20261120-204633` (#1420 #1) | implement | 61 | 137.5k | 0 | 0 | 8 | 17 |
| `implement-20261120-221953` (#1420 #2) | implement | 29 | 40.2k | 0 | 0 | 3 | 13 |
| `review-20261120-223120` (#1420) | review | 34 | 60.3k | 0 | 0 | 2 | 8 |
| `implement-20261120-225043` (#1421 #1) | implement | 59 | 148.8k | 0 | 0 | 14 | 17 |
| `implement-20261121-002243` (#1421 #2) | implement | 42 | 51.9k | 0 | 0 | 2 | 12 |
| `review-20261121-004537` (#1421) | review | 55 | 66.8k | 0 | 0 | 1 | 18 |
| **Total** | | **480** | **max 148.8k** | **3** | **1** | **69** | **154** |

The three tags commands are all `python3 "$GHFLOW_CLI" tags outline tests/test_skills.py` in the first #1419 session. The model used no `tags brief` and no `tags find`.

Turn counts come from step-finish events in the full logs. The session debrief counts 483 turns because it includes a final partial turn.

Input tokens total 27,469,635. Cached-prompt tokens are zero in every session. Sixty turns reached 100k or more context. The maximum context was 148.8k.

### Did the model use the tools?

Yes, once. The first #1419 session used `tags outline` three times to navigate the 3,138-line file. The other large-file sessions (#1420 and #1421) used `read`, `sed` chunks, and an extraction script instead. The directive was present in every implement handoff. The model did not ignore a missing instruction. It chose other tools on the two largest tasks.

### Comparison with the pre-#211 run

The closest earlier local-model run is the [#1432 queue run](https://github.com/lmorchard/decafclaw/issues/1432) on 2026-11-19. It used the same runner and model. It is not a controlled baseline: its issues were smaller implementation changes, not test splits.

| Measure | #1432 run, 2026-11-19 | This run, 2026-11-20 |
| --- | ---: | ---: |
| Sessions | 17 | 12 |
| Turns | 582 | 480 |
| Tags commands | 0 | 3 |
| grep tool calls | 52 | 1 |
| read calls | 148 | 69 |
| shell grep calls | 111 | 154 |
| Input tokens | 29.18M | 27.47M |
| Cached-prompt tokens | 0 | 0 |
| Turns at 100k or more | 27 | 60 |
| Maximum context | 121.9k | 148.8k |
| Duration | 7.2h | 7.8h |
| Delivered | 7 PRs | 3 ready PRs, 1 parked, 1 draft, 1 not started |

The per-turn input is similar: 50.1k in the baseline and 57.2k here. Context per turn is higher here because of the large test files. This run does not show a token fall. It also does not isolate the compact tags, because the tasks differ.

### Verdict

Run another trial. The compact tags were used once, on the one task that used them for file structure. The model used other tools on the two largest files. There is no measured token saving, and the baseline had no tags use to compare. Keep the commands. Do not claim adoption or a saving from this run.

A better next trial uses a task that needs symbol navigation, such as a cross-module refactor. Record the tags count from the full session log, not the debrief column.

## Operations and follow-ups

**Facts refresh.** The kickoff expected the runner to publish a facts-refresh PR. The runner has no such dispatch. It only prints a stale-facts warning. No facts-refresh PR exists. The stale sources were `AGENTS.md`, `CLAUDE.md`, `Makefile`, `.github/workflows/ci.yml`, `conftest.py`, `tests/conftest.py`, `pyproject.toml`, and `docs/config.md`. Only #1548 (CI browser job) and #1542 (notification defaults) changed them since the facts write. The `make check` target is unchanged. The risk was low for this run.

**Runner lock.** The lock file held a dead holder (pid 19918, "project o/12"). The operating-system lock was free. The runner acquired the lock. No second runner ran.

**Model availability.** `opencode models` listed the pinned model before launch. Every implement handoff said `Review plan: model lmstudio/qwen3.8-27b-mlx@4bit`. Every review verdict named the same model. The reviews were same-model in a fresh session. Different-model review was waived under the standing local-model exception.

**Notebook.** The run posted step notes to https://github.com/lmorchard/decafclaw/discussions/1607.

**Session timeouts.** The run had two 900-second idle aborts (#1419) and two 5400-second session timeouts (#1420 first session, #1421 first session). It had no 300-second aborts. The 900-second idle timeout avoided the baseline's premature aborts, but the 5400-second cap hit during final verification for #1420 (after the commit) and before the commit for #1421. The context reached 137.5k and 148.8k in those sessions. The runner had no context cap (`--max-context-tokens 0`).

**Toil that hit Three Strikes.** The runner's toil audit found one pattern in three implement sessions: the sequence `gate --cmd "make check"` then `gate --cmd "make test"` after a `cd` to the worktree. The run also showed a second repeated pattern below the threshold: `make check` regenerates four tracked API files in a fresh worktree, and the worker must revert them. #1421 and #1423 kept the drift.

**Debrief tags signal.** `session debrief` shows zero tags for this run. The actual count is three. The debrief reads a truncated shell summary, and the `cd` prefix pushes `tags outline` past the truncation.

### Candidate changes

These were proposals at the time of the run. The implemented subset is in "Implemented after the trial" below.

1. Add a facts-refresh dispatch to `scripts/run_queue.py`, or state in the burndown reference that the coordinator must run `prepare-project-facts` before launch. The current runner only warns.
2. Pass a context cap for local runs, such as `--max-context-tokens 120000`, so a session stops at a step boundary instead of growing to 149k.
3. Make `make check`'s generated files idempotent in a fresh worktree, or have the runner revert `openapi.json`, `openapi.yaml`, and the two api-client files after the gate.
4. Add a resume path for a draft PR with a clean verdict. The current runner leaves it stranded when the floor stops the ready step.
5. Fix the debrief tags signal to read the full shell command, not the truncated summary.
6. Consider a deterministic test-file splitter for issues like #1419 and #1421. The local model does not complete them within one session.
7. Decide whether to close #1423 as already met by #1520 and keep the regression guard, or fold the guard into another issue.
8. Re-run the compact-tags trial on a symbol-navigation task and compare tokens with a same-task baseline.

### Implemented after the trial

[PR #213](https://github.com/lmorchard/ghflow/pull/213) implements the safe subset:

- A deterministic `submit-pr`, the endpoint bookkeeping, and a park can run below the time floor. A successful submit below the floor is recorded as endpoint `ready`. This fixes the stranded #1421 draft.
- The precomputed gate restores the paths that `make check` regenerates, and the implement directive names those paths.
- The implement directive asks for a checkpoint commit before the full gate.
- The session debrief counts the compact tags from the full shell command, not the truncated summary.
- Every session directive names the stale project-facts sources.

The full facts-refresh dispatch, a context cap, a deterministic test splitter, and the #1423 and #1422 decisions remain open.

## Evidence limits

- The run has one sample and a different issue mix from the baseline.
- The runtime reports no cached-prompt tokens.
- No coverage measurement was made.
- The debrief tags column is wrong for this run. The report uses the full log.
- #1421 is a draft with a clean verdict. It is not ready and not merged.
- #1419 is parked. No code exists for it.
- Merge was not authorized and did not occur.
