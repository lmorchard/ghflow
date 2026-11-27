---
skills: [sweep-triage]
source: references/tasks/sweep-triage.md; decafclaw triage sweep, 2026-10-08
---

## Situation

You are reconciling the `blocked` queue. `ghflow triage status` reports the following.

- Issue #964: `blockers.open` contains #1007; `label_stale` is null.
- Issue #999: `blockers.open` is empty, `blockers.cleared` is true, and `label_stale` reads
  "triage:blocked is set but every blocked-by edge is closed". Its closed blocker #956
  closed through a merged PR.
- Issue #1000: `blockers.blockers` is empty. Its body says "Blocked by #923", and #923 is
  closed.

## Expected

Leave #964 on `triage:blocked` and report #1007 as its open blocker.

For #999, remove `triage:blocked` and post a comment naming #956 and its closing PR. Return
it to **untriaged**, not to `triage:needs-definition`: the label recorded a dependency, and
nothing has been checked against current code since the blocker closed. Say in the comment
that a fresh assessment decides whether it is still worth doing.

For #1000, do not relabel on text alone. Report that its body names #923 so the relationship
can be set.

## Not acceptable

- Unblocking #964 because one of its blockers closed.
- Advancing #999 to `triage:needs-definition` on a cleared dependency alone.
- Relabeling #1000 from the text without a recorded relationship.
- Writing a full specification for #999 in this task.
- Reading the edges with `gh issue view --json blockedBy`, which fails on current `gh`.
