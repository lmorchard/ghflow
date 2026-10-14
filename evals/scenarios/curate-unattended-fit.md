---
skills: [curate-ready-queue]
source: docs/research/trials/2026-10-14-unattended-burndown-2.md; the 2026-10-13 OpenCode curation that ranked #149 as an alternate
---

## Situation

The user asks: "Curate the Ready column for tonight's unattended burndown, two or three issues." Ready is empty. The project facts file names `make check` and `make test` as the gates. You read four Backlog candidates:

- A: add two optional parameters to a tool, with mock tests specified; decisions recorded; estimate 120 to 190 lines.
- B: change a confirmation message, with four named tests; the issue says "Open: none"; estimate 80 to 140 lines.
- C: restart the dev server when a config file changes. Unit tests for the file filter are specified, and the acceptance criterion reads "With `make dev` running, an edit to the config file restarts the server." Decisions recorded; estimate 50 to 90 lines.
- D: prune resolved errors from context history, approved spec with named tests; estimate 150 to 240 lines.

## Expected

Apply the unattended-fit criterion, since the request names an unattended run. Reject C, because its acceptance criterion needs a running dev server, even though unit tests exist. Recommend A and B. Offer D as the third pick with a flag that its estimate is near the top of the range and may take much longer than the others. Show each candidate's result per condition, and wait for the user's approval before any board change.

## Not acceptable

- Ranking C as a pick or an alternate because it has unit tests.
- Treating D like the others without flagging its size.
- Selecting by priority instead of fit.
- Moving any item before the user approves.
