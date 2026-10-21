# Setup

Install `ghflow` from a full checkout of this repository.
The agent uses this source checkout while it works in a target project.

## Requirements

Install Git, Python 3, and GitHub CLI (`gh`) in the agent environment.
Keep a local checkout of the target project for code investigation.
A command-line interface (CLI) accepts commands in a terminal.
The standard-library CLI in [cli/ghflow.py](../cli/ghflow.py) handles repeatable operations.
It uses existing Git and `gh` commands for other work.

Observed on 2026-10-09 while running `make check`: Python 3.14.7 and GitHub CLI 2.101.0.
These are observed versions, not minimum supported versions.

### Operation requirements

- Reading: [reconsider-issue](../references/tasks/reconsider-issue.md) needs a target checkout, source access, and permitted GitHub reads.
- Implementation: [implement-issue](../references/tasks/implement-issue.md) makes local commits. Subagents use the configured [machine identity](../references/shared/identity.md) and need target repository access for Git and GitHub commands.
- Coordinated delivery: [express-issue](../references/tasks/express-issue.md) needs [subagent dispatch](../references/shared/coordination.md#handoffs). Review follow-up leaves the PR open.
- Independent review: [review-changes](../references/tasks/review-changes.md) uses a fresh context and, by default, a different model recorded from runtime or dispatch metadata. See [Review](../references/shared/review.md).
- Board work: when a task uses a project board, select that board, use its actual Status options, and make sure the machine identity has writer access. See [Board status](../references/shared/board-status.md) and [Machine account access](#machine-account-access).
- Merge: [merge-pr](../references/tasks/merge-pr.md) needs separate, explicit authorization under [Authorization](../references/shared/authorization.md#limits).

Apply each [user-approved review exception](../references/shared/review.md#user-approved-exceptions) within its recorded scope. Report unavailable dispatch or model information. Self-review does not replace independent review. Direct operations remain usable without a coordinator, subject to their own requirements.

## Install the skill

Keep a full checkout of this repository.
A symbolic link is a path that points to another location.
From the source checkout, install personal symbolic links with:

```sh
python3 scripts/install-skill.py claude codex
```

A symbolic link points to the source checkout root. Source edits appear through the links without another installation.
The installer preserves correct links and refuses existing conflicting entries before it creates links.
It creates `~/.claude/skills/ghflow` and `~/.agents/skills/ghflow`.
OpenCode also discovers these compatible directories. See the [root-package setup trial](research/trials/2026-10-07-ghflow-root-setup.md) for tested discovery and limits.
If you use only OpenCode, run `python3 scripts/install-skill.py opencode` for its native personal directory.
Do not add a native OpenCode link when compatible links already expose `ghflow`.

For one target project, use `--project TARGET_PATH` with the agent names.
For an isolated personal installation trial, use `--home TEMP_HOME`.
These options change the link destinations, not agent authentication or configuration.
The installer does not remove older generic skill installations. Remove those links separately after you inspect their sources.
If you move the source checkout, replace its stale links manually. The installer refuses to overwrite them.

## Try a read-only task

After you install `ghflow`, start an agent session in a local checkout of the target repository.
The agent needs the installed skill and access to its source checkout.
It also needs permission to read the target issue and related GitHub records.

Copy this request:

```text
Use ghflow to reassess https://github.com/lmorchard/gh-project-workflow/issues/23. Return findings only. Do not edit GitHub records or implement changes.
```

The [reconsider-issue task](../references/tasks/reconsider-issue.md) returns current evidence, remaining work, and unresolved decisions.
The request forbids repository and GitHub writes. Issue #23 is closed.
If current evidence shows that it is resolved, a result with no remaining work is correct.

## OpenCode discovery limits

OpenCode can discover nested `SKILL.md` files inside the linked checkout, including Git-ignored worktrees.
Repository checks ignore worktrees, but native discovery does not.
The selected policy documents this limitation and permits root checkout links without an installer guard.
Inspect the installed source's worktrees for nested skill files.
Maintain worktrees through authorized cleanup, and preserve worktrees with uncommitted changes or an open PR.
If additional skills are unwanted, use a separate source checkout without nested skill packages.
The [root-package trial](research/trials/2026-10-07-ghflow-root-setup.md#nested-worktree-discovery) records the evidence and decision.

## Prepare the project facts

After the first task in a project, ask for the project facts file:

```text
Use ghflow to prepare the project facts for this repository.
```

The agent writes `.ghflow/project.md` with the worktree setup, gates, generated files, test layout, and conventions that workers otherwise rediscover in every session, and records the source files it read. `python3 "$GHFLOW_CLI" facts` reports the live checkout and issue state and names the sources that changed since the file was written. Refresh the file when it reports stale sources, not on a schedule.

## Request another operation

Start a new agent session in the target project. Request an operation explicitly:

> Use ghflow to define issue #123. Produce a draft only. Do not publish or implement.

> Use ghflow to deliver issue #123 through review follow-up.

> Use ghflow to review PR #456.

Read [ghflow](../SKILL.md) for routing and dependency access.
The entry skill resolves the source checkout root and uses its absolute `cli/ghflow.py` path.
Commands preserve the target project's current directory.
It does not require the workflow checkout to be the current directory.

## Source access permissions

The agent needs access to the resolved source checkout, including `references/`, `docs/writing.md`, and `cli/ghflow.py`.
If the agent requests external directory access, permit that source checkout for this task.
A link does not grant tool permissions.
For Claude Code, `--add-dir SOURCE_CHECKOUT` includes that checkout in the session's allowed directories.
Codex's read-only sandbox allowed these dependency reads in the setup trial.

OpenCode prompts for external directory access by default. An `opencode run --auto` session approves those prompts, but an interactive session stops at each one until you answer it. ghflow writes to two places outside the target project: coordinator task notes under `~/.local/state/ghflow/notes/`, and PR body files in a temporary directory, as [submit-pr](../references/tasks/submit-pr.md) allows. Merge these narrowly scoped rules into the target project's `opencode.json` after you inspect its existing rules:

```json
{
  "permission": {
    "external_directory": {
      "/ABSOLUTE/SOURCE_CHECKOUT/*": "allow",
      "/ABSOLUTE/HOME/.local/state/ghflow/*": "allow",
      "/tmp/*": "allow"
    },
    "edit": {
      "/ABSOLUTE/SOURCE_CHECKOUT/*": "deny"
    }
  }
}
```

Replace the source checkout paths with the resolved source checkout and `/ABSOLUTE/HOME` with your home directory.
The first rule permits source access, and the `edit` rule blocks file-tool edits to it. The other two let workers write notes and body files without a prompt. Other tool permissions still apply.
On 2026-10-13, an interactive delivery waited 40 minutes at a prompt for a write to `/tmp/pr1067-body.md` before anyone noticed.
The installer does not change agent permissions or write this configuration.
See [OpenCode permissions](https://opencode.ai/docs/permissions/#external-directories) for directory and tool rules.

## Run a queue unattended

`scripts/unattended-burndown.sh` composes the request for an unattended Ready-queue burndown and launches one agent session with it. Run it from the target project checkout:

```sh
/PATH/TO/ghflow/scripts/unattended-burndown.sh --owner OWNER --project NUMBER --hours 8 --agent opencode --model llama.cpp/llama --same-model-exception
```

The request names the board, the review-follow-up endpoint without merge, the unattended rule from [Decisions](../references/shared/decisions.md#decide-in-an-unattended-flow), the deadline from `--hours`, and, with `--same-model-exception`, the user's approved same-model review exception. `--agent` selects `opencode`, `claude`, or `codex`; the script inlines the entry skill for `opencode run`, as the [#1012 trial](research/trials/2026-10-12-issue-1012-qwen-delivery.md) did. On macOS it runs under `caffeinate` so the machine does not sleep. Output goes to the file named by `--log`, default `unattended-burndown-TIMESTAMP.log` in the current directory. `--dry-run` prints the request and the command without launching.

In the morning, `gh pr list --author MACHINE_LOGIN` lists the delivered PRs, and the project's needs-input view, or `gh issue list --label triage:needs-input`, lists the parked issues with their questions as comments.

For OpenCode, the launcher refuses to start while a session titled "Unattended burndown" was active in the last 30 minutes, and names it; pass `--allow-concurrent` only on purpose. An OpenCode run keeps going on OpenCode's background service after its client exits, so the launcher's "finished" line does not prove the run ended. To stop a run, delete its session with `opencode session delete SESSION_ID`; killing the client leaves it running. The launcher also starts OpenCode with `OPENCODE_DISABLE_AUTOUPDATE=1`, and it warns when less than 30% of memory is free or a virtual machine such as Docker Desktop's is running, because other jobs slow the local model and can exhaust its cache. To keep OpenCode from upgrading between runs as well, set `"autoupdate": false` in its configuration.

The log holds only the coordinator's event stream. To keep the transcripts, run `scripts/export-opencode-sessions.py "Unattended burndown"` from the project checkout after the session ends. It finds the coordinator session by that title, exports it with `opencode export`, follows each task call to its subagent session, and writes `session-ID.json` files with an `index.md` of titles, parents, times, and task calls into `opencode-sessions/` or the `--out` directory. Pass a session ID instead of a title when more than one session matches.

`scripts/trial_stats.py DIR` summarizes those exports for a trial record. It reports each session's times, output tokens, largest context, reference reads before the worktree, other reads, shell commands by kind, amends, and force pushes, and the coordinator's dispatch timeline. `--watch TEXT` counts mentions of a string, such as the configured default model, and `--json` prints the raw figures. It reads OpenCode 1.x and 2.x exports.

## Machine account access

The repository owner grants access before an agent works in the repository or project board:

- Add the machine user as a repository collaborator with Write access.
- For a user-owned project board, add the machine user as a writer with `scripts/add-board-writer.sh OWNER PROJECT_NUMBER LOGIN`.

Resolve the script from the source checkout containing the entry skill. Do not resolve it from the target project.
The [identity reference](../references/shared/identity.md) supplies runtime configuration and credential handling.
The [identity research and trials](research/agent-identity.md) document records the adoption evidence and historical limits.
