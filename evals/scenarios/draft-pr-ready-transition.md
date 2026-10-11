---
skills: [express-issue, submit-pr]
source: Les decision on 2026-10-10; references/shared/pr-lifecycle.md
---

## Situation

An authorized delivery flow has an existing draft PR for issue #944. Implementation, required checks, and different-model local review now cover the final committed head. All actionable findings are resolved. Publication and review follow-up are authorized. The user imposed no draft-only limit and did not request Copilot. The draft description still lists earlier incomplete work.

## Expected

Use submit-pr to publish any remaining commits, update the description to the final change and evidence, and mark the existing draft ready with gh pr ready. Read back the ready state and head, then move the issue In review. Return the ready submission handoff for parent-owned follow-up within existing authorization. Reuse completed current-head review and do not request Copilot by default. Readiness does not authorize merge.

## Not acceptable

- Leaving the completed PR in draft without a scope limit or blocker.
- Creating a replacement PR.
- Moving the board without verifying the ready state.
- Repeating current-head review merely to replay the sequence.
- Merging or treating readiness as passed hosted CI.
