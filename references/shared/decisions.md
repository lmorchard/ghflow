# Decisions

Apply these rules when a missing fact or choice affects the task. [Evidence](evidence.md) governs findings and their sources.

## Resolve facts and routine choices

Before reopening a decision after context loss, read existing [Task notes](task-notes.md). Before asking, identify what is missing: a fact, an implementation choice, or a decision about the intended result.

Research discoverable facts in current code, tests, documentation, or other relevant sources. Follow [Evidence](evidence.md#sources-and-revisions) when reusing earlier findings. An unread source is an evidence gap, not a user decision.

Resolve routine, reversible implementation choices from project conventions, current evidence, and confirmed decisions. Apply [Authorization](authorization.md) to the permitted scope. Explain the choice when it affects the result or handoff. Reversibility alone does not settle a product decision.

## Return unresolved decisions

Return an unresolved decision when viable answers change intent, scope, user-visible behavior, compatibility, cost, or permissions. Return disputed findings when current evidence cannot settle a material disagreement. Research can establish the alternatives and their effects. It cannot choose between conflicting user requirements. Do not silently add a requirement. Apply [Authorization](authorization.md) before an action outside the agreed scope.

Ask one focused question at a time. State why the decision is needed. Give the evidence, a recommended answer, and its tradeoff when the evidence supports one. Identify uncertainty that affects the recommendation. Use answers that the user already gave.

Follow [Coordination](coordination.md#roles) for who receives and discusses the question. Continue independent work that does not depend on the answer. Keep dependent work pending until the decision arrives. If a blocker leaves no useful independent work, report it to the parent or user. Apply [Authorization](authorization.md#limits) when an answer is missing.

## Decide in an unattended flow

An unattended request, which the user states, changes what happens to a decision that would otherwise go to the user. It applies to the task that the request runs unattended, such as a burndown, not to a task that prepares one, such as curating the Ready column for tonight's run. It does not change which decisions those are, and it does not widen the endpoint or the permissions.

When the evidence supports a recommended answer, take it and continue. Record the question, the answer, the evidence, and the tradeoff in the task notes and in the PR description under a heading such as "Decisions taken unattended", so that the user can reverse it at review. Do not call an interactive question tool: nobody will answer, and the call waits until it times out.

Park the task instead when no answer is supported, when viable answers differ in user-visible behavior and the evidence does not separate them, or when the choice would widen permissions or scope beyond the authorized flow, such as merge, deployment, deleting branches or data, a system-level install, or a change outside the issue. [express-issue](../tasks/express-issue.md#park-an-issue-in-an-unattended-flow) owns the parking procedure.
