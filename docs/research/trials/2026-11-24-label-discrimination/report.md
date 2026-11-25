# Report: do `impl:local` and `impl:strong` discriminate on quality?

Date: 2026-11-24
Issue: [ghflow#219](https://github.com/lmorchard/gh-project-workflow/issues/219)

## Result

The labels did not discriminate on implementation quality in this sample.

Both arms produced implementations of similar size and shape, passed the same gates, and failed review in the same places. On #1723 both arms need work, and the main blocking defect is the same in both diffs. On #1731 both arms are minor, with the same themes: an unused label reader, a narrower recipe search, and JSON/exit-code edge cases.

The strong model was not faster. On the two paired issues the strong sessions used 23 and 26 turns in 6 m 58 s and 7 m 51 s; the local sessions used 22 and 24 turns in 8 m 15 s and 7 m 09 s. The local model also produced comparable output volume: 43,828 and 36,236 output tokens against 47,393 and 56,672.

The rest of this report gives the evidence, maps it to the issue's decision rule, and states the recommendation.

## Paired comparison: #1723

| | Local (#1784) | Strong (#1793) |
| --- | --- | --- |
| Diff | +672/−102, 4 files | +726/−103, 4 files |
| Turns / wall | 22 / 8 m 15 s | 23 / 6 m 58 s |
| Max input | 99,979 | 92,965 |
| Output | 43,828 | 47,393 |
| Focused tests | 27 passed | 27 passed |
| Gates | `make check` pass, CI green | `make check` pass, CI green |
| Review | needs-work, 1 blocking, 10 non-blocking | needs-work, 2 blocking, 9 non-blocking |

The blocking defect is the same. The host listing script runs the container engine's `ps` and `volume ls`, and any failure marks the whole host unreachable, including its native lease files. On a Mac with `podman machine` stopped, native environments can no longer be created and existing native workspaces are not reaped. The issue asks the native occupancy check to read lease files on the host; it does not make that check depend on container engine health. Both reviewers found this and both called it blocking.

The strong diff has a second blocking finding: native workspaces created before the change have no `.scavenger-lease.json`, so the first reconcile drops them from the cache and they become orphans. The local diff has the same behavior. The local review graded it non-blocking; the strong review graded it blocking. That is a severity judgment, not a difference in the code. The two diffs are close on this issue, and the verdict difference overstates the gap.

Both diffs also share the same non-blocking themes: serial fleet scans on common paths, an occupancy check that is not atomic, and test files that use function-local stdlib imports.

The strong implementation is not cleaner. It is slightly larger and adds a second blocking finding for a defect both diffs contain.

## Paired comparison: #1731

| | Local (#1786) | Strong (#1794) |
| --- | --- | --- |
| Diff | +734/−157, 7 files | +990/−169, 7 files |
| Turns / wall | 24 / 7 m 09 s | 26 / 7 m 51 s |
| Max input | 98,612 | 109,831 |
| Output | 36,236 | 56,672 |
| Focused tests | 37 passed | 63 passed |
| Gates | `make check` pass, CI green | `make check` pass, CI green |
| Review | minor, 0 blocking, 10 non-blocking | minor, 0 blocking, 9 non-blocking |

Both diffs meet the issue's main requirements: the hardcoded `/home/lmorchard` path is gone, the recipe directory order is implemented, labels are renamed with a legacy reader, every CLI command takes `--json`, `wake`/`exec-native`/`env-info` exist, and `SKILL-cli.md` documents shell-only use.

The findings also match. Both reviewers note that the new label reader has no production caller yet. Both note that the recipe search is narrower for some layouts: the local review flags `workspace/skills/scavenger/dockerfiles`, the strong review flags `<workspace>/dockerfiles` when `recipes_dir` is set. Both note gaps in the JSON and exit-code contract for edge cases.

The strong diff is larger and carries more CLI tests (63 against 37). It also introduces more surface: a shared `wake_host`, a `CLIError`/`main(argv)` structure, and new commands with their own edge cases. The local diff is smaller and leaves more CLI paths untested. Neither is clearly better on the issue's requirements.

## The `impl:local` cell

#1725 and #1726 are `impl:local` issues. The strong arm did not implement them, so this cell has only the local arm:

| Issue | Diff | Review |
| --- | --- | --- |
| #1725 | +258/−6, 6 files | minor, 0 blocking, 9 non-blocking |
| #1726 | +307/−37, 5 files | minor, 0 blocking, 8 non-blocking |

Both are acceptable with small fixes. #1725's reviewer found a real risk that the new `--network=default` flag changes behavior on rootless Podman, and that log options are chosen by engine name rather than log driver. #1726's reviewer found a docstring that contradicts the return value, no escape hatch for leases on hosts that never return, and untested tool-layer failure branches.

These results establish a local ceiling for the local-labeled cell. They do not test the strong model on local-labeled work.

## Metrics

| Issue | Arm | Turns | Max input | Output | Wall |
| --- | --- | ---: | ---: | ---: | ---: |
| #1725 | local | 70 | 107,726 | 17,309 | 68 m 29 s |
| #1726 | local | 55 | 117,707 | 13,351 | 68 m 14 s |
| #1723 | local | 22 | 99,979 | 43,828 | 8 m 15 s |
| #1723 | strong | 23 | 92,965 | 47,393 | 6 m 58 s |
| #1731 | local | 24 | 98,612 | 36,236 | 7 m 09 s |
| #1731 | strong | 26 | 109,831 | 56,672 | 7 m 51 s |

- No session reached the 150-turn or 5400-second limit.
- All sessions stayed below the 118k-token context warning.
- No session reported cached tokens, so cache effects were not measured.
- The local #1725/#1726 sessions took about 68 minutes each; the local #1723/#1731 sessions took 7 to 8 minutes. The difference is task mix, not a paired comparison, and the strong arm did not run #1725/#1726.
- On the paired issues, strong saved 1 m 17 s on #1723 and cost 42 s more on #1731. The spread is within run-to-run noise for one run per arm.

## Gates

Every head passes `make check` and has green hosted CI (`lint-and-test`, `js-test`, `browser-test`, `check-tui`). Focused scavenger tests pass on every head.

The full suite has four `tests/test_host_metrics.py` failures on this macOS host for every head, including the base. The strong #1731 worker saw one extra `tests/test_npm_policy.py` failure in its full-suite run; it passes alone and did not recur in CI. No arm produced a red gate that the other arm did not.

## Decision rule

The issue's rule:

- **Local is clean on `impl:strong` and strong is clean:** the label does not discriminate.
- **Local has more blocking findings or fails on `impl:strong`, and strong is clean:** the label discriminates.
- **Both are clean on `impl:local`:** expected ceiling, not evidence.
- **Strong fails on `impl:local`:** not a model-fit discriminator in the expected direction.

Observed:

- Neither arm is clean on `impl:strong`. Both #1723 diffs need work, with the same main defect. Both #1731 diffs are minor.
- The local arm does not have more blocking findings on the core defect. The strong diff has one extra blocking finding for a defect both diffs contain.
- The `impl:local` cell has only local results; both are minor, not clean.
- The strong arm did not run on `impl:local`.

This is a no-discrimination result, with the caveat that both arms sit below clean on #1723. The label did not separate better from worse work; it separated two implementations that need the same correction.

## Decision: narrow

Keep `impl:local` and `impl:strong` as routing labels for model provider, cost, and privacy. Remove any quality expectation from them.

Why narrow rather than keep:

- The runner uses the labels as keys in `runner.json` to pick a model. That use is real and unchanged.
- The labels are also read as fit or strength claims. `docs/setup.md` calls `impl:local` "local-fit" and shows `impl:strong` mapped to a cloud model. The janitorial report treats `impl:strong` as a stall-prone shape. This trial does not support a quality reading.
- Two issues per cell cannot establish a general rule, but they can falsify a strong claim. A strong model that was expected to be cleaner produced the same defect and one more blocking finding.

Why not reclassify now:

- Renaming the labels touches `runner.json`, the board, the docs, and every trial record. The evidence does not yet justify that churn.
- Narrowing the meaning is reversible and keeps the provider mapping working.

Reclassify if a later sample shows that the quality implication persists in prompts or in operator behavior. A rename such as `impl:cloud` would make the cost/provider meaning explicit.

### Concrete changes

1. In `docs/setup.md`, say the labels select the model provider and cost, not expected quality. Keep the `runner.json` example.
2. In the skills, do not treat `impl:strong` as a reason for less review. Both arms get the same gates and the same review.
3. In `docs/research/trials/README.md`, link this record and state the result.
4. Do not change the labels or the runner map in this PR.

## Human calibration

Not performed in this run. The automated reviews used one model and one prompt, so a human check is still the guard against a shared reviewer blind spot.

An operator spot-check did confirm two of the automated findings against the diffs:

- Local #1781 (`diff-1`): `container_limit_flags` always emits `--network=<mode>`, so the default path now sends `--network=default` where the base sent no flag. The concern about rootless Podman network names is valid.
- Strong #1793 (`diff-2`): `list_host_envs` returns `None` when any section contains `---ERROR---`, and the native create path raises on `None`. The blocking finding about native work depending on container engine health is valid.

This is not human calibration. It checks two findings, not the full review.

Set aside for human calibration:

- One local diff: #1781 (`diff-1`, #1725).
- One strong diff: #1793 (`diff-2`, #1723).

A human should read both anonymized diffs in [`reviews/`](reviews/) with the same prompt and compare the verdicts with the automated ones. The local #1781 review is a useful calibration because its findings are specific and checkable: the `--network=default` behavior change and the log-driver assumption.

## Limits

- **Sample size.** Two issues per cell, one epic, one run per arm. Directional evidence only.
- **Retrospective strong arm.** The strong work was written after the local work, by a different harness (manual OpenCode, not the queue runner). The prompt, model, gates, and limits match; the monitor, auto-commit, and PR submission do not.
- **Different local conditions.** The local arm ran on 2026-11-23/24 with a different server state and a per-issue model map. Its original reviews were same-model for #1725/#1726 and Opus for #1723/#1731. The trial re-reviewed every diff under one prompt to remove that difference.
- **Diff-only review.** The reviewer did not inspect the repository or run tests. It can miss a defect that needs surrounding code and can over-weight a local hunk. Both arms were reviewed the same way.
- **No live fleet.** No diff was exercised against real hosts. The manual Verify steps that need a fleet were not run for either arm.
- **Independence exposure.** The strong sessions read issue comments that named the local branches and a run-narrative link. They did not read the branches, the PRs, or the discussion. The local implementation was not in the worktree or the handoff.
- **Cached tokens.** No session reported cached tokens, so cost per arm is not measured beyond output tokens and wall time.
- **Reviewer model.** One reviewer model for all six diffs controls consistency but leaves a shared blind spot. Human calibration was not performed.
