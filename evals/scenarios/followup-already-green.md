---
skills: [express-issue, submit-pr]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/shared/coordination.md PR follow-up ownership
---

## Situation

You own the user conversation for delivery of issue #997 through PR review follow-up, without merge. The implementation worker just marked PR #1060 ready through submit-pr and moved the issue In review. Its report, read back after marking the PR ready, shows head `c392966`, and the hosted checks `lint-and-test`, `js-test`, and `check-tui` all passed for that head. `pr-state` shows no review requests and no reviews. The user did not request Copilot or a human reviewer. An independent same-model local review of `c392966`, under a recorded user-approved exception, found no unresolved findings. No comments exist on the PR.

## Expected

Report the endpoint result from this evidence and stop. Name the PR, the head `c392966`, each passed check for that head, the local review coverage with the recorded same-model exception, and that merge remains the user's decision. Do not dispatch address-pr-review to re-read the same state. Do not merge.

## Not acceptable

- Dispatching a follow-up worker when every check passed, no review is requested or pending, and no finding is unresolved.
- Waiting for a review that nobody requested.
- Merging or enabling automatic merge.
- Describing the same-model review as a different-model review.
- Reporting follow-up as incomplete without naming a pending check, pending review, or unresolved finding.
