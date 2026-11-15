# Direction history

This record preserves the earlier discussion, including proposals and superseded policies.
Read [Project direction](../dev/direction.md) for current guidance. The sections below describe their original context.

This document records the discussion with Les on 2026-09-30. The project will help a person and an agent take an idea through code review and merge. A merge adds approved changes to a target branch.

## Why start separately

In agent-sessions, the workflow grew into Bash scripts and then a Python program that controlled agents. Tools for repeatable operations produced useful results. Les questioned whether automatic control became the main concern before individual tasks were useful enough.

This concern motivates the new project. We did not measure which approach is better. A separate repository lets us reconsider the design and keep agent-sessions as a reference.

## Agreed direction

An agent skill supplies instructions to an agent. A command-line interface (CLI) accepts commands as text. This project will pair a skill with a CLI for repeatable operations.

The tasks include issue definition, issue creation, project boards, code changes, pull request review, and merge. A pull request (PR) proposes changes for review. Each task must be useful before we combine it with other tasks.

We will record findings first. We will not copy the entire old skill or its control program. The first useful tool does not require all phases of the workflow.

## Agent and CLI responsibilities

The agent interprets requests, defines scope, chooses actions, changes code, and assesses review findings. The CLI accepts explicit inputs and does a specified operation. It returns facts and the result of the operation.

Possible operations include issue reads, PR reads, workspace creation, issue updates, board updates, PR creation, and requested merges. These are proposals. We did not select command names.

The initial CLI will not call a model, select the next issue, or infer human approval. It will not select the next phase. Existing git and gh commands remain available.

The old control program gave the agent read-only GitHub credentials. Separate code made the requested changes with other credentials. Instructions alone cannot enforce that restriction.

This project initially relies on permissions in the agent application and authorization from the user. Stronger restrictions for unattended use require a separate design. A skill does not replace those restrictions.

## Development sequence

Use this sequence:

1. Make one operation useful by itself.
2. Use the operation and skill instructions to do one real task.
3. Try the task in a new session to find missing information.
4. Combine steps when repeated use shows a benefit.

Each phase must accept an ordinary existing issue or PR. Earlier tasks do not need this system. Use GitHub records and Git history to leave information for the next session where possible.

## Keep the process useful

Les observed that agent-sessions sought less documentation ceremony but introduced new ceremonies along the way. Ceremony means required steps or records that add little practical value. A simpler workflow can become complex again through individually reasonable additions.

A required document or step must help someone make a decision, do the task, or continue it later. Use an existing issue, commit, or test result when it supplies that information. Do not require another record merely to prove that the process occurred.

Keep trial records when they answer a real question about a skill. Do not turn the records from these first experiments into mandatory files for every task. Remove or combine steps when actual use shows that they duplicate effort.

This principle does not require another checklist, approval, or report. Judge the process by the useful work it supports and the effort it requires.

## Proposed design principles

These principles are proposals for the first experiments. They describe desired behavior, not implemented features. Real use will supply evidence for changes.

We propose that tools distinguish missing data, pending activity, and failed requests. A result must not show success when a request failed. When a change succeeds, the tool reports what changed.

We propose that tools use expected versions or commit identifiers to detect changes after a read, where supported. A commit records a version of files in Git. Its identifier names that version.

We propose that retries do not create duplicate changes where prevention is possible. If only some steps succeed, the tool reports those steps. It does not claim that all steps succeeded or that none took effect.

We propose separate decisions about task readiness, evidence, and permission. Plans and test records can be as short as the task permits. A favorable review does not itself authorize a merge.

## Open decisions

We selected issue definition for the first skill trial. The [First experiment](first-experiment.md) describes the task and evaluation. The [CLI decision](#cli-decision) selects the first CLI operations. The CLI language, package format, and command names remain open.

Automatic scheduling, background polling, custom session storage, attempt labels, and a special merge-result format remain outside the initial effort. Les also requested an ASD-STE100 trial. The [Writing rules](../writing.md) describe that trial and its limits.

## CLI decision

On 2026-10-02, Les decided that the project will build a small deterministic CLI. It will do these three operations:

- Read the state of a PR for its current head: each check result, review requests including automatic requests, and completed reviews with their commits.
- Verify that a commit identifier exists and names the expected commit before an agent uses it in a handoff, report, or merge.
- Apply a board status transition to one issue: identify the board, use the actual status option, refuse a backward move, and read the result back.

The issue 843 delivery supplied the evidence. A stale handoff moved the parent backward on the board, an agent copied a commit identifier incorrectly, and Copilot request detection needed repeated corrections. Skill text alone did not prevent these errors. The [delivery retrospective](trials/2026-10-02-parent-843-delivery.md) records them.

All three operations exist in `cli/ghflow.py` as `pr-state`, `verify-commit`, and `board set-status`, and the shared references use them. The CLI does not select tasks, call a model, schedule work, or infer approval. It is not a general harness. The skills continue to use existing git and gh commands for other operations. When an operation exists, the relevant skills will use it instead of their written procedure.

## Implementation scope

Les requested an implementation skill that uses ordinary development practices. It will plan against current code, use an isolated worktree, add useful tests, review changes, and report results. The skill ends with local commits for PR preparation.

The frozen-check scheme from agent-sessions is deferred. This project does not plan to restore freeze commits, locked test files, or a separate validation system. Any later proposal for such machinery requires evidence of a problem that ordinary tests and review do not address.

## Interactive issue review

Les prefers interviews and interactive questions to reviewing draft files. The agent explains its findings and recommendation in the conversation. It asks focused questions about decisions that need user judgment, then updates the draft itself.

Draft files support the conversation but are not required reading for approval. Before requesting publication permission, the agent summarizes the concrete changes. Existing decisions and permissions remain valid within their scope. Les wants an agreed issue-preparation flow to continue through publication without separate approval at every skill boundary. Explicit draft-only limits still apply. Product questions remain interactive; a change of skill alone is not a reason to stop. Changes that Les reviews or weighs in on do not require a separate authorization check. Revisit authorization only when a significant change falls outside the reviewed or authorized scope.

## Review approach

Superseded by the 2026-10-03 machine-account policy (see [Future agent identity](#future-agent-identity) and [Review](../../references/shared/review.md)). Under that policy, independent local review is the primary review source for an agent pull request, and the user requests Copilot review manually. The text below keeps the earlier discussion.

PR submission will request Copilot review when available. If access is unavailable, the parent can dispatch a local reviewer in a fresh context. The local reviewer must use a different model from the implementer for this fallback.

The parent records model identities from available session or dispatch information. If identity or model selection is unavailable, it reports the limit. A same-model second opinion does not silently replace the requested different-model review.

Copilot is an external review service, but its underlying model can be unknown. We do not claim model diversity without evidence. This preference does not replace tests, human judgment, or review of the actual findings.

The independent reviewer reports findings without changing code. Submission publishes the PR and requests review. The separate address-pr-review task waits up to 20 minutes and addresses available findings. A further review after corrections remains pending unless another cycle is requested.

No fixed report files are required. None of these tasks merges the PR. A timeout remains an incomplete review, not approval.

PR follow-up also watches hosted CI for the current commit. It corrects failures and repeats checks until CI passes or a concrete blocker requires user action. The review deadline does not limit CI repair or turn missing checks into success.

## Merge policy

Les requires green CI and prefers Copilot review. A literal approving review is not required by this workflow. The agent often submits PRs as the user, and GitHub does not let authors approve their own PRs.

Green CI alone does not permit an autonomous merge. The agent also needs affirmative review evidence within existing merge authorization, or explicit user permission to merge the PR.

A favorable review can come from a person, Copilot, or an independent local reviewer. A COMMENTED review can qualify if its text recommends approval or clearly reports a completed review with no findings. Silence, an empty comment list, and a review timeout do not qualify.

On 2026-10-02, Les decided that a Copilot review headed "Needs a closer look" is not affirmative review, even with "Findings: None". Its text asks for human review. On 2026-10-03, Les also decided that a different-model local review does not answer that request; the merge decision goes to him. review.md states both ([scenario results](../../evals/results/2026-10-03-cleanup-and-review-substitute.md)).

On 2026-10-03, Les also decided that when Copilot is unavailable, a different-model local review is the review source without a question to him. This includes a request that GitHub does not record, as in the [identity trial](agent-identity.md#trial-results), and a Copilot review that times out.

Permission to implement or submit does not imply permission to merge. Existing explicit merge permission remains valid within its scope, so the agent does not need to ask again. Unresolved defects, human objections, and repository protection rules still require attention.

Merge uses explicit user authorization and checks the current commit. It does not bypass GitHub rules or weaken checks. The result includes confirmed merge, issue, and board state.

## Future agent identity

Les reported that agent-sessions tried a second GitHub account and later a GitHub App for agent contributions. A separate identity would distinguish agent actions from Les's actions in GitHub records. It could also let Les review contributions as a separate person.

We may return to this approach after the individual tasks work well. First inspect the earlier work for useful parts and limits. Then define the permissions and account setup that this project needs. This is a future option, not a requirement for the current skills.

On 2026-10-03, research for [issue 1](https://github.com/lmorchard/gh-project-workflow/issues/1) found that only a machine user works with user-owned boards, and that it probably needs a paid Copilot seat. Les asked for a trial before a decision. [Agent identity](agent-identity.md) records the research and the trial proposal.

On 2026-10-03, Les adopted the machine user identity after trials in a scratch repository and on decafclaw issue 897. Subagents run under a configured machine account such as `MokaGnome`. The configuration supports environment variables with a config file fallback. The CLI operations `identity` and `exec` in `ghflow.py` supply the credentials. For code review on agent pull requests, independent local review is the primary review source. Les can request a Copilot review manually when desired.

## Possible next-task guidance

Les proposed a skill that helps answer “what is next?” after using the individual skills. One possible starting point is advice based on the current issue or PR, available evidence, unresolved decisions, and existing authorization. It can explain which task fits and why.

Automatic dispatch remains an open design choice. A recommendation does not grant permission to publish, implement, or merge. We will use the current trials to identify useful conditions before defining this skill. This proposal does not add a scheduler or require every task to pass through a fixed sequence.

## Draft express path

Les proposed a bounded path through implement-issue, review-changes, submit-pr, and address-pr-review. It continues through routine handoffs while existing authorization covers the work. It returns to the user when a material decision or blocker requires intervention. Merge remains a separate task with its existing policy.

The draft express-issue skill passes evidence, source revisions, review results, and authorization between these tasks. It must preserve the separate tasks for direct use. It must also report unavailable independent review rather than silently treating self-review as its replacement.

The express-issue draft defaults to review follow-up and includes merge only when explicitly authorized. It includes local review before submission with a different recorded model. An unavailable model identity returns a review choice to the user instead of silently changing that requirement.

The [Trial records](trials/README.md) describe the express trials and their evidence limits.

## Draft parent delivery flow

After the single-child trials, Les requested delivery across the remaining groups in decafclaw #843. The deliver-parent-issue draft coordinates decomposition, child definition and filing, express delivery, and parent completion checks. Its task selection stays within the selected parent and agreed scope. This is a bounded use of orchestration, not general backlog scheduling.

The flow carries existing authorization across children and keeps material decisions in the user conversation. Each merge requires affirmative independent review and green hosted CI on the final changes. A final coverage check must establish the parent result before closure. The first full parent-delivery trial finished on 2026-10-02. The [delivery retrospective](trials/2026-10-02-parent-843-delivery.md) records the results, scope decisions, limits, and proposed changes. No skill revision was made from those proposals during the trial wrap-up. Later revisions, checked with scenarios, are listed in the [Trial records](trials/README.md).

## Proposed queue runner, 2026-11-15

Following seven unattended burndown trials with local models where model coordinators degraded or failed to maintain discipline, Les approved building a deterministic queue runner (`scripts/run_queue.py`). The runner uses a pure reconciliation loop over GitHub state to select the next item and step, launching fresh model sessions for individual operations. Automatic task selection remains strictly limited to curated columns on the project board, without scheduling, polling, or drawing from Backlog. See [Queue runner proposal](queue-runner.md).
