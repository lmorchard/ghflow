# Triage issues

Evaluate a batch of open issues to identify completed, obsolete, well-defined, or uncertain work. Post findings comments on the issues and apply one [triage label](../shared/triage-labels.md) to each. Close confirmed completed or obsolete issues with evidence. This skill does not implement changes, submit PRs, or modify project boards.

Apply [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Agent identity](../shared/identity.md) throughout. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Select the issue batch

Identify the issues to evaluate:
- A parent issue number (evaluating the sub-issues attached to that parent),
- An explicit list of issue numbers, or
- A query of open issues without `triage:*` labels, optionally filtered by area label (such as `core` or `tui`).

Keep batch sizes bounded to 5 to 10 issues per run to ensure thorough inspection of target code and git history. When a parent issue contains more than 10 sub-issues, split the work into parallel slices of 5 to 8 issues to maintain high inspection depth.

## Inspect code and history

For each issue in the batch:

1. Read the issue title, body, comments, and any linked issues or PRs.
2. Search git history and merged PRs in the subject repository for relevant changes or commits that already address the problem.
3. Inspect current code and tests at the target revision (such as `main`).
4. Compare requested behavior and assumptions against current architecture and implementation.

Treat issue claims and older comments as unverified until you check current code.

## Classify each issue

Assign each issue to one classification based on evidence:

- **Already completed**: Current code, merged PRs, or existing tests already satisfy the requested result. Cite the exact commit SHA, PR number, or test path.
- **Obsolete or not planned**: Architectural direction changed, the referenced component was removed or superseded, or the issue is an exact duplicate of another issue. Cite the specific change or primary issue.
- **Needs human input**: The core purpose or scope requires product, architectural, or tradeoff decisions from the user. Identify the exact 1 to 2 questions with specific choices or tradeoffs.
- **Needs technical definition**: The goal is valid and desirable, but the issue lacks concrete technical scope, file boundaries, or acceptance criteria, and it can be specified now.
- **Blocked**: The goal is valid, but a useful specification depends on open issues that will change the code or supply a contract or decision. Name each blocking issue.
- **Parent tracked by children**: Open sub-issues carry all of the remaining work. Label it `triage:parked`. Park other issues only on the user's decision.
- **Ready as-is**: Problem, scope, and verification criteria are clear, accurate, and actionable against current code.

Autonomous closure requires verifiable evidence: a commit SHA, merged PR, passing test path, or concrete duplicate reference. Do not close active bugs or desired features autonomously merely because they are difficult or open questions exist; label them `triage:needs-input` instead.

## Update GitHub records

For each evaluated issue:

1. Post a concise comment with:
   - Summary of findings against current code.
   - Cited evidence (commit SHAs, file paths, test assertions, PRs).
   - The blocking questions or missing criteria, if applicable.
2. Apply the matching label from [Triage labels](../shared/triage-labels.md). For a blocked issue, set a native blocked-by relationship for each blocking issue before you apply `triage:blocked`.
3. If the issue is already completed, close it:
   - `ghflow exec -- gh issue close ISSUE_URL --reason completed`
4. If the issue is obsolete or not planned, close it:
   - `ghflow exec -- gh issue close ISSUE_URL --reason "not planned"`
   - Add the `wontfix` or `duplicate` label if the repository uses it.
5. If updating labels fails because a label does not exist in the repository, create the label with a brief description and retry.
6. When evaluating a parent issue's sub-issues, post a rollup summary comment to the parent issue listing the status of its children.

## Return the batch summary

Return a structured summary table to the parent:

- Issue number and title.
- Classification.
- Key evidence or blocking question.
- GitHub action taken (closed with reason, labeled).

Do not implement code, open pull requests, or alter project board cards during triage.
