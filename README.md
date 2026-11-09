# ghflow

`ghflow` helps a person and an agent prepare GitHub issues, implement selected work, review changes, and deliver pull requests.
A pull request (PR) proposes changes for review.

## Get started

Install Git, Python 3, and GitHub CLI (`gh`) in the agent environment.
Keep local checkouts of this repository and the target project.
From this repository, install the skill for Claude Code and Codex:

```sh
python3 scripts/install-skill.py claude codex
```

The installer creates symbolic links, paths that point to this source checkout.
Keep the checkout available so the agent can read the skill and its references.
OpenCode also discovers these compatible directories. When the source checkout has worktrees, use a separate checkout for OpenCode. Read [Setup](docs/setup.md#opencode-discovery-limits).

Read [Setup](docs/setup.md) for OpenCode installation, project installation, source permissions, machine account access, and discovery limits.

Start a new agent session in the target checkout and try a read-only request:

```text
Use ghflow to reassess https://github.com/lmorchard/gh-project-workflow/issues/23. Return findings only. Do not edit GitHub records or implement changes.
```

For local-model work, ghflow keeps all authorized steps in the current session and forbids subagents.
Review uses a separate pass with the same model in that session.
[Execution mode](references/shared/coordination.md#execution-mode) explains mode selection and limits.

## Find the relevant docs

- [Setup](docs/setup.md): Installation, requirements, and access.
- [Operations](docs/operations.md): Tasks for issues, PRs, delivery, and project boards.
- [Documentation index](docs/README.md): Guides for the use of ghflow.
- [Development](docs/dev/README.md): Project direction, skill style, checks, and evaluations.
- [Research and history](docs/research/README.md): Earlier proposals, sources, and trial records.
- [Entry skill](SKILL.md): Routing from a request to the relevant task instructions.
- [CLI reference](references/cli.md): Results from commands that inspect PRs and commits.

## Develop the workflow

Read [Project direction](docs/dev/direction.md) and [Agent instructions](AGENTS.md) before changing the project. The [development index](docs/dev/README.md) lists the other development documents.
Use [Skill style](docs/dev/skill-style.md) for skills and [Writing rules](docs/writing.md) for documents.
Run `make check` before you commit. [Repository maintenance](docs/dev/maintenance.md) explains checks and branch cleanup.
