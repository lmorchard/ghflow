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
A link to a separate checkout shows source edits only after `git -C ~/.agents/skills/ghflow pull --ff-only`.
The installer preserves correct links and refuses existing conflicting entries before it creates links.
It creates `~/.claude/skills/ghflow` and `~/.agents/skills/ghflow` on a clean installation.
If `~/.agents/skills/ghflow` is already a separate checkout, do not run the `codex` target. The installer refuses that destination.
The installer has no option to link another agent to the separate checkout.
Create that link by hand after you inspect and remove an old link:

```sh
ln -s ~/.agents/skills/ghflow ~/.claude/skills/ghflow
```

Keep an existing link if it already points to the separate checkout.
OpenCode also discovers these compatible directories. See the [root-package setup trial](research/trials/2026-10-07-ghflow-root-setup.md) for tested discovery and limits.
If you use only OpenCode and the source checkout has no worktrees, run `python3 scripts/install-skill.py opencode` for its native personal directory.
Do not add a native OpenCode link when compatible links already expose `ghflow`.
If the source checkout has worktrees, use the separate OpenCode checkout below.

### OpenCode separate checkout

OpenCode discovers nested `SKILL.md` files through a symbolic link, including copies in `.claude/worktrees/`.
A worktree copy can become the selected skill instead of the main checkout.
When the source checkout has worktrees, use a separate checkout for OpenCode at `~/.agents/skills/ghflow`.
Do not link a working clone that has worktrees.

Create the separate checkout once:

```sh
git clone git@github.com:lmorchard/ghflow.git ~/.agents/skills/ghflow
```

Refresh it after skill changes:

```sh
git -C ~/.agents/skills/ghflow pull --ff-only
```

Do not edit the installed checkout.
Make skill changes in the source checkout, publish them, and pull them in the installed checkout.
Run `python3 "$GHFLOW_CLI" facts` from a subject checkout and confirm that `skill_source.head` names the intended revision.
A separate checkout without worktrees gives OpenCode one copy of the skill.
Check it with:

```sh
git -C ~/.agents/skills/ghflow worktree list
```

If it lists more than the main checkout, remove a worktree only when it has no uncommitted changes and no open PR.
Otherwise use another clean checkout.
A worktree still exposes its copy through the separate checkout.

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
The selected policy permits root checkout links for a clean source checkout.
A working clone with worktrees can expose worktree copies, so use the separate OpenCode checkout above for that case.
The current OpenCode installation uses a separate checkout at `~/.agents/skills/ghflow` because OpenCode selected a worktree copy through the root link.
Inspect the installed source's worktrees for nested skill files.
Maintain worktrees through authorized cleanup, and preserve worktrees with uncommitted changes or an open PR.
If additional skills are unwanted, use a separate source checkout without nested skill packages.
The [root-package trial](research/trials/2026-10-07-ghflow-root-setup.md#nested-worktree-discovery) records the evidence and decision.

## Prepare the project facts

After the first task in a project, ask for the project facts file:

```text
Use ghflow to prepare the project facts for this repository.
```

The agent writes `.ghflow/project.md` with the worktree setup, gates, generated files, test layout, and conventions that workers otherwise rediscover in every session, and records the source files it read. A `worktree:` frontmatter declaration makes the setup executable, and `worktree create` applies it to every child worktree. `python3 "$GHFLOW_CLI" facts` reports the live checkout and issue state and names the sources that changed since the file was written. Refresh the file when it reports stale sources, not on a schedule.

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

`scripts/run_queue.py` drives unattended delivery from the project board with a deterministic reconciliation loop, starting a fresh session for each operation. Run it from the target project checkout:

```sh
python3 /PATH/TO/ghflow/scripts/run_queue.py --project OWNER/NUMBER --hours 8 --model llama.cpp/llama
```

`--project OWNER/NUMBER` selects the project board. If omitted, the runner automatically discovers the single open project linked to the repository. `--hours` sets the time budget (default 8). `--once` drives the single next item to its desired state and exits. `--model` overrides the model for worker sessions. A local model can take minutes to process a large context. The runner logs a warning after 120 seconds without events. It stops a step after `--step-idle-timeout` seconds (default 900). Raise the value for large contexts. On macOS it runs under `caffeinate` so the machine does not sleep.

For a parent issue, pass `--parent OWNER/REPO#NUMBER`; repeat `--parent` for several parent issues. Parent selection skips children labeled `triage:needs-input`, `triage:blocked`, or `triage:needs-definition`, and children with an open native blocked-by issue. It orders the rest by board Priority, then Size, then issue number. It creates a stack only for a native dependency, or with `--stack`. Use `--require-label impl:local` to keep a local-model run to local-fit children, and `--exclude 1294,1295` for one-off exclusions. The session turn cap follows the issue's Size unless `--max-turns` is set. The runner refreshes the ctags index for the subject checkout when it is missing or stale, so symbol lookups use definitions rather than a git-grep fallback.

Worker sessions inherit `GHFLOW_CLI`, so the CLI path is available and a worker does not need to re-export it. OpenCode shell commands can start in the project checkout rather than the task worktree. The runner tells workers to `cd` to the worktree or use absolute paths, and it warns when the primary checkout changes during a session. When the project facts declare `generated` paths, the runner leaves them out of the automatic commit and restores their tracked files in the worktree after publishing. `tags find SYMBOL --refs` returns definitions plus bounded code-only references. `review inspect` includes the PR checks, reviews, and verdicts; use `--no-gate` when the runner already ran `make check` at the head.

When the repository has Discussions and a `Lab Notebook` category (slug `lab-notebook`), the runner publishes a run notebook: it starts or reuses the day's `Run notebook YYYY-MM-DD` thread, appends one note for each session, and appends the run result. One short model call summarizes each session log; when that call fails, the note states the step and outcome. The runner also comments "Work started" on the issue when implementation begins. Use `--narrative-category SLUG` for another category, or `--no-notebook` to disable the thread and its model calls. When Discussions are disabled or the category is missing, the runner prints the reason once and continues with the local notes and the issue checkpoint.

In the morning, `gh pr list --author MACHINE_LOGIN` lists the delivered PRs, and the project's needs-input view, or `gh issue list --label triage:needs-input`, lists the parked issues with their questions as comments.

The runner runs one session at a time and deletes each OpenCode session after its step. It holds `~/.local/state/ghflow/runner.lock` for the run and refuses to start while another runner holds it. It also refuses to start while an unattended OpenCode session was active in the last 30 minutes; pass `--allow-concurrent` only on purpose. It starts OpenCode with `OPENCODE_DISABLE_AUTOUPDATE=1`.

To keep the transcripts, run `scripts/export-opencode-sessions.py "Queue runner"` from the project checkout after the run ends. It exports sessions with `opencode export` and writes `session-ID.json` files into `opencode-sessions/` or the `--out` directory.
`scripts/trial_stats.py DIR` summarizes those exports for a trial record. It reports each session's times, output tokens, largest context, reference reads before the worktree, other reads, shell commands by kind, amends, and force pushes, and the coordinator's dispatch timeline. `--watch TEXT` counts mentions of a string, such as the configured default model, and `--json` prints the raw figures. It reads OpenCode 1.x and 2.x exports.

## Machine account access

The repository owner grants access before an agent works in the repository or project board:

- Add the machine user as a repository collaborator with Write access.
- For a user-owned project board, add the machine user as a writer with `scripts/add-board-writer.sh OWNER PROJECT_NUMBER LOGIN`.

Resolve the script from the source checkout containing the entry skill. Do not resolve it from the target project.
The [identity reference](../references/shared/identity.md) supplies runtime configuration and credential handling.
The [identity research and trials](research/agent-identity.md) document records the adoption evidence and historical limits.
