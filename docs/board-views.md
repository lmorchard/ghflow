# Project board views

A view is a saved filter and layout on a GitHub project board. This document gives filters for views that show work for a person or a sweep. Each view names the task that acts on its items. The filters use the [triage labels](../references/shared/triage-labels.md).

The examples come from board 6 for [decafclaw](https://github.com/lmorchard/decafclaw). That board has the Status values `Backlog`, `Ready`, `In progress`, `In review`, and `Done`. It also has a single-select `Priority` field. Change the field names and values to match your board.

## Filter syntax

The [GitHub filter reference](https://docs.github.com/en/issues/planning-and-tracking-with-projects/customizing-views-in-your-project/filtering-projects) defines the syntax. These rules apply to the views below:

- A space between two terms means AND.
- A comma between values of one field means OR. For example, `label:bug,support` matches either label.
- A hyphen before a term negates it. For example, `-status:Done`.
- `no:FIELD` matches items with no value. `has:FIELD` matches items with a value.
- `*` is a wildcard in a value. For example, `label:*bug*` matches a label that contains "bug". A negated wildcard also works. Les confirmed `-label:triage:*` on board 6 on 2026-10-08, although the reference does not show that form.
- The reference documents no OR across different fields. It documents no `or` keyword and no parentheses.
- The reference documents no filter for issue dependencies, such as blocked-by relationships.

## Triage views

### Needs attention

```text
label:triage:needs-attention -status:Done
```

This view shows issues that are waiting on the user. Use [sweep-needs-attention](../references/tasks/sweep-needs-attention.md) to work through them one at a time in a live session. Blocked and parked issues have other labels, so they do not appear.

### Untriaged

```text
-label:triage:* status:Backlog -priority:P-null
```

This view shows backlog issues that have no triage label. Run [sweep-triage](../references/tasks/sweep-triage.md) on them in batches.

The term `-label:triage:*` removes every issue with a label that starts with `triage:`. A new triage label therefore needs no change to this filter.

On board 6, `P-null` is a literal Priority value for theme and epic issues. The term `-priority:P-null` removes those issues. It does not remove issues with no Priority value. To remove those issues also, add `-no:priority`.

### Blocked

There is no board view for blocked issues. Blocking is a native blocked-by relationship and the project board has no documented dependency filter, so the label that used to stand in for it is gone rather than approximated.

Run `python3 "$GHFLOW_CLI" triage list blocked --owner OWNER --project NUMBER` to enumerate them: it derives the set from the edges, including issues that carry a triage label. Use it with [sweep-triage](../references/tasks/sweep-triage.md) `--queue blocked` to reconcile — a cleared edge returns the issue to untriaged rather than advancing it, because a cleared dependency is not a readiness judgment.

### Parked — needs more discussion

```text
label:triage:parked -status:Done
```

This is the shelf: issues deliberately set aside that need more discussion or consideration. Nothing in triage acts on them, and they never reach Ready. Review this view on your own schedule.

Two reasons the set exists, and the view is only useful if it holds both:

- **Routing parks** clear themselves when the named condition changes.
- **Decision parks** wait for you.

Keep the view small enough to read in one sitting. If it grows without you remembering what is in it, that is the signal that the label has drifted back into being a place work goes to be forgotten.

An epic should never appear here. A parent is a container, not a shelf; the board selection already exempts it while its children are open. Run [sweep-triage](../references/tasks/sweep-triage.md) with `--queue parked` to reconcile: it removes the label from any parent and checks whether each remaining park reason still holds.

## Planning views

### Ready without a priority

```text
label:triage:ready no:priority -status:Done
```

This view shows defined issues that nobody has prioritized. Use [sweep-prioritize](../references/tasks/sweep-prioritize.md) to set Priority and Size.

### Ready queue

```text
label:triage:ready status:Ready
```

Sort this view by Priority. It shows the issues that [curate-ready-queue](../references/tasks/curate-ready-queue.md) staged. [burndown-ready-queue](../references/tasks/burndown-ready-queue.md) delivers them in sequence.

## Health views

### Recent agent closures

```text
is:closed label:triage:agent-closed updated:>@today-7d
```

This view shows issues that an agent closed in the last seven days. Use [sweep-audit-closed](../references/tasks/sweep-audit-closed.md) to confirm or reopen them. A closed item appears only if nobody archived it from the board.

### Stale active work

```text
status:"In progress","In review" updated:<@today-14d
```

This view shows active items with no update in 14 days. Examine each item for a stopped PR, a missing review, or a wrong status. Use [address-pr-review](../references/tasks/address-pr-review.md) for a PR that waits for follow-up.

### Status drift

```text
is:open status:Done
```

```text
is:closed -status:Done
```

The first view shows open issues that are marked `Done`. The second view shows closed issues that are not marked `Done`. Both show board states that disagree with the issue state. Correct each item with the board-status procedure in [Board status](../references/shared/board-status.md), or report it when the cause is unclear.

## Limits

Les confirmed the `-label:triage:*` wildcard on board 6 on 2026-10-08. The needs-attention view comes from a view that Les used on the same day, and this page rewrites it with the documented comma syntax. Nobody has tested the other filters on a live board. They follow the documented syntax only. If a filter gives unexpected results, compare it with the GitHub filter reference and correct this page.
