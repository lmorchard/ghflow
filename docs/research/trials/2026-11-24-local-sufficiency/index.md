# Local sufficiency audit

This record answers [#248](https://github.com/lmorchard/ghflow/issues/248): which well-defined issues need a strong model?

The audit uses existing run records. It does not start a new run.

## Facts

- Date: 2026-11-24.
- Audit source: ghflow `9613716`.
- Local model: `lmstudio/qwen3.8-27b-mlx@4bit`.
- Strong model: `otari-local/claude-sonnet-5.5`.
- Reviewer: `otari-local/claude-opus-5.5`.
- [#219](https://github.com/lmorchard/ghflow/issues/219) label-discrimination trial: [PR #246](https://github.com/lmorchard/ghflow/pull/246), head `3189903`, open. The result comment is on #219.
- #1438 local trial: `ab0d88d`.
- 2026-11-21 weekend run: the janitorial burndown record.
- #1729 run: `9613716`. Local PRs #1781 to #1786.

The #219 trial compared local and strong implementations of #1723 and #1731. It also recorded the local-only #1725 and #1726. Its decision is **narrow the labels**.

## Method

1. Read the #219 paired trial, the #1438 local trial, the weekend run, and the #1729 run.
2. Record the label, Size, task shape, preparation, model, outcome, turns, and tokens.
3. Classify preparation as complete, partial, or missing.
4. Classify each result against the acceptance bar: pass, fail, park, or quality gap.
5. Separate failures on well-prepared issues from failures on under-prepared issues.
6. Do not use wall time or average model quality.

A well-defined issue has human decisions from `needs-input`, a strong-model `needs-definition` pass, acceptance criteria, tests, and file targets.

The acceptance bar: the gates pass, tests cover the change, the review finds no blocking defect, the scope matches, and the code is maintainable.

## Decision

- **The labels do not predict implementation quality.** The #219 paired trial found local and strong comparable on #1723 and #1731. The strong arm was not cleaner and was not faster.
- **The local model did the strong-labeled #1729 issues.** It produced #1723, #1727, #1728, and #1731. The strong label did not prevent local work. #1728 still needs a real-host check.
- **The local label is not a guarantee.** Local M test splits and remote-command work stalled, parked, or stayed a draft. The weekend S and XS issues #1337, #1408, and #1411 parked. The failures are stalls, limits, and task shape, not bad code.
- **Preparation is mixed.** #1411 had no target at the run base. #1423 had a stale target. The well-defined M test splits and the remote-command issue still stalled. Preparation is necessary, not sufficient.
- **The labels need a change.** Narrow them to routing labels for provider, cost, privacy, and environment. Remove quality expectations. The #219 record owns the trial. This audit adds the shape and preparation evidence.
- Use the local model first for S and M mechanical work. Use the local model first with a strong fallback on stall for M test splits, remote-command work, and design. Use a person or a strong environment for manual and real-host checks.
- Do not run another label trial. #219 is the decisive check. The #1435 S batch remains a local-first routing test.

The answer to #248: no well-defined issue in this sample needed a strong model for implementation quality. The strong model was comparable, not better. A strong fallback helps with stalls, provider needs, and manual environments.

## Evidence limits

- The #219 record is an open PR, not merged. Its result comment is on #219.
- #219 used two issues per cell, one epic, and one run per arm.
- The strong arm was retrospective and manual.
- #1438 and #1729 used same-model review. #219 used an anonymized Opus review.
- The weekend run had one run and a changing task mix.
- #1422 and #1409 have no per-issue token data in the weekend record.
- #1337, #1408, and #1411 parked. #1411 was under-prepared.
- No diff ran against a live fleet. Manual checks are unverified.
- The closed epics #1434, #1432, #1425, and #1426 have no per-issue data. #1432 and #1425 have strong children.
- Token counts differ by tokenizer, reasoning style, and tool output.
- Wall time is omitted because it measures hardware and infrastructure.

[report.md](report.md) records the tables, findings, and rubric.
