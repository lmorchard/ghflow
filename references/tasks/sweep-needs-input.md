# Sweep issues needing input

Settle the product and design questions that are holding issues in `triage:needs-input`, then record the decision and move each issue to its next state. The distinct work here is the **conversation**; the classification and the write follow [Triage state](../shared/triage-state.md).

Apply [Triage state](../shared/triage-state.md), [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md). The parent agent conducts the conversation; subagents execute writes following [Agent identity](../shared/identity.md), and [GitHub writes](../shared/github-writes.md) before changing records.

## List pending issues

```bash
python3 "$GHFLOW_CLI" triage list needs-input --repo OWNER/REPO
```

If none carry the label, report that the input backlog is clear and stop.

## Present issues for review

Group issues that share a decision into one cluster, so the user resolves a pattern once rather than stepping through serial turns. Present isolated issues one at a time.

For each issue or cluster:

1. Read the issue, its comments, and its latest assessment comment. Confirm the assessment still covers the issue; if `ghflow triage status ISSUE` reports `assessment.stale`, say so before asking anything, because the question may have moved.
2. Present a short summary in conversation:
   - Number, title, URL.
   - The core problem and where the code stands now.
   - The one or two questions that need the user's decision, each with concrete choices or a named tradeoff.
3. If the tradeoffs need exploring first, follow [interview-issue](../tasks/interview-issue.md).

Do not ask the user to read code or diffs unless they ask.

## Record the decision

The user's answer settles direction. It does not settle readiness, and the two are easy to conflate: a decision that unblocks a task is not a judgment that the task is specified.

Dispatch a subagent to:

1. Post a comment recording the decision and its rationale, using the assessment format from [Triage state](../shared/triage-state.md#the-assessment-comment).
2. Remove `triage:needs-input`.
3. Apply the state that follows from the decision:

| Decision | Resulting state |
|---|---|
| Do not proceed | close `not planned` — record it as **Unnecessary**, per the closure rule |
| Actionable as-is, and the evidence verifies | `triage:ready`, after `--verify-evidence` |
| Direction settled, technical detail still open | `triage:needs-definition` |
| Waits on other open issues | `triage:blocked`, with native blocked-by edges set first |
| Parking lot, or a parent whose children carry the work | `triage:parked`, with the revisit trigger recorded |

When a decision settles direction but the technical detail is open, prefer `triage:needs-definition` over `triage:ready`. Skipping the definition pass is how an issue arrives at implementation with an unanswered question.

4. If the issue belongs to a parent theme, update the parent's rollup comment.

## Return

Summarize what was decided, what state each issue reached, and anything still waiting on the user. Hand off to [sweep-needs-definition](sweep-needs-definition.md) for anything that landed there.
