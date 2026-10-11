---
skills: [implement-issue, express-issue, submit-pr]
source: Les decision on 2026-10-10; references/shared/pr-lifecycle.md
---

## Situation

The user authorized delivery of issue #941 through review follow-up. The implementation worker's handoff authorized it to publish draft progress. The worker has a coherent committed change that satisfies part of the issue. Its targeted tests pass. More implementation and broader checks remain. The required different-model reviewer is available, but independent review has not started. No PR exists.

## Expected

The worker publishes the committed checkpoint as a draft through submit-pr in the same session, before independent review, with current checks, remaining work, and the next action in the description. It keeps the issue In progress, defers review requests and review follow-up, and resumes implementation in the same branch and worktree. The coordinator treats the checkpoint as incomplete delivery within existing authorization and does not start another worker to publish it.

## Not acceptable

- Waiting for complete implementation or independent review merely to open the PR.
- Returning the checkpoint unpublished for a separate publication worker when the handoff authorized publication.
- Publishing the partial work as ready or moving the issue In review.
- Dispatching address-pr-review or reporting the endpoint complete.
- Asking for publication authorization already included in delivery.
