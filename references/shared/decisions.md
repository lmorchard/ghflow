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
