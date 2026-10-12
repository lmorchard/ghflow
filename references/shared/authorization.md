# Authorization

Apply these rules to permission and scope for every operation.

## Use the authorization that exists

Use the authorization already given in the conversation. Do not ask for it again because the next task uses a different skill.

An agreed flow, such as issue preparation through publication or delivery through review follow-up, authorizes each task that it includes. Carry that authorization and its limits into every [handoff](coordination.md#handoffs).

Changes that the user reviews or decides stay within the authorized flow. Revisit authorization only when a significant change falls outside the reviewed or authorized scope.

An interview settles decisions. It does not grant or renew permission.

## Limits

An explicit narrower limit takes precedence. Examples are draft-only work, read-only assessment, a selected subset, or a time or cost budget. Do not invent a budget that the user did not give. An unattended request, which the user states, lets the coordinator take a supported recommendation and park the rest, as [Decisions](decisions.md#decide-in-an-unattended-flow) states; it does not widen the endpoint, and it never authorizes merge.

Permission for one action does not imply the next:

- Agreement with an idea does not authorize publishing it.
- Definition, reconsideration, and decomposition do not authorize publication or implementation.
- Issue preparation does not authorize implementation or merge.
- Permission to implement, submit, or address review does not authorize merge.
- A favorable review does not authorize merge. See [Review](review.md).
- Delivery does not authorize deployment or cleanup, such as deleting branches or worktrees.

Never infer a decision or a permission from silence.
