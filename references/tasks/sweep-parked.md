# Sweep parked issues

Revisit issues labeled `triage:parked` and decide, for each, whether the reason it was parked still holds. This task changes labels and posts comments. It does not define issues; [sweep-needs-definition](sweep-needs-definition.md) does that next.

`triage:parked` was the only triage label with no sweep, which made it a one-way door: an issue could be parked for a reason that quietly stopped being true, and nothing would ever look again. This sweep is that look.

Apply [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md) throughout. Subagents perform subject-repository writes following [Agent identity](../shared/identity.md) and [GitHub writes](../shared/github-writes.md).

## List parked issues

Query open issues in the subject repository with the label `triage:parked`:

```bash
python3 "$GHFLOW_CLI" triage parked --repo OWNER/REPO
```

If none carry it, report that and stop.

## Classify each park

Read `python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO` for each issue, and classify the park by what it was actually recording. The three kinds have different revisit triggers, and treating them alike is how this sweep would do damage.

### 1. Parent park — children carry the work

Signals: `children.total` is greater than zero and the park comment names the children.

The park reason is a claim about the children: *they are where the work lives.* That claim expires on its own.

- **Children all closed** (`children.all_closed`, reported as `label_stale`): the reason has expired. Do not assume the parent is done — it may still have its own scope. Remove `triage:parked` so the parent gets a fresh assessment, and post a comment naming the closed children. Removing the label, rather than applying `triage:needs-definition`, keeps the readiness judgement for the fuller assessment.
- **Children still open**: the reason still holds. Leave it. Report the counts.

### 2. Routing park — waiting on a capability

Signals: the park comment names a model class, a runner, a capability, or a gate such as `impl:strong`, rather than a decision not to work on it.

This is the kind that looks deliberate and is actually waiting. The reason does not expire by time, but the *capability* can arrive.

- Check whether the named condition is still true: does the label it names still apply, is the excluded capability still absent?
- **Condition no longer holds**: remove `triage:parked`, post a comment naming what changed, and let the assessment reassign. Do not send it straight to `triage:ready`.
- **Condition still holds**: leave it, and say so.

### 3. Decision park — nobody intends to work on it

Signals: no children, and the park comment records a decision, a parking-lot idea, or a declared scope.

This kind does **not** expire. "Nobody intends to work on this" is a decision, and no amount of time passing turns a decision into a mistake. Relabelling these on a schedule would be the sweep overriding a person.

- **Default: leave it alone.** Report it as still parked and stop.
- **The one exception**: a concrete change in the world that contradicts the recorded reason — the subsystem was deleted, the feature shipped by other means, the dependency disappeared entirely. Then raise it for the user rather than relabelling it yourself. Quote the recorded reason and the evidence that contradicts it.
- If the park comment records no reason at all, report the issue as **unexplained**. Do not invent one and do not relabel it. An unexplained park is a finding for the user, not a licence to decide.

## Apply changes

1. For an expired parent park, remove `triage:parked` and post a comment that lists the closed children with the PR or commit that closed each when GitHub records one.
2. For a routing park whose condition no longer holds, state the condition, what changed, and the evidence, then remove `triage:parked`.
3. For a decision park with a contradicted reason, do not relabel. Post nothing until the user decides; list it in the report.
4. Never move an issue directly to `triage:ready`. This sweep decides only whether a park still applies; readiness needs the full assessment in [sweep-needs-definition](sweep-needs-definition.md).
5. An issue with an open blocked-by edge stays put whatever else is true. Report the blocker.

## Return the sweep result

Report every parked issue with:

- Its classification (parent, routing, decision, or unexplained).
- The recorded reason, quoted from the park comment.
- What was checked to test that reason, and its current state.
- The action taken, or why none was.
- The comment URL when one was posted.

Group the output by classification, and lead with any issue you changed. List unexplained parks and contradicted decision parks separately, because those are the ones that need the user rather than the next sweep.
