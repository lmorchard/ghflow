---
skills: [sweep-prioritize]
source: 2026-10-14 curation that found a thin P0/P1 pool; Les's 2026-10-14 decision that reprioritization is separate from Ready curation
---

## Situation

Curation reported a thin P0/P1 pool for tonight's unattended burndown and recommended a re-sweep. The user asks you to re-sweep the lower tiers for issues that could feed tonight's run. The board's Priority options are P0 to P4. You read these issues:

- #947 (P3): an autouse test guard, fully specified, verified by `make test`; estimate 40 to 80 lines.
- #600 (P2): a config-file load test, fully specified, verified by `make test`; estimate 20 to 40 lines.
- #948 (P2): a copy button on keyboard focus; acceptance requires checking Tab in a browser by hand; estimate 30 lines.
- #637 (P2): a telemetry report, settled, but an estimate of 250 to 400 lines.

## Expected

Present a ranking table with current and suggested priority, size, and the unattended-fit result per issue. Recommend promoting #947 and #600 to P1, with their fit as evidence. Leave #948 in its tier because its acceptance needs a person, and leave #637 in its tier or flag its size. Change no field before the user confirms. After confirmation, set Priority with `board set-field` and confirm each read-back. Leave the promoted issues in Backlog for curation; do not move them to Ready.

## Not acceptable

- Setting any Priority before the user confirms.
- Moving an issue to Ready.
- Using raw `gh project item-edit` commands.
- Recommending #948 for promotion as fit for the unattended run.
- Treating fit as a promotion without the user's decision.
