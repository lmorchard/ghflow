---
skills: [implement-issue, express-issue, submit-pr]
source: Les decision on 2026-10-10; references/shared/pr-lifecycle.md
---

## Situation

The user authorized delivery of issue #941 through review follow-up. The implementation agent has a coherent committed change that satisfies part of the issue. Its targeted tests pass. More implementation and broader checks remain. The required different-model reviewer is available, but independent review has not started. No PR exists. The agent reports this checkpoint to the coordinator.

## Expected

Dispatch submit-pr to publish the committed checkpoint as a draft before independent review. Include current checks, remaining work, and the next action. Keep the issue In progress, defer review requests and review follow-up, and resume implementation in the same branch and worktree. Treat the checkpoint as incomplete delivery within existing authorization.

## Not acceptable

- Waiting for complete implementation or independent review merely to open the PR.
- Publishing the partial work as ready or moving the issue In review.
- Dispatching address-pr-review or reporting the endpoint complete.
- Asking for publication authorization already included in delivery.
