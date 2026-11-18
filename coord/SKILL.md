---
name: ghflow-coord
description: Coordinate multi-issue delivery, parent epics, Ready queue burndowns, and board triage. Use for project-level planning, queue curation, and unattended burndown management.
---

# GitHub project coordination

Coordinate multi-issue delivery, parent epics, Ready queue burndowns, board triage, and queue automation. The coordinator manages project health, dependency ordering, and work scheduling; it delegates single-issue implementation and review to workers running [ghflow](../SKILL.md) or dispatches the deterministic runner (`scripts/run_queue.py`).

Before choosing how to execute an operation, apply [Execution mode](../references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help

# Audit runner session logs for repeated procedural toil (Three Strikes and You Automate):
python3 "$GHFLOW_CLI" audit toil [--last 30] [--min-strikes 3]
```

For unattended queue burndowns across a parent epic or Ready queue, drive the deterministic queue runner:

```sh
python3 ABSOLUTE_SKILL_DIRECTORY/scripts/run_queue.py --help
```

Open shared references when their conditions apply: [Authorization](../references/shared/authorization.md) when permission or scope boundaries arise; [Evidence](../references/shared/evidence.md) before reporting results; [Decisions](../references/shared/decisions.md) when a choice is missing; [Agent identity](../references/shared/identity.md) before Git or GitHub writes; [GitHub writes](../references/shared/github-writes.md) before mutating records.

## Select the orchestration operation

Match the user's explicit request to the coordination operation below:

| Request | Task reference |
|---|---|
| Deliver an agreed parent issue (epic) | [deliver-parent-issue](../references/tasks/deliver-parent-issue.md) |
| Deliver an explicitly requested Ready queue | [burndown-ready-queue](../references/tasks/burndown-ready-queue.md) |
| Stage issues into the Ready queue | [curate-ready-queue](../references/tasks/curate-ready-queue.md) |
| Split a broad parent into children | [decompose-parent-issue](../references/tasks/decompose-parent-issue.md) |
| Group related issues under themes | [bundle-issues](../references/tasks/bundle-issues.md) |
| Assess a requested set of open issues | [triage-issues](../references/tasks/triage-issues.md) |
| Prioritize a requested board scope | [sweep-prioritize](../references/tasks/sweep-prioritize.md) |
| Resolve issues needing input | [sweep-needs-input](../references/tasks/sweep-needs-input.md) |
| Define accepted issues | [sweep-needs-definition](../references/tasks/sweep-needs-definition.md) |
| Return unblocked issues to definition | [sweep-blocked](../references/tasks/sweep-blocked.md) |
| Audit closed issues | [sweep-audit-closed](../references/tasks/sweep-audit-closed.md) |
| Write or refresh the project facts file | [prepare-project-facts](../references/tasks/prepare-project-facts.md) |

For single-issue implementation, code changes, PR review, or feedback resolution in an isolated worktree, use the companion delivery skill [ghflow](../SKILL.md).

## Coordinate and dispatch

In delegated mode, apply [Coordination](../references/shared/coordination.md#handoffs). Write the handoff file before dispatching worker sessions, and carry decisions, base revisions, and limits across tasks.

Maintain project notes under [Task notes](../references/shared/task-notes.md) when findings or decisions are costly to reconstruct. Return verified results, remaining blockers, and decision points clearly to the user. After an unattended burndown or multi-issue run, audit worker operational logs with `python3 "$GHFLOW_CLI" audit toil` to identify repeated friction patterns hitting the Three Strikes threshold for deterministic automation.
