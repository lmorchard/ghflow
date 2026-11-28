# Sweep triage state

Reconcile an issue queue's recorded triage state against what the repository actually says. One procedure, three queues: assess new work, clear expired blocks, revisit parks.

Apply [Triage state](../shared/triage-state.md) throughout — it holds the classification vocabulary, the closure rule, the evidence rules, and the authority ladder. This file holds only the selection and the pass structure. Do not restate the contract here.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Agent identity](../shared/identity.md) before writes, and [GitHub writes](../shared/github-writes.md) before changing records.

## Select the queue

```bash
python3 "$GHFLOW_CLI" triage list untriaged --owner OWNER --project NUMBER
python3 "$GHFLOW_CLI" triage list blocked   --repo OWNER/REPO
python3 "$GHFLOW_CLI" triage list parked    --repo OWNER/REPO
```

| Queue | Selects | What a pass does |
|---|---|---|
| `untriaged` | open issues with no `triage:*` label, a real Priority, no open children | assess and classify |
| `blocked` | open `triage:blocked` | reconcile the blocked-by edges |
| `parked` | open `triage:parked` | test whether the park reason still holds |

If the queue is empty, say so and stop. An empty queue is a result, not a failure to find work.

**`--dry-run` first.** Run the whole pass with the intended comment and label printed instead of posted. For a queue that has not been swept before, or after a prompt or model change, the dry run is the deliverable; the live pass comes after a reader has seen the output.

## Bound the pass

Work in slices of 5 to 10 issues. One agent per issue, because a classification needs the whole issue read against current code and that does not share well.

When a slice finishes, report it and continue. If a pass is interrupted, the written comments and labels are the record of what completed; re-running the same query resumes from what remains.

Never re-classify an issue whose `triage status` reports a fresh assessment covering the current state. `assessment.stale` is the signal that a re-read is warranted.

## Start every issue with the derived state

```bash
python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO
```

Read `bucket`, `stage`, `blockers`, `children`, `label_stale`, and `next_step` from it. This is the whole starting position; do not reconstruct it from labels.

If `next_step.eligible` is false, act on its **reason**:

| Reason | Action |
|---|---|
| already at a terminal state | skip, and report why |
| waiting on a decision from the user | skip: that is `triage:needs-input`'s job, not this pass |
| blocked by open issue(s) | skip, unless this is the `blocked` queue and they have since closed |
| cited evidence does not verify | re-assess; the earlier assessment is wrong or stale |
| parked parent whose children all closed | judge against the parent rules below, not as an ordinary issue |

## The pass, by queue

### `untriaged` — assess and classify

Investigate before classifying. Read the issue, then search git history and merged PRs for work that already addresses it, then read the current code at the target revision. Treat the issue text as a claim.

Classify into exactly one class from [Triage state](../shared/triage-state.md#classification), write the assessment comment, apply the label.

Closure is available here and is subject to the closure rule: close only when the issue looks genuinely closed, obsolete, or unnecessary. Hard, old, and quiet are not grounds.

A parent issue in this queue is judged by [Parents are not their children](../shared/triage-state.md#parents-are-not-their-children), not by the assessments its children received. A parent with no children at all is `triage:needs-input`, never an auto-classification: decomposing it is an interactive design session.

Before advancing anything to `triage:ready`, re-run with verification:

```bash
python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO --verify-evidence
```

`triage:ready` requires `evidence.verified`. Unverified evidence stops at `triage:needs-definition` with a comment naming the unverified citation, so a definition pass can repair it.

### `blocked` — reconcile the edges

Read `blockers` and `label_stale` from the status, not from raw `gh` output.

- **`label_stale` set** (every edge closed): remove `triage:blocked`. Do **not** advance to `triage:needs-definition`. The label recorded a dependency, not a readiness judgment; nothing has been checked against current code since the blockers landed. Removing the label sends the issue back through a full assessment.
- **Open edges remain**: leave it. Report the open blockers by number.
- **No edges at all**: the blocker may exist only in text. Read the body and comments; if they name blocking issues, report them so the relationships can be set. Do not relabel on text alone.

A blocker closed as `not planned` still counts as closed, but it may have invalidated the issue's premise. Say so in the comment.

### `parked` — test whether the reason still holds

Read the park comment and classify the park by what it recorded. The kinds differ in whether they can expire:

- **Parent with `triage:parked`** — the label does not belong on a container. A parent's state derives from its children rollup, and the board selection already exempts it while any child is open. Remove the label and report it. If the children have all closed, judge the parent against [Parents are not their children](../shared/triage-state.md#parents-are-not-their-children) instead of parking it again.
- **Routing park** — the comment names a capability, model class, label, or gate being waited on. Check whether that condition still holds. If it has changed, remove the label and name what changed. If it holds, leave it.
- **Decision park** — needs more discussion or consideration. This does not expire. Leave it. The one exception is a concrete change that contradicts the recorded reason; raise that for the user rather than relabelling.
- **Unexplained park** — no reason recorded. Report it. Do not invent a reason and do not relabel.

Parking rules and the revisit-trigger requirement live in [Triage labels](../shared/triage-labels.md#parked-issues).

## Never in this pass

- Move an issue to `triage:ready` on a cleared dependency alone.
- Change Priority or Size; that is [sweep-prioritize](sweep-prioritize.md).
- Implement anything or open a PR.
- Close an issue because it is hard, old, or quiet.

## Return the result

Report per issue: number, title, classification, the evidence cited, the action taken, and the comment URL.

Group by queue, and lead with what changed. List separately:

- Closures, each with the evidence that justified it — these are the highest-consequence writes.
- Issues left alone with the reason, so a reader can check the reasoning rather than take the silence on trust.
- Unexplained parks and contradicted decision parks, which need the user rather than the next pass.
- Any citation that failed verification.

Name the queue and slice in the summary, so a later pass knows what was covered.
