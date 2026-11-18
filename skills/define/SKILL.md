---
name: ghflow-define
description: Research ideas, interview the user, define issue boundaries, and file structured GitHub issues. Use when specifying, scoping, or filing new issues or reconsidering existing issues.
---

# GitHub issue definition

Research ideas, interview the user, settle technical and product scope, and write structured GitHub issues. You operate at specification altitude: you define what the issue needs, its success criteria, and its verification plan. You do not create worktrees, write implementation code, or run test gates.

Before starting, apply [Execution mode](../../references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

Use `facts` to inspect live repository facts, existing issues, and board state:

```sh
python3 "$GHFLOW_CLI" facts
python3 "$GHFLOW_CLI" facts --issue ISSUE_URL
```

Open shared references when their conditions apply: [Interview issue](../../references/tasks/interview-issue.md) to settle user intent; [Decisions](../../references/shared/decisions.md) to separate intent from implementation choices; [Writing rules](../../docs/writing.md) for simplified English.

## Issue definition operations

| Operation | Task reference |
|---|---|
| Define an idea or issue, including draft-only work | [define-issue](../../references/tasks/define-issue.md) |
| Settle issue decisions with the user | [interview-issue](../../references/tasks/interview-issue.md) |
| Publish a reviewed issue draft | [file-issue](../../references/tasks/file-issue.md) |
| Reassess an existing issue against current code | [reconsider-issue](../../references/tasks/reconsider-issue.md) |
| Split a broad parent into children | [decompose-parent-issue](../../references/tasks/decompose-parent-issue.md) |
| Group related issues under themes | [bundle-issues](../../references/tasks/bundle-issues.md) |

For code implementation in a worktree, use the builder skill `ghflow-build`. For multi-issue queue and board orchestration, use `ghflow-coord`.
