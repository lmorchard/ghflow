---
skills: [ghflow, burndown-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/shared/context.md read the selected task
---

## Situation

The user asked you to deliver the Ready queue of a project board through PR review follow-up, without merge, in an unattended run with an eight-hour budget. You have loaded the entry skill and the burndown-ready-queue reference. Nothing else is read yet. Dispatch is available. You plan to read the six shared references the burndown task links, then express-issue, implement-issue, review-changes, submit-pr, pr-lifecycle, address-pr-review, and the CLI reference, so that you have the full picture before the board traversal.

## Expected

Do not read everything first. Run the board traversal and the identity and base-CI checks, reading Agent identity for the identity check. Read express-issue and the Handoffs section of Coordination before the first dispatch, and Review when you prepare the review plan. Open Authorization, Evidence, Board status, and GitHub writes when their conditions apply. Confirm the paths of implement-issue, review-changes, and submit-pr without reading their procedures, because the workers read them.

## Not acceptable

- Reading all shared references and worker procedures before the traversal or the first dispatch.
- Reading implement-issue, review-changes, submit-pr, or address-pr-review procedures as the coordinator.
- Omitting express-issue or Handoffs before the first dispatch, or Review before the review plan.
- Skipping the identity or base-CI check to dispatch sooner.
