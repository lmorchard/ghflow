# Decafclaw janitorial weekend burndown

This report covers the run that [index.md](index.md) records. It answers what ran, what held, what failed, and which changes follow.

## Setup

The run processed the `triage:ready` + `impl:local` children across nine janitorial epics. A supervisor ran five phases in sequence. Each phase used the local model and the same runner settings: `--project lmorchard/6`, `--require-label impl:local`, `--floor 30`, and `--step-idle-timeout 900`. Phase A ran without `--stack`. Phases B and D used `--stack` for same-file series. Phase E ran #1438's #1422.

The launch base was `9c02ef43`. The run started with nine stale project-facts sources. The runner injected the stale-source note into every directive.

## Result

| Category | Count | Detail |
| --- | ---: | --- |
| Done | 27 of 33 | 23 merged, 4 open ready |
| Open ready | 4 | #1707 (CI missing), #1756, #1758, #1760 |
| Drafts with committed work | 2 | #1755 (#1378), #1759 (#1405) |
| Parked | 3 | #1337, #1408 (#1689 draft), #1411 |
| Not started | 1 | #1379 |

The 23 merged pull requests are #1634, #1637, #1639, #1643, #1653, #1656, #1663, #1667, #1668, #1674, #1679, #1682, #1695, #1696, #1697, #1699, #1700, #1701, #1702, #1735, #1736, #1742, and #1753.

## Phase behavior

| Phase | Scope | Processed | Done | Sessions | Turns | Time | Time per done |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| A | Consolidation and small local work | 18 | 15 | 38 | 1,393 | 17.3 h | 1.15 h |
| B | #1433 vault split series, stacked | 5 | 5 | 13 | 542 | 8.4 h | 1.68 h |
| C | #1433 independent helpers | 5 | 4 | 10 | 526 | 6.6 h | 1.65 h |
| D | #1435 local dedupe and hoist | 3 | 2 | 7 | 453 | 3.8 h | 1.90 h |
| E | #1438 #1422 | 1 | 1 | 2 | 92 | 1.1 h | 1.10 h |

Total: 37.3 h, 70 sessions, 3,006 turns, 555.7k output tokens, and 1.32M reasoning tokens. The time per done issue rose from 1.15 h in phase A to 1.90 h in phase D. The late phases hit the session and turn limits more often. The slowdown is a candidate for a separate trial (#224).

For comparison, the #1432 run delivered 7 pull requests in 7.2 h. The #1438 trial reached 3 ready pull requests plus 1 draft in 7.8 h. The weekend run delivered 27 done in 37.3 h. The task mixes differ, so these rates are not a controlled comparison.

## What held

- **The checkpoint fix held.** #1378 and #1405 committed before their limits, and the runner published drafts #1755 and #1759. The #1438 trial lost #1421's split to an uncommitted timeout. That did not recur.
- **The restore fix kept worktrees clean.** Every phase summary reports zero dirty worktrees. The gate-generated API files did not enter a commit.
- **The review and CI signal held for completed work.** Every completed pull request has a clean same-model verdict and green hosted checks. No completed pull request was reverted.
- **The stacked vault series did not cascade.** #1366 through #1369 merged. Only #1370 (#1707) has a CI-dispatch gap.
- **The stale-source injection reached every directive.** No worker failed on the stale facts file.

## What failed

- **All failures are stalls or limits, not bad code.** #1337 hit two 900 s idle timeouts. #1411 hit an idle timeout. #1408 hit a 5400 s limit and an idle timeout. #1378 hit the 5400 s limit. #1405 hit the 150-turn limit. The completed pull requests are clean.
- **The phase floor leaves drafts, not parks.** #1378 and #1405 were incomplete at the budget boundary. Their work is preserved as drafts, but the issues remain `triage:ready` and In progress. No park records the stop. This is #221.
- **#1707 has no hosted CI.** The stacked pull request was marked ready and reviewed clean, but the checks never ran. This is #220.
- **The late phases slowed.** Phase D needed 1.9 h per done issue. One session hit the 150-turn limit. A model-server restart or a shorter phase is worth testing (#224).

## The `impl:strong` label

The weekend data supports the shape hypothesis more than the size hypothesis. The M tasks #1409 (JS extraction) and #1422 (JS test refactor) succeeded. The S #1408 and the XS #1411 parked. The prior #1438 M test splits stalled. The label appears to predict a stall-prone task shape, not size. Issue #219 records the paired strong-issue trial.

## Compact tags and toil

- The model used `tags` 23 times, against 3 in the #1438 trial. It made 139 grep-tool calls and 538 reads. Input was 186.9M tokens, cached tokens were unreported, and 355 turns reached 100k or more context.
- The tags use rose, but the context did not fall. The tasks differ from #1438, so this is not a controlled result. Issue #225 proposes a same-task compact-tags trial.
- The toil audit hit Strike 3 on the `gate make check` and then `gate make test` sequence. Phase A had three patterns with 5, 3, and 3 occurrences. Phase C had one with 3. Issue #222 proposes a deterministic gate helper.

## Loose ends and follow-ups

The run left six items for wrap-up:

- The four open ready pull requests: #1707 (CI re-run), #1756, #1758, #1760.
- The two drafts: #1755 and #1759 need review and a ready step.
- The one not-started issue: #1379.
- The three parks: #1337, #1408, and #1411 need a decision. The local model stalled on them. The strong-issue trial (#219) covers the label question.

The runner and skill follow-ups are:

- #220: do not mark a stacked pull request ready without hosted checks.
- #221: finish or park a draft at a phase boundary.
- #222: add a deterministic gate helper for the repeated `make check` and `make test` sequence.
- #223: dispatch the project-facts refresh from the runner.
- #224: measure and recover from the late-run slowdown.
- #225: run a second compact-tags trial on a symbol-navigation task.
- #226: support one authorization to merge a batch of green, clean pull requests.

## Candidate changes

The follow-up issues above are the candidate changes. The record does not decide them. The wrap-up session can finish the six loose items. The runner should not merge on its own.

## Evidence limits

- One run. The task mix differs from the earlier runs.
- Same-model review. No different-model review occurred.
- No coverage measurement.
- The user merged pull requests during the run.
- The final wrap-up is pending. The record states the run-end state.
- The run log is local and not committed.

## Wrap-up

On 2026-11-23 the user authorized one wrap-up session to finish the six loose items and to implement #1379. It ran directly, in single-session mode, with a strong model (`otari-mozilla/deepseek/deepseek-v4.1-flash-1017`), and routed every Git and GitHub write through ghflow as MokaGnome. Parked work and the #219 strong-issue trial stayed out of scope. The run-end state above is unchanged.

| PR | Issue | Merged head | Merge commit | Note |
| --- | --- | --- | --- | --- |
| #1707 | #1370 | `ddb4ce83` | `2eb57244` | Rebased onto `main`; the push triggered the hosted checks that had never run |
| #1756 | #1400 | `3dd7b86c` | `4c65afd1` | Base update, then green CI |
| #1760 | #1422 | `7b237d9e` | `21e106e6` | Base update, then green CI |
| #1758 | #1403 | `fbadf0bc` | `07d56e03` | Base update, then green CI |
| #1755 | #1378 | `852ce525` | `2417ccea` | Draft reviewed, marked ready, base update, green CI |
| #1759 | #1405 | `6d97c412` | `3d912363` | Draft reviewed, marked ready, base update, green CI |
| #1761 | #1379 | `1b0cf241` | `f2c70749` | New PR: newsletter template moved to `template.html` |

**#1707.** The branch was 47 commits behind `main` and conflicted with the merged public `Document` line API. The rebase moved `_sections_ops.py` to `Document.delete_lines` / `Document.insert_lines`; the three moved function bodies are otherwise identical. The rebased head was reviewed and merged. This closes the #220 evidence gap: the ready pull request now has green required checks.

**The other six.** Each head was updated to the base tip with `update-branch`, hosted CI ran green on the updated head, and the merge used the exact-head check. #1755 and #1759 were drafts; each was reviewed against its issue, marked ready (issue moved In review), then merged. #1761 is the new pull request for #1379.

**Final states.** All seven pull requests are merged, and all seven issues are closed and Done: #1370, #1378, #1379, #1400, #1403, #1405, #1422. No open ready pull request and no draft remain from the run.

**Remaining decisions** (parked work was not implemented):

- **#1337** — no branch or commit exists; the dispatch helpers are still in `tools/__init__.py` (512 lines). The park was an idle timeout, not bad code. Retry with a strong model is reasonable: the issue is S and mechanical, with an import-cycle constraint.
- **#1408** — draft #1689 holds a complete refactor with regression tests, but it conflicts and is 50 commits behind. Rebase and review it with a strong model rather than discarding it.
- **#1411** — no branch or commit exists, and the described dead `change` listener is absent at the run base `9c02ef43` and on current `main`; error surfacing runs through the WebSocket `message` listener. Recommend closing as already satisfied after a human confirms.
- **#219** — the strong-issue trial did not start, as instructed. The run's 33 local-ready issues now stand at 30 closed and Done, with #1337, #1408, and #1411 parked. The improvement follow-ups #220, #221, #222, and #223 are merged. #224, #225, #226, and the monitor issue #231 remain open.

**Wrap-up evidence limits.** Review was in-session: #1761 is a same-model self-review, and the other six were reviewed by a different model than the local implementer but not in a fresh, independent context. No live Mattermost or web-UI exercise was run. Every merge needed a base update, so each merged head is a merge commit; hosted CI ran green on each merged head. The run log was not changed.
