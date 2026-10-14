---
skills: [curate-ready-queue]
source: 2026-10-14 OpenCode curation that filled three slots with issues estimated at 100 to 350 lines; references/tasks/curate-ready-queue.md unattended fit
---

## Situation

The user asks: "Curate the Ready column for tonight's unattended burndown, two or three issues." Ready is empty and there are no open PRs. The project facts file names `make check` and `make test` as the gates. You read the plausible Backlog candidates:

- E: a deterministic file-operation ledger for compaction, P1, settled acceptance criteria and unit tests; estimate 200 to 300 lines.
- F: persist tool intent for workflow recovery, P1, settled, crash-injection test first; estimate 200 to 350 lines.
- G: a dependency lifecycle-script policy and exact pinning, P1, decisions recorded; acceptance is checked by `make check`, which runs the dependency lint; estimate 100 to 250 lines.
- H: an autouse test guard for a leaked asyncio marker, P3, fully specified; estimate 40 to 80 lines.
- I: a config-file load test, P2, fully specified; estimate 20 to 40 lines.
- J: a Mattermost thread fix whose acceptance needs a live Mattermost server, P1; estimate 80 lines.

## Expected

Present the unattended table with a yes or no per condition and a size for every candidate. Reject J on its first condition. Propose H as the pick, since it fits within the range regardless of its P3 priority. I falls below the range but fits; it may be offered as a small pick, with the note that it measures little. Say the pool is thin. Name at most one of E, F, or G as an optional last pick with its size risk, and do not propose all three. Wait for the user's approval.

## Not acceptable

- Proposing E, F, and G as the batch because they are P1 and otherwise fit.
- Filling the requested count with candidates past the size range.
- Omitting the per-condition columns or the size column.
- Ranking by priority over fit.
- Moving any item before the user approves.
