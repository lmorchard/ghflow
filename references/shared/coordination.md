# Coordination

Apply these rules when delegating tasks or returning their results. [Authorization](authorization.md) supplies permission and scope limits.

## Roles

The **parent** agent owns the conversation with the user. It makes workflow decisions, conducts interviews, and dispatches tasks. A **subagent** does work in the **subject repository**, the project that the task changes. That work includes code changes, commits, pushes, issue and board updates, PRs, review replies, and merges. When a separate identity is configured, subagents follow [Agent identity](identity.md).

A subagent returns questions to the parent instead of interviewing the user or waiting for an answer. Apply [Decisions](decisions.md#return-unresolved-decisions) to frame the question. Apply [Authorization](authorization.md#limits) to missing answers.

For an unpublished implementation handoff, pass the supplied checkout path, branch, base, full tested head, and publication state. Verify the base and head locally before review, as [Evidence](evidence.md#verifying-a-commit) requires. Local verification establishes local existence only. Use remote verification after publication.

In a direct session with no parent, the agent that does the work also talks to the user.

## Handoffs

A coordinator dispatches each task to a subagent, except for PR follow-up owned by the parent as described next. Give the subagent its resolved entry skill, task-reference, and CLI paths, the source checkout revision used for instructions and tools, the target checkout, the subject, current revisions, relevant evidence, confirmed decisions, and authorization limits. Tell it to execute that operation without selecting another. Include unresolved questions only when they affect that task. Require actual results and evidence limits in return. For tasks with [working notes](task-notes.md), carry their exact path and relevant facts in both directions; keep independent reviewer inputs within that reference's limits.

If a needed skill or delegation is unavailable, report the limit. Do not do the subject-repository work in the parent instead, or silently replace a skill's procedure. If nested dispatch hits a capacity limit, let the coordinator finish its handoff and let the parent dispatch the next task. Preserve completed work and recorded model identities across that change.

For continued implementation, checkpoints, and corrections on the same issue, reuse the responsible implementation worker when it is available. Supply changed facts, the current revision, and the notes path instead of replaying unchanged context. A worker can execute successive authorized operations through their task references; each operation keeps its own scope and stopping point. Use a fresh review context when the selected [review plan](review.md) requires it.

When a subagent finishes one task, dispatch the next included task within [existing authorization](authorization.md#use-the-authorization-that-exists). Do not stop and wait for the user to ask what is next.

Keep progress updates in the conversation and durable facts in issues, commits, and PRs. Use [Task notes](task-notes.md) for findings and decisions that support continued execution. A coordinator does not need a custom storage system, scheduler, fixed report format, or approval document.

## PR follow-up ownership

An early draft checkpoint under [Draft PRs and readiness](pr-lifecycle.md) returns to the implementation coordinator. Continue implementation and local review within the agreed scope; do not dispatch review follow-up for that checkpoint.

After ready-for-review PR submission, a delegated delivery coordinator stops and returns the submission handoff to the parent. An intervening coordinator relays that handoff to the parent that owns the user conversation. Include the issue and PR URLs, worktree, branch, base and published head, exact source revisions, check results and their commits, review coverage and model evidence, original review request times and deadlines, review identifiers, chosen endpoint, and authorization limits. Mark follow-up as incomplete when the endpoint includes it.

For an authorized review-follow-up endpoint, the parent directly dispatches [address-pr-review](../tasks/address-pr-review.md) and receives its final report for each PR. Submission alone does not complete that endpoint. Carry [existing authorization](authorization.md#use-the-authorization-that-exists) into the included work. In a direct session with no parent, the agent handling the conversation owns this dispatch.

If another worker updates the PR branch during follow-up, the parent notifies the responsible follow-up worker with the PR, new head, and available change evidence. The worker independently reads the actual current head and reassesses its evidence under [Evidence](evidence.md). The parent does not replace the worker's CI repair or final verification with its own subject-repository actions.

After follow-up, the parent dispatches any remaining authorized task, including [merge-pr](../tasks/merge-pr.md) only for an authorized merge endpoint. Return the verified endpoint result to a queue or parent-issue coordinator before it credits completion or selects dependent work. Keep merge checks and separate merge permission intact.
