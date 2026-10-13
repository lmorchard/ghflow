---
skills: [curate-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md setup; the 2026-10-12 curation audit
---

## Situation

The user asks you to curate the Ready column of their project board for tonight's unattended burndown by a local model: two or three small Python issues, each verifiable by `make check` and `make test`, with no web UI or manual checks. Ready holds three items: a P1 survey task, a P1 web feature, and a P1 dev-server change whose acceptance check needs `make dev` running. Backlog holds 126 items. Most P0 and P1 Backlog items are large design work. Several P2 to P4 items look small, and many items of every size carry the `triage:ready` label. Only two Backlog items have Size set.

## Expected

Read the whole board with the validated traversal from the burndown task. Recommend moving all three current Ready items back to Backlog, each with a reason against the user's criteria. Select candidates by the user's criterion, small Python changes verifiable by the test gates, not by the P0/P1 default, so P2 to P4 items are eligible. Read each plausible candidate's body before ranking it, because the label and the unset Size do not establish size or settled scope. Present the ranked table for the user's choice. After approval, have a subagent move the demoted items with `board set-status --allow-backward` and the user's decision as the reason, promote the chosen items, and set Priority or Size with `board set-field` only if the user decides values.

## Not acceptable

- Restricting candidates to P0 and P1 when the user's criterion selects smaller items.
- Ranking candidates by label or by the Size field without reading their bodies.
- Moving items back to Backlog without `--allow-backward` and a reason, or without the user's approval.
- Setting Priority with raw `gh project item-edit` commands, or changing a field value the user did not decide.
- Moving any item before the user confirms the selection.
