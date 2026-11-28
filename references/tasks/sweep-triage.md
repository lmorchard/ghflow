# Sweep triage state

Reconcile an issue queue's recorded triage state against what the repository actually says. One procedure, three queues: assess new work, clear expired blocks, revisit parks.

Apply [Triage state](../shared/triage-state.md) throughout — it holds the vocabulary, the reconciliation-loop framing, the closure rule, the evidence rules, and the authority ladder. This file holds only the selection and the pass structure. Do not restate the contract here.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Agent identity](../shared/identity.md) before writes, and [GitHub writes](../shared/github-writes.md) before changing records.

## Select the queue

```bash
python3 "$GHFLOW_CLI" triage list untriaged --owner OWNER --project NUMBER
python3 "$GHFLOW_CLI" triage list blocked   --owner OWNER --project NUMBER
python3 "$GHFLOW_CLI" triage list parked    --repo OWNER/REPO
```

| Queue | Selects | What a pass does |
|---|---|---|
| `untriaged` | open issues with no `triage:*` label, a real Priority, no open children, and no open blocked-by edge | assess, define, and classify |
| `blocked` | open issues with an open blocked-by edge, whatever label they carry | reconcile the edges |
| `parked` | open `triage:parked` | test whether the park reason still holds |

`untriaged` and `blocked` come out of the same board read and partition the unlabelled issues between them: an issue with an open edge never appears in `untriaged`. `blocked` is not label-scoped on purpose — a labelled issue holding an open edge is a contradiction worth surfacing, not hiding.

If the queue is empty, say so and stop. An empty queue is a result, not a failure to find work.

**`--dry-run` first.** Run the whole pass with the intended comment and label printed instead of posted. For a queue that has not been swept before, or after a prompt or model change, the dry run is the deliverable; the live pass comes after a reader has seen the output.

## Bound the pass

Work in slices of 5 to 10 issues. One agent per issue, because an assessment needs the whole issue read against current code and that does not share well.

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
| waiting on a decision from the user | skip: that is `triage:needs-attention`'s job, not this pass |
| blocked by open issue(s) | skip, unless this is the `blocked` queue and they have since closed |
| cited evidence does not verify | re-assess; the earlier assessment is wrong or stale |
| parked parent whose children all closed | judge against the parent rules below, not as an ordinary issue |

## The pass, by queue

### `untriaged` — assess, define, and classify

This pass **attempts `triage:ready` for every issue**. Classification and definition are not separate stages: an agent that has read the issue against current code is the one best placed to write the scope and verification criteria, and handing that to a later pass is how an issue lands in a queue nothing guarantees will be worked.

Investigate before classifying. Read the issue, then search git history and merged PRs for work that already addresses it, then read the current code at the target revision. Treat the issue text as a claim.

Then take one of five exits:

1. **Close it** — Already done, Obsolete-superseded, or Unnecessary, per the closure rule in [Triage state](../shared/triage-state.md#closure-only-when-the-issue-looks-closed). Closures need cited evidence.
2. **Define it and promote it** — write the scope, the file targets, and the verification criteria into the body, then run the gate below. This is the common case and the one to reach for.
3. **Record the block** — the work depends on other open issues. Set native blocked-by edges with `ghflow triage block`, optionally leaving an outline naming the contract it consumes. Apply **no label**: an open edge is the blocked state. Do not guess at a specification that a blocker will invalidate, and do not clear a triage label the issue already earned — an issue that is `triage:ready` *and* blocked should keep both facts, and `triage status` reports the contradiction as `stage: blocked`.
4. **Split it** — the issue holds several separable goals. Rules are in [Triage state](../shared/triage-state.md#splitting): the original body goes verbatim into the child that inherits it, children land `untriaged`, the parent closes as Obsolete-superseded naming the children.
5. **Ask** — the pass cannot reach a specification or a closure, because a product, design, or tradeoff decision is genuinely the user's. Apply `triage:needs-attention` and write the question per `sweep-needs-attention`, including a recommendation where the evidence supports one.

Exits 1, 3, and 4 need no person. Exit 5 is the pass admitting a limit, and it is the only exit that spends the user's attention. Prefer exit 2 whenever the evidence actually supports a specification.

**Rewriting a stale contract is exit 2, not its own state.** An issue whose goal stands but whose body describes components that no longer exist (the Obsolete-stale-contract class) is rewritten against current code in this pass and promoted. If the rewrite uncovers a genuine decision it becomes exit 5.

Before advancing anything to `triage:ready`, run the gate:

```bash
python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO --verify-evidence
```

`triage:ready` requires `evidence.verified`. An unverified definition is a retry, not a state: post the comment naming each citation that failed to resolve, and leave the issue `untriaged` so the next pass picks it up. Do not apply a label for it, and do not read the failure as a question for the user.

A parent issue in this queue is judged by [Parents are not their children](../shared/triage-state.md#parents-are-not-their-children), not by the assessments its children received. A parent with no children at all is `triage:needs-attention`, never an auto-classification: decomposing it is an interactive design session.

### `blocked` — reconcile the edges

Read `blockers` from the status, not from raw `gh` output. There is no `label_stale` for blocking any more, because no label records it.

- **Edges all closed**: remove any stale `triage:blocked` label a human or an older sweep left behind — `ghflow triage unblock` is not needed, the edges are already closed, just clear the label. Then return the issue to `untriaged` **unless it already carries `triage:ready`**, in which case leave the label and let the next pass judge it: the dependency cleared, but nothing has been checked against current code since it did, so a `ready` label from before the blocker landed is a claim to re-verify, not to trust.
- **Open edges remain**: leave it. Report the open blockers by number.
- **No edges at all**: the issue is only in this queue because something set an edge that has since been removed, or it was selected by a stale label. Report it and clear any `triage:blocked` label.

A blocker closed as `not planned` still counts as closed, but it may have invalidated the issue's premise. Say so in the comment.

Note what this queue is *for* now: it is not "issues wearing the blocked label", it is "issues with an open edge", which includes labelled ones. If a `triage:ready` issue shows up here, that is the signal the old label scheme used to hide — report it rather than quietly clearing its label.

### `parked` — test whether the reason still holds

Read the park comment and classify the park by what it recorded. The kinds differ in whether they can expire:

- **Parent with `triage:parked`** — the label does not belong on a container. A parent's state derives from its children rollup, and the board selection already exempts it while any child is open. Remove the label and report it. If the children have all closed, judge the parent against [Parents are not their children](../shared/triage-state.md#parents-are-not-their-children) instead of parking it again.
- **Routing park** — the comment names a capability, model class, label, or gate being waited on. Check whether that condition still holds. If it has changed, remove the label, return the issue to `untriaged`, and name what changed. If it holds, leave it.
- **Decision park** — needs more discussion or consideration. This does not expire. Leave it. The one exception is a concrete change that contradicts the recorded reason; raise that for the user rather than relabelling.
- **Unexplained park** — no reason recorded. Report it. Do not invent a reason and do not relabel.

Parking rules and the revisit-trigger requirement live in [Triage labels](../shared/triage-labels.md#parked-issues).

## Never in this pass

- Move an issue to `triage:ready` on a cleared dependency alone.
- Move an issue to `triage:ready` without `evidence.verified`.
- Leave an issue in an intermediate state that no scheduled pass will pick up.
- Change Priority or Size; that is [sweep-prioritize](sweep-prioritize.md).
- Implement anything or open a PR.
- Close an issue because it is hard, old, or quiet.

## Return the result

Report per issue: number, title, classification, the evidence cited, the action taken, and the comment URL.

Group by queue, and lead with what changed. List separately:

- Closures, each with the evidence that justified it — these are the highest-consequence writes.
- Splits, naming the parent and every child.
- Issues left for `triage:needs-attention`, with the exact question each one needs answered, so the later session starts from the pass's research rather than repeating it.
- Issues left alone with the reason, so a reader can check the reasoning rather than take the silence on trust.
- Any citation that failed verification.

Name the queue and slice in the summary, so a later pass knows what was covered. State whether the queue is now idle: every issue either terminal or waiting on something named.
