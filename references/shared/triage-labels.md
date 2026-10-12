# Triage labels

Triage labels record where an open issue stands in refinement. Give each triaged issue exactly one `triage:*` label. Replace the old label when the state changes. Apply [GitHub writes](github-writes.md) to each label change.

| Label | Meaning | Next step |
|---|---|---|
| `triage:needs-input` | A product or design decision from the user blocks the issue. | [sweep-needs-input](../tasks/sweep-needs-input.md) |
| `triage:needs-definition` | The goal is settled and the issue can be specified now against current code. | [sweep-needs-definition](../tasks/sweep-needs-definition.md) |
| `triage:blocked` | The issue cannot be refined until other open issues land. | [sweep-blocked](../tasks/sweep-blocked.md) |
| `triage:parked` | Nobody intends to work on the issue now, such as a parking lot or a parent whose children carry the work. | None. Revisit only on request. |
| `triage:ready` | Scope and verification criteria are concrete enough to implement. | Prioritize or implement. |
| `triage:agent-closed` | An agent closed the issue with cited evidence. | [sweep-audit-closed](../tasks/sweep-audit-closed.md) |

`triage:needs-input` and `triage:needs-definition` mean that someone can act now. Keep blocked and parked issues off those labels, so that a query for them shows only actionable work.

## Blocked issues

An issue is blocked when its refinement depends on an open issue: the specification would describe code, a contract, or a decision that the other issue will change or supply. An open question for the user is `triage:needs-input`, not a blocker.

Record each blocker as a native GitHub blocked-by relationship, not only in text. The relationship is the source that [sweep-blocked](../tasks/sweep-blocked.md) reads to return the issue to `triage:needs-definition`. Check the installed `gh issue edit` help for the blocked-by option. If the relationship cannot be set, report the failure and leave the issue on its previous label.

A blocked issue can carry an outline that names the contract it consumes, its scope, and its acceptance criteria, without file targets. Note in the outline that the full specification waits for the blocker.

Do not label an issue blocked when only part of it waits. If an independent part can be specified now, propose a split instead.

## Parked issues

Park an issue only on the user's decision or when it is a parent whose open children carry all of its work. State the reason in a comment. A parked issue is not closed: it records an idea or a parent's scope.

## Parked deliveries

An unattended delivery that cannot settle a question, or that hits a blocker it cannot clear, replaces `triage:ready` with `triage:needs-input`, posts the question or blocker as a comment on the issue, and leaves its draft PR and the In progress board status in place. The label puts the issue in the same view as other issues that need the user. [sweep-needs-input](../tasks/sweep-needs-input.md) resolves it, and the delivery resumes from the PR. This use of `triage:needs-input` is distinct from `triage:parked`, which marks an issue nobody intends to work on.
