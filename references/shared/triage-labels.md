# Triage labels

Triage labels record where an open issue stands in refinement. Give each triaged issue exactly one `triage:*` label. Replace the old label when the state changes. Apply [GitHub writes](github-writes.md) and [Agent identity](identity.md#running-commands-under-the-identity) to each label change.

[Triage state](triage-state.md) defines the classification vocabulary, the assessment comment, the closure rule, and the evidence rules. This file covers only what each label means and how to record a park.

| Label | Meaning | Next step |
|---|---|---|
| `triage:needs-input` | A product or design decision from the user blocks the issue. | [sweep-needs-input](../tasks/sweep-needs-input.md) |
| `triage:needs-definition` | The goal is settled and the issue can be specified now against current code. | [sweep-needs-definition](../tasks/sweep-needs-definition.md) |
| `triage:blocked` | The issue cannot be refined until other open issues land. | [sweep-triage](../tasks/sweep-triage.md) `--queue blocked` |
| `triage:parked` | Nobody intends to work on the issue now, such as a parking lot or a parent whose children carry the work. | [sweep-triage](../tasks/sweep-triage.md) `--queue parked` |
| `triage:ready` | Scope and verification criteria are concrete enough to implement. | Prioritize or implement. |
| `triage:agent-closed` | An agent closed the issue with cited evidence. | [sweep-audit-closed](../tasks/sweep-audit-closed.md) |

`triage:needs-input` and `triage:needs-definition` mean that someone can act now. Keep blocked and parked issues off those labels, so that a query for them shows only actionable work.

## Blocked issues

An issue is blocked when its refinement depends on an open issue: the specification would describe code, a contract, or a decision that the other issue will change or supply. An open question for the user is `triage:needs-input`, not a blocker.

Record each blocker as a native GitHub blocked-by relationship, not only in text. **The relationship is the fact and the label is a claim**; `ghflow triage status` reads the edges and reports a label whose edges have all closed as `label_stale`. Check the installed `gh issue edit` help for the blocked-by option. <!-- allow-bare-gh: names the command for its help text, not a run instruction --> If the relationship cannot be set, report the failure and leave the issue on its previous label.

Do not read blocked-by edges with `gh issue view --json blockedBy`: that field does not exist, and the read fails with `Unknown JSON field` on current `gh`. Use `ghflow triage status` or the GraphQL `blockedBy` connection.

A blocked issue can carry an outline that names the contract it consumes, its scope, and its acceptance criteria, without file targets. Note in the outline that the full specification waits for the blocker.

Do not label an issue blocked when only part of it waits. If an independent part can be specified now, propose a split instead.

## Parked issues

`triage:parked` means **"needs more discussion or consideration — set it aside for now."** It is a deliberate shelf, not a way out of a loop. Nothing in triage acts on a parked issue, it never reaches the Ready queue, and the user reviews the parked set on their own schedule through the board view.

Parking requires the user's intent. An agent may park on the user's decision, or when a parent's open children carry all of its remaining work. An agent may **not** park an issue to silence a sweep, to avoid a hard classification, or to stop a question from recurring — those are what the closure rule and the attempt counter are for. Using the label as a loop-escape hatch makes the parked set meaningless: it stops being "things we chose to set aside" and becomes "things triage gave up on," which no one can then review.

State the reason in a comment. A parked issue is not closed: it records an idea or a parent's scope.

### What parked is not

Three things look like parking and are not:

| Looks like parking | Actually |
|---|---|
| An epic whose children carry the work | A **container**, not a shelf. Its state derives from the children rollup. Remove `triage:parked`; the board selection already exempts parents with open children. |
| An issue waiting on another issue | **Blocked** — `triage:blocked` with a native blocked-by edge. |
| A question the user has now twice declined to answer | A **failing needs-input loop**. Raise the attempt counter; do not shelve it quietly. |

### Record a revisit trigger

A park reason that cannot be tested is a park that outlives its reason, because nothing will ever reopen the question. Every park comment names **which kind of park it is**, so [sweep-triage](../tasks/sweep-triage.md) `--queue parked` knows what to check:

| Kind | What the comment must name | Revisit trigger |
|---|---|---|
| **Routing** | The capability, model class, label, or gate being waited on | That condition changing. Does not expire by time, so the comment must name something checkable. |
| **Decision** | The decision and who made it, and what still needs considering | None on a schedule. Revisited when the user next reviews the parked view, or when a concrete change contradicts the stated reason. |

There is no parent kind. A parent is not parked; its state derives from its children, and the board selection exempts it while they are open.

Prefer the kind that has a checkable condition. "Nobody wants this now" cannot be re-examined and will sit forever; "gated on `impl:strong`, which no available model satisfies" can be re-examined and will clear on its own the day it stops being true.

An issue parked without a stated reason is treated as unexplainable by the sweep, which reports it rather than acting on it. Say which kind it is and what would change your mind.

## Parked deliveries

An unattended delivery that cannot settle a question, that hits a blocker it cannot clear, or that is in progress when its time budget ends, replaces `triage:ready` with `triage:needs-input`, posts the question, blocker, or remaining steps as a comment on the issue, and leaves its draft PR and the In progress board status in place. The label puts the issue in the same view as other issues that need the user. [sweep-needs-input](../tasks/sweep-needs-input.md) resolves a question or blocker. A park for time has nothing to resolve. When the delivery resumes from the PR with no open question, it replaces `triage:needs-input` with `triage:ready` before it continues.
This use of `triage:needs-input` is distinct from `triage:parked`, which means the issue needs more discussion or consideration and has been set aside for the user's own periodic review.

The park comment names the next step. For a well-defined issue, suggest a retry with a different local model or a person. For a partial or missing preparation, suggest a preparation fix first. For a time park, resume with the local model. Do not suggest a cloud model.
