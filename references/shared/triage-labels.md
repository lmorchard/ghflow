# Triage labels

Triage labels record where an open issue stands in refinement. Give each triaged issue exactly one `triage:*` label. Replace the old label when the state changes. Apply [GitHub writes](github-writes.md) and [Agent identity](identity.md#running-commands-under-the-identity) to each label change.

[Triage state](triage-state.md) defines the classification vocabulary, the assessment comment, the closure rule, and the evidence rules. This file covers only what each label means and how to record a park.

| Label | Meaning | Next step |
|---|---|---|
| `triage:needs-attention` | The autonomous pass could not reach a specification or a closure alone; one product, design, or tradeoff decision needs the user's attention in a live session. | [sweep-needs-attention](../tasks/sweep-needs-attention.md) |
| `triage:parked` | Nobody intends to work on the issue now, such as a parking lot or a parent whose children carry the work. | [sweep-triage](../tasks/sweep-triage.md) `--queue parked` |
| `triage:ready` | Scope and verification criteria are concrete enough to implement. | Prioritize or implement. |
| `triage:agent-closed` | An agent closed the issue with cited evidence. | [sweep-audit-closed](../tasks/sweep-audit-closed.md) |

`triage:needs-attention` means a person is the only thing standing between the issue and `triage:ready`. Keep parked issues off that label, so that a query for it shows only work genuinely waiting on the user.

Two labels were retired rather than renamed, and neither is valid any more:

- `triage:needs-definition` was for issues that were understood but not yet specified. It became a second waiting room: a specification pass would run, write a partial definition, stop, and nothing guaranteed a later pass would return. The autonomous pass now defines what it can and either promotes the issue or sends it to `triage:needs-attention`.
- `triage:blocked` restated a relationship as a label. See [Blocked issues](#blocked-issues).

There is also no label for **blocked**. Blocking is a native blocked-by edge, and no label records it.

## Blocked issues

An issue is blocked when its refinement depends on an open issue: the specification would describe code, a contract, or a decision that the other issue will change or supply. An open question for the user is `triage:needs-attention`, not a blocker.

**There is no `triage:blocked` label.** An open edge *is* the blocked state: `ghflow triage status` reports `stage: blocked`, and `triage list blocked` derives the queue from the edges. An earlier vocabulary had a label for it, and that label was a cache of a fact GitHub already held — one that drifted. Two issues were found carrying `triage:ready` while holding open blockers, invisible to the label-based query. Nothing now records blocking, so nothing can record it wrongly.

Set and clear the edge with the CLI:

```bash
python3 "$GHFLOW_CLI" triage block   ISSUE BLOCKER --repo OWNER/NAME
python3 "$GHFLOW_CLI" triage unblock ISSUE BLOCKER --repo OWNER/NAME
```

`block` means "ISSUE waits on BLOCKER". Both commands resolve issue node ids, write through GitHub's `addBlockedBy`/`removeBlockedBy` mutations, and re-read the issue to report the resulting edges. Both are idempotent: a duplicate add reports `already_present` and a missing edge reports `already_absent`, each with exit 0, so a sweep can re-run over its own earlier work.

`gh issue edit` has **no** blocked-by flag. The CLI above is the supported write path; do not tell a reader to look for a flag that does not exist. <!-- allow-bare-gh: names the command to deny a flag it does not have, not a run instruction -->

Do not read blocked-by edges with `gh issue view --json blockedBy`: that field does not exist, and the read fails with `Unknown JSON field` on current `gh`. Use `ghflow triage status` or the GraphQL `blockedBy` connection.

A blocked issue can carry an outline that names the contract it consumes, its scope, and its acceptance criteria, without file targets. Note in the outline that the full specification waits for the blocker.

Do not record a block when only part of the issue waits. If an independent part can be specified now, propose a split instead.

## Parked issues

`triage:parked` means **"needs more discussion or consideration — set it aside for now."** It is a deliberate shelf, not a way out of a loop. Nothing in triage acts on a parked issue, it never reaches the Ready queue, and the user reviews the parked set on their own schedule through the board view.

Parking requires the user's intent. An agent may park on the user's decision, or when a parent's open children carry all of its remaining work. An agent may **not** park an issue to silence a sweep, to avoid a hard classification, or to stop a question from recurring — those are what the closure rule and the attempt counter are for. Using the label as a loop-escape hatch makes the parked set meaningless: it stops being "things we chose to set aside" and becomes "things triage gave up on," which no one can then review.

State the reason in a comment. A parked issue is not closed: it records an idea or a parent's scope.

### What parked is not

Three things look like parking and are not:

| Looks like parking | Actually |
|---|---|
| An epic whose children carry the work | A **container**, not a shelf. Its state derives from the children rollup. Remove `triage:parked`; the board selection already exempts parents with open children. |
| An issue waiting on another issue | **Blocked** — a native blocked-by edge. No label. |
| A question the user has now twice declined to answer | A **failing needs-attention loop**. Raise the attempt counter; do not shelve it quietly. |

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

An unattended delivery that cannot settle a question, that hits a blocker it cannot clear, or that is in progress when its time budget ends, replaces `triage:ready` with `triage:needs-attention`, posts the question, blocker, or remaining steps as a comment on the issue, and leaves its draft PR and the In progress board status in place. The label puts the issue in the same view as other issues that need the user. [sweep-needs-attention](../tasks/sweep-needs-attention.md) resolves a question or blocker. A park for time has nothing to resolve, and a resumed delivery with no open question replaces `triage:needs-attention` with `triage:ready` before it continues.
This use of `triage:needs-attention` is distinct from `triage:parked`, which means the issue needs more discussion or consideration and has been set aside for the user's own periodic review.

The park comment names the next step. For a well-defined issue, suggest a retry with a different local model or a person. For a partial or missing preparation, suggest a preparation fix first. For a time park, resume with the local model. Do not suggest a cloud model.
