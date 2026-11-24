# Local sufficiency audit

This record answers [#248](https://github.com/lmorchard/ghflow/issues/248): which well-defined issues need a strong model?

The audit uses existing run records. It does not start a new burndown run.

## Facts

- Date: 2026-11-24.
- Audit source: ghflow `9613716`.
- Local model: `lmstudio/qwen3.8-27b-mlx@4bit`.
- Strong model: `otari-local/claude-sonnet-5.5`.
- Review model: `otari-local/claude-opus-5.5`.
- Local attempts: the #1438 trial at `ab0d88d` and the #1729 scavenger run at `9613716`.
- Strong baselines: the #1729 scavenger run at `9613716`.
- Other closed epics: #1434 and #1426 are local-only. #1432 and #1425 have local and strong children. All four are closed.

## Method

1. Select completed and parked janitorial issues with local attempts or strong baselines.
2. Record the label, Size, task shape, preparation evidence, model, outcome, turns, tokens, and review findings.
3. Classify preparation as complete, partial, or missing.
4. Classify the local result against the acceptance bar: pass, fail, park, or quality gap.
5. Separate failures on well-prepared issues from failures on under-prepared issues.
6. Do not use wall time or average model quality.

A well-defined issue has human decisions from `needs-input`, a strong-model `needs-definition` pass, acceptance criteria, tests, and file targets.

The acceptance bar for local sufficiency: the gates pass, tests cover the change, the review finds no blocking defect, the scope matches, and the code is maintainable.

## Decision

- The local label is not a guarantee. Local-labeled M test splits and remote-command work failed, parked, or stayed a draft.
- The strong label is mostly untested locally. The #1729 strong labels used Sonnet. The local model was not tried on them.
- Preparation is good in the sample. The local failures are task-shape and size failures, not definition gaps.
- Keep the local default for S mechanical work. Use a strong fallback for M test splits, remote-command work, and design work until the local-on-strong test runs.
- Do not reclassify the labels yet. Run [#219](https://github.com/lmorchard/ghflow/issues/219) on #1723 and #1731. Add #1727 as a false-strong candidate. Run the #1435 S batch as the local-first test.

## Evidence limits

- One retrospective sample, not a controlled experiment.
- The strong labels were not tested with the local model.
- Some local results used same-model review.
- #1727 and #1728 need a real enrolled host. Environment access confounds their labels.
- #1423 had a stale target. The worker adapted.
- Token counts differ by tokenizer, reasoning style, and tool output.
- Wall time is omitted because it measures hardware and infrastructure.

[report.md](report.md) records the tables and the candidate rubric.
