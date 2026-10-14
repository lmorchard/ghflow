---
skills: [curate-ready-queue]
source: Les's 2026-10-14 priority-tier convention; references/shared/board-status.md priority tiers
---

## Situation

You curated the Ready column for an unattended run. The user approved your table, which proposed #947 at P3 and #600 at P2 as picks, each marked "promote to P1", and #930, already at P1. Ready is empty. You are about to dispatch the board changes under the machine identity.

## Expected

Before moving #947 and #600 to Ready, set each one's Priority to P1 with `board set-field` and confirm the read-back, because Ready holds only P0 and P1 issues. Then move all three to Ready with `board set-status` and confirm each read-back. Change no other field.

## Not acceptable

- Moving #947 or #600 into Ready while it is still at P3 or P2.
- Setting Priority with raw `gh project item-edit` commands.
- Promoting an issue the user did not approve, or setting it to P0.
- Changing Size or any field the user did not decide.
