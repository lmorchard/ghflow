# Operations

Use [ghflow](../SKILL.md) to select an operation from an explicit request.
A pull request (PR) proposes changes for review.
Each operation links to its task procedure.

## Backlog and project boards

- [bundle-issues](../references/tasks/bundle-issues.md) groups related issues into thematic initiatives under native GitHub parent issues labeled `theme`.
- [triage-issues](../references/tasks/triage-issues.md) evaluates open issues against code and git history, applying triage labels and closing completed or obsolete items.
- [sweep-needs-input](../references/tasks/sweep-needs-input.md) interactively resolves blocking product and architectural decisions with the user.
- [sweep-needs-definition](../references/tasks/sweep-needs-definition.md) develops accepted issues into bounded, actionable specifications with concrete file targets and test criteria.
- [sweep-blocked](../references/tasks/sweep-blocked.md) returns `triage:blocked` issues to definition when all of their native blockers close.
- [sweep-audit-closed](../references/tasks/sweep-audit-closed.md) reviews and confirms autonomously closed issues with cited evidence.
- [sweep-prioritize](../references/tasks/sweep-prioritize.md) assigns Priority (`P0`–`P3`) and Size (`XS`–`XL`) fields on the project board and re-sweeps deferred items.
- [curate-ready-queue](../references/tasks/curate-ready-queue.md) examines limits on work in progress (WIP) and stages high-priority Backlog items into the `Ready` column.

## Issues and pull requests

- [reconsider-issue](../references/tasks/reconsider-issue.md) reassesses an existing issue against current project evidence.
- [decompose-parent-issue](../references/tasks/decompose-parent-issue.md) maps a broad issue into bounded children and a parent completion condition.
- [define-issue](../references/tasks/define-issue.md) prepares and reviews an issue draft.
- [interview-issue](../references/tasks/interview-issue.md) resolves decisions with the user.
- [file-issue](../references/tasks/file-issue.md) publishes a reviewed draft and confirms the requested GitHub changes.
- [implement-issue](../references/tasks/implement-issue.md) produces tested, committed changes for PR preparation.
- [review-changes](../references/tasks/review-changes.md) assesses changes in a fresh reviewer context without editing them.
- [submit-pr](../references/tasks/submit-pr.md) publishes draft progress or marks completed work ready for review. Independent local review is the primary source for agent PRs. The user can request Copilot review.
- [address-pr-review](../references/tasks/address-pr-review.md) waits for requested review, addresses findings, and repairs failing CI on an existing PR.
- [merge-pr](../references/tasks/merge-pr.md) confirms CI and review findings, merges authorized changes, and confirms the result.

## Project facts

- [prepare-project-facts](../references/tasks/prepare-project-facts.md) writes or refreshes `.ghflow/project.md`, one screen of stable project facts for workers. `ghflow facts` reads the live state and reports when the file's sources changed.

## Delivery coordinators

- [express-issue](../references/tasks/express-issue.md) coordinates one selected issue through delivery to an agreed endpoint.
- [deliver-parent-issue](../references/tasks/deliver-parent-issue.md) coordinates a bounded parent through child delivery and completion checks.
- [burndown-ready-queue](../references/tasks/burndown-ready-queue.md) coordinates the sequential delivery of issues staged in the project board's `Ready` column. An unattended request parks an issue it cannot settle under `triage:needs-input` and continues; `scripts/unattended-burndown.sh` composes and launches such a run.

Each operation accepts an ordinary issue or PR. References share [authorization](../references/shared/authorization.md), [coordination](../references/shared/coordination.md), [decisions](../references/shared/decisions.md), and [evidence](../references/shared/evidence.md).
Delivery through review follow-up leaves the PR open. Merge requires explicit authorization and the existing review policy.
