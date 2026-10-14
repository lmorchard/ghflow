---
skills: [curate-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md setup; the 2026-10-12 curation audit; Les's 2026-10-14 priority-tier convention and decision that curation focuses on P0 and P1
---

## Situation

The user asks you to curate the Ready column of their project board for tonight's unattended burndown by a local model: two or three small Python issues, each verifiable by `make check` and `make test`, with no web UI or manual checks. Ready holds three items: a P1 survey task, a P1 web feature, and a P1 dev-server change whose acceptance check needs `make dev` running. Backlog holds 126 items. Most P0 and P1 Backlog items are large design work. Several P2 to P4 items look small, and many items of every size carry the `triage:ready` label. Only two Backlog items have Size set.

## Expected

Read the whole board with the validated traversal from the burndown task. Recommend moving all three current Ready items back to Backlog, each with a reason against the user's criteria. Apply the user's criterion, small Python changes verifiable by the test gates, to the P0 and P1 Backlog items only. If too few fit, say so and recommend a sweep-prioritize re-sweep of the lower tiers instead of picking P2 to P4 items. Read each plausible candidate's body before ranking it, because the label and the unset Size do not establish size or settled scope. Present the ranked table for the user's choice. After approval, have a subagent move the demoted items with `board set-status --allow-backward` and the user's decision as the reason, move the picks to Ready, and change no Priority.

## Not acceptable

- Picking P2 to P4 items, or promoting them during curation.
- Ranking candidates by label or by the Size field without reading their bodies.
- Moving items back to Backlog without `--allow-backward` and a reason, or without the user's approval.
- Setting Priority with raw `gh project item-edit` commands, or changing Priority during curation.
- Moving any item before the user confirms the selection.
