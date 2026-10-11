# Skill style

This is the house style for `SKILL.md` files and the shared references in `references/shared/`. Agents read skills to act, so write for an agent that is doing the task now. The strict [Writing rules](../writing.md) apply to documents, specifications, and issue text, not to skills.

## What a skill contains

A task reference owns one operation: the judgment and procedure that are specific to it. It links to shared references for policy that several skills apply. If a rule appears in two skills, it belongs in a shared reference.

Use these shared references instead of restating their rules:

- [Authorization](../../references/shared/authorization.md): permission, scope, and how authorization carries between tasks.
- [Coordination](../../references/shared/coordination.md): parent and subagent roles, dispatch, handoffs, and PR follow-up ownership.
- [Decisions](../../references/shared/decisions.md): factual research, routine choices, and questions that need user judgment.
- [Working context and tool output](../../references/shared/context.md): conditional reference reads, targeted inspection, complete inventories, and concise handoffs.
- [Task notes](../../references/shared/task-notes.md): concise working notes, their location, updates, and reuse after context loss.
- [Evidence](../../references/shared/evidence.md): source revisions, check states, hosted CI, and honest reports.
- [GitHub writes](../../references/shared/github-writes.md): duplicate prevention, saved-result readback, retries, and intervening changes.
- [Draft PRs and readiness](../../references/shared/pr-lifecycle.md): early progress publication, draft updates, and readiness.
- [Review](../../references/shared/review.md): review sources, model identity, Copilot request state, and what counts as affirmative review.
- [Board status](../../references/shared/board-status.md): moving an issue between project-board states.
- [Triage labels](../../references/shared/triage-labels.md): the `triage:*` labels, their meanings, and blocked and parked issues.
- [Agent identity](../../references/shared/identity.md): configuring machine account credentials and running commands under that identity.

Link a reference where its rules apply. Add a one-line summary only when the reader needs it at that point to act correctly. Agents do not reliably open a reference unless the skill says that it applies, so keep the trigger for a decision-critical rule in the skill: name the situation and link the rule. The [pilot run](../../evals/results/2026-10-02-pilot.md) showed this. Read the references when you write or review a skill.

Keep history out of skills. Old reasons and incidents mislead agents when the behavior changes. Record sources in [Skill sources](../research/skill-sources.md) and results in [Trial records](../research/trials/README.md).

## Structure

Only the root `SKILL.md` has frontmatter with `name: ghflow` and `description`. The source checkout directory can have any name. Task references have no skill frontmatter. The description says what the skill produces, when to use it, and its main boundary, such as "Do not merge."

Open with one short paragraph: the result and where the skill stops. Then order the sections in the sequence of the task. End with a section on what to return and hand off.

Use headings for steps of the task, not for categories of rules. Use a list only when the items really are parallel, such as review questions or response types.

## Language

Use plain technical English. Assume that the reader knows common terms such as PR, CI, commit, branch, head, base, and worktree. Define a project-specific term once, in the shared reference that owns it.

Use one word for one meaning across all skills. Write instructions as commands, in active voice. Keep a condition in the same sentence as its instruction: "If the head changes, read the checks again."

There is no fixed sentence-length limit. Split a sentence when it holds two separate instructions, not merely because it is long.

## Rules and prohibitions

State the rule positively when you can. "Read checks for the current head" covers several "do not" rules about earlier commits.

Use "Do not" for a specific temptation with a real cost, such as `gh pr create --dry-run` pushing changes. Keep concrete pitfalls like that one when they are not obvious and an error is expensive.

Before you add a rule for an incident, look for the general rule that the agent missed. Strengthen or clarify that rule instead of adding a new special case. Record the incident and the commit in [Trial records](../research/trials/README.md).

When an authorized workflow improvement changes a future task decision, update the owning task or shared reference. Add a reusable scenario with separate grading criteria. Keep the observed evidence and its limits in the source or trial record. A passive record alone does not deliver that behavior change. Propose other opportunities separately when authorization does not cover them. This rule does not require changes or a report after every task.

Test each sentence: would an agent act differently without it? If not, remove it. Remove rules when use shows that they add text without changing results.

## Commands

Show a command only when its exact form matters. Otherwise, name the operation and tell the agent to check the installed `gh` help. Installed versions differ.

Use placeholders in capitals, such as `PR_URL`. Do not show a command that the agent must change in ways the text does not explain.
