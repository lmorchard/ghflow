# Instructions for agents

Before you propose a design, read [Project direction](docs/dev/direction.md). Before you copy code or instructions from agent-sessions, read [Findings](docs/research/findings.md). The instructions in agent-sessions do not apply to this repository.

## Development

Start with an operation that is useful by itself. A phase is a task such as an issue definition or a PR review. Combine operations into phases after real use shows their value.

Do not add automatic task selection without evidence of a need and an explicit project decision. Use existing git and gh commands when they are sufficient. Add a tool when it removes a repeated procedure or a known cause of errors.

Keep decisions separate from proposals. Give a source for each lesson or code section that you copy. Select a language and command names when a specific task supplies enough information.

Create each worktree for this repository at `.claude/worktrees/<branch>` inside the checkout, not in a sibling directory. Git ignores that folder. Do not remove a worktree that has uncommitted changes or an open PR.

## Parent and trial agent roles

First apply [Execution mode](references/shared/coordination.md#execution-mode). In single-session mode, the current agent performs authorized subject-repository tasks directly and must not use subagents. The parent and trial-agent separation below applies only in delegated mode.

The parent agent develops skills with Les and evaluates their trials. It can edit this workflow repository and inspect subject repositories for research. A subject repository is a project used to try the skills.

Subagents perform subject-repository tasks through the relevant skills. This includes code changes, commits, pushes, issue and board updates, PR submission, review replies, merges, and cleanup. The parent must not perform those actions directly merely because the user authorized the task.

Give each subagent the skill, necessary inputs, and the authorized scope. Return decisions that need user judgment to the parent conversation. The parent reviews results and improves the skills without silently completing missing subject-repository actions itself.

If a skill is incomplete, revise it here and let a subagent continue the task. If delegation is unavailable, report that limit. Only an explicit user exception permits the parent to act directly in the subject repository.

## Local-model execution and review

Les requested single-session execution for local-model work, with no subagents and same-model review allowed. Apply [Execution mode](references/shared/coordination.md#execution-mode) and [Single-session review](references/shared/review.md#single-session-review). This approval covers local-model setups beyond the earlier OpenCode and Qwen exception below. It does not change cloud-model defaults.

Les approved skipping different-model review for this project when using OpenCode with local `qwen3.8:latest` on his laptop. A fresh same-model second opinion is optional. Keep tests and self-review, and report the different-model review as waived under this approval. This exception does not apply to cloud-model workflows, waive other checks, or authorize merge. Carry its scope under [Review](references/shared/review.md#user-approved-exceptions).

## Authorization across issue tasks

Les wants an agreed issue-preparation flow to continue through research, interviews, draft review, and publication without approval at every skill boundary. Carry that authorization and its limits across tasks and into any subagent handoff. Once decisions are settled, publish the reviewed result within the agreed scope and report it. A subagent finishing a draft does not end the parent's authorized flow. Dispatch the next included task instead of waiting for the user to ask what is next.

Interviews settle questions, not repeated authorization. Carry authorization forward through changes that Les reviews or weighs in on. Revisit authorization only when a significant change falls outside the reviewed or authorized scope.

An explicit draft-only or read-only request still limits the work. Ask about unresolved product decisions or actions beyond the agreed scope, not merely because the next skill changes. Issue preparation does not authorize implementation or merge. Keep the existing merge policy.

## Writing

Use [Writing rules](docs/writing.md) for documents and specifications. This project is trying ASD-STE100 with the available simple-english skill. Do not claim full compliance without a review against the official standard and dictionary.

Write and revise skills with [Skill style](docs/dev/skill-style.md). Put a rule that several skills share in `references/shared/`, not in each skill.

Keep facts, command names, identifiers, and quoted errors unchanged. Define necessary technical terms at first use. Do not invent terms when ordinary words are sufficient.
