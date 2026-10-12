---
name: ghflow
description: Prepare GitHub issues, implement selected issues, review changes, submit PRs, address feedback, and coordinate explicitly requested delivery. Use for Git and GitHub project tasks, including requests to tackle or deliver an issue. Merge requires explicit authorization; do not select backlog work unless requested.
---

# GitHub workflow

Select the requested operation and follow its task reference. Each operation works on an ordinary issue or PR without earlier ghflow tasks. Load only the task and shared rules needed now. Apply [Working context and tool output](references/shared/context.md) to reference loading, searches, and handoffs.

## Locate the source and tools

Resolve this `SKILL.md` path through any symbolic link. Its parent is `GHFLOW_SKILL_DIR`. Use absolute paths below that directory for references and subagent handoffs. Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` below it before running command examples. Quote the path. A command tool can start a new shell for each call, so export the variable in each command that uses it, or write the full path:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

Replace `ABSOLUTE_SKILL_DIRECTORY` with the resolved directory. The resolved skill directory is the source checkout root. Use its `cli/ghflow.py` directly. Keep the current directory at the target project so Git, GitHub, and identity configuration use that project. Resolve writing guidance through each reference's links, not through the current directory. If source reads need external directory permission, report the resolved checkout path and use the setup instructions in [Source access permissions](docs/setup.md#source-access-permissions). Do not silently change agent permissions.

The selected task reference names the shared rules it needs. Open a shared reference when its condition applies, and read the section that owns the decision; do not read every shared reference before the first action. The conditions: [Authorization](references/shared/authorization.md) when a permission or scope question arises; [Evidence](references/shared/evidence.md) before you report a result or pass on an identifier; [Decisions](references/shared/decisions.md) when a fact or choice is missing; [Agent identity](references/shared/identity.md) before a subagent runs Git or GitHub commands; [GitHub writes](references/shared/github-writes.md) before changing GitHub records. CLI reads do not grant permission to write.

## Select the requested operation

Match the user's explicit request to the operation below. Identify the subject repository from the user's request or the target checkout. The source checkout supplies instructions and tools; its remote and the configured account do not identify the subject. If the selected repository, issue, or PR is missing, return the needed input before GitHub searches or dispatch. For an assessment-only request, explain the operation and limits without performing delivery. If a material endpoint is unclear, ask only for that decision. Do not choose backlog work or add a fixed sequence. A delivery request defaults to review follow-up with its PR left open. Read its coordinator reference for subagent dispatch and different-model review requirements.

| Request | Task reference |
|---|---|
| Reassess an existing issue | [reconsider-issue](references/tasks/reconsider-issue.md) |
| Define an idea or issue, including draft-only work | [define-issue](references/tasks/define-issue.md) |
| Settle issue decisions with the user | [interview-issue](references/tasks/interview-issue.md) |
| Split a broad parent into children | [decompose-parent-issue](references/tasks/decompose-parent-issue.md) |
| Publish a reviewed issue draft | [file-issue](references/tasks/file-issue.md) |
| Implement an issue through local commits | [implement-issue](references/tasks/implement-issue.md) |
| Independently review code changes | [review-changes](references/tasks/review-changes.md) |
| Publish committed changes as a PR | [submit-pr](references/tasks/submit-pr.md) |
| Address PR feedback and repair CI | [address-pr-review](references/tasks/address-pr-review.md) |
| Merge an explicitly authorized PR | [merge-pr](references/tasks/merge-pr.md) |
| Deliver or tackle one selected issue | [express-issue](references/tasks/express-issue.md) |
| Deliver an agreed parent issue | [deliver-parent-issue](references/tasks/deliver-parent-issue.md) |
| Group related issues under themes | [bundle-issues](references/tasks/bundle-issues.md) |
| Assess a requested set of open issues | [triage-issues](references/tasks/triage-issues.md) |
| Resolve issues needing input | [sweep-needs-input](references/tasks/sweep-needs-input.md) |
| Define accepted issues | [sweep-needs-definition](references/tasks/sweep-needs-definition.md) |
| Return unblocked issues to definition | [sweep-blocked](references/tasks/sweep-blocked.md) |
| Audit closed issues | [sweep-audit-closed](references/tasks/sweep-audit-closed.md) |
| Prioritize a requested board scope | [sweep-prioritize](references/tasks/sweep-prioritize.md) |
| Stage issues into the Ready queue | [curate-ready-queue](references/tasks/curate-ready-queue.md) |
| Deliver an explicitly requested Ready queue | [burndown-ready-queue](references/tasks/burndown-ready-queue.md) |

## Execute and hand off

For sustained work or findings that would be costly to reconstruct, apply [Task notes](references/shared/task-notes.md). On resumption or after context compaction, read the task's existing notes before repeating research or reopening decisions.

Follow the selected reference's scope and stopping point. Carry existing authorization across included tasks. Draft-only and read-only limits still apply; implementation or submission never implies merge permission.

For delegation, apply [Coordination](references/shared/coordination.md#handoffs). Give the subagent the selected operation and required inputs. If delegation or the required reviewer model is unavailable, follow the shared rules and report the limit.

Return the operation's actual result, sources, checks, and remaining decisions. Report missing capabilities and incomplete evidence explicitly.
