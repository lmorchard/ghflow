# Project direction

`ghflow` helps a person and an agent take an idea through issue definition, implementation, review, and authorized merge.
A pull request (PR) proposes changes for review. A merge adds changes to a target branch.
This document states current direction. [Direction history](../research/direction-history.md) preserves earlier discussions and superseded proposals.

## Useful operations first

Make each operation useful by itself. Use it on a real task before combining operations into a larger flow.
Each task accepts an ordinary issue or PR. Earlier tasks do not need this system.
Use GitHub records and Git history to supply information for the next session.

The separate agent-sessions repository supplies research material. Adapt useful ideas with sources, rather than copying its entire workflow or control program.
[Findings](../research/findings.md) records the earlier lessons and their limits. [Skill sources](../research/skill-sources.md) records selected adaptations.

## Agent and tool responsibilities

The agent interprets requests, defines scope, changes code, and assesses findings.
The command-line interface (CLI) accepts explicit inputs and performs a specified operation. It returns facts and results.
Use existing Git and `gh` commands when they are sufficient. Add a tool for repeated work or a known cause of errors.

The CLI uses Python and the standard library. Its operations include `pr-state`, `verify-commit`, `board set-status`, `pr ready`, `facts`, `identity`, and `exec`.
The [CLI reference](../../references/cli.md) explains PR and commit results. Installed command help supplies other command details.
The CLI does not call models, select tasks, schedule work, or infer approval.

## Skill package and delivery

The repository root contains the single `ghflow` skill. Task procedures and shared rules live in `references/`.
Personal symbolic links install the checkout root. [Setup](../setup.md) records commands, source access, and the nested-worktree discovery limitation.

Individual tasks remain usable directly. Delivery coordinators combine tasks within an explicitly selected issue, parent, or Ready queue.
Coordination follows [roles and handoffs](../../references/shared/coordination.md). It requires available subagent dispatch.
Bounded delivery does not authorize general backlog selection or scheduling.

## Current workflow boundaries

The user conversation settles intent and scope. Agents research discoverable facts and resolve routine choices within that scope.
[Decisions](../../references/shared/decisions.md) owns that distinction. [Interview issue](../../references/tasks/interview-issue.md) owns the conversation procedure.
Draft files support the conversation. They are not required reading for approval.

Delivery publishes significant committed progress as a draft PR before independent review.
[Draft PRs and readiness](../../references/shared/pr-lifecycle.md) owns progress updates and the transition to ready for review.
Standalone implementation remains local-only.

Existing authorization carries across task boundaries within its scope. Explicit draft-only and read-only limits still apply.
[Authorization](../../references/shared/authorization.md) owns permission rules. Implementation or submission does not authorize merge.

Subagents use a configured machine account for subject-repository actions. [Agent identity](../../references/shared/identity.md) owns account selection and credential handling.
Independent local review with a different recorded model is the primary review source for agent PRs.
[Review](../../references/shared/review.md) owns review preparation, exceptions, and affirmative review criteria.
[Merge PR](../../references/tasks/merge-pr.md) owns the merge procedure and its current-head checks.

## Keep the process useful

Agents keep concise [Task notes](../../references/shared/task-notes.md) when findings and decisions would be costly to reconstruct.
They read existing notes after context loss and carry the exact path through handoffs.
Project conventions control the location. The default is `docs/dev-sessions/{timestamp}-{slug}/notes.md` inside the active worktree.

[Working context](../../references/shared/context.md) limits source loading to the selected operation and applicable rules.
Agents inspect complete required evidence, then return concise results with links to detailed output.
They reuse the responsible implementation worker across checkpoints when it remains available.

A required step or document must help someone make a decision, do the task, or continue it later.
Use an existing issue, commit, or test result when it supplies that information.
Keep trial records when they answer a real question about a skill. Do not require such records for every task.
Remove or combine steps when actual use shows that they duplicate effort.

[Skill style](skill-style.md) assigns task and shared-rule ownership. [Writing rules](../writing.md) records the simplified-English trial and its limits.
[Trial records](../research/trials/README.md) and [scenario results](../../evals/README.md) supply evidence, with limits stated for each assessment.

## Deferred proposals

Automatic scheduling, custom session storage systems, attempt labels, and a special merge-result format remain outside the selected effort.
Frozen checks, locked test files, and a separate validation system remain deferred.
A later proposal for these mechanisms needs evidence that ordinary tools, tests, and review do not address the problem.

Next-task advice remains a proposal in [Direction history](../research/direction-history.md#possible-next-task-guidance).
Automatic task selection needs evidence of a need and an explicit project decision.
Agent application permissions and user authorization remain the execution boundaries. A skill does not enforce stronger restrictions for unattended use.
An unattended request lets a coordinator take a supported recommendation, record it in the PR, and park an issue it cannot settle under `triage:needs-input`. [Decisions](../../references/shared/decisions.md#decide-in-an-unattended-flow) owns that rule; the request, not the skill, turns it on.
