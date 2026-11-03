# Agent identity

These rules apply to every agent that runs Git commands or interacts with GitHub, including the current agent in single-session mode.

## Overview

Agents perform subject-repository actions under a designated machine account (such as `MokaGnome`). This distinguishes agent contributions from human actions on GitHub and allows the user to submit approving reviews on agent PRs.

## Configuration

Configure the agent identity using environment variables or a configuration file.

### Environment variables

- `GHFLOW_IDENTITY_LOGIN` (or `GHFLOW_LOGIN`): machine account GitHub username.
- `GHFLOW_IDENTITY_NAME` (or `GHFLOW_NAME`): name for Git commit author and committer.
- `GHFLOW_IDENTITY_EMAIL` (or `GHFLOW_EMAIL`): email for Git commit author and committer.
- `GHFLOW_TOKEN_FILE`: path to a file containing the machine account personal access token.

### Configuration file

Explicit `GHFLOW_*` values take precedence over configuration-file values. In a Git repository, `ghflow` checks these files in order:

1. `.ghflow/identity.json` at the current worktree root.
2. `.ghflow/identity.json` at the primary checkout root, when the current directory is in a linked worktree.
3. `~/.config/ghflow/identity.json`.

Git discovers the repository roots, so running `ghflow` from a subdirectory uses the same project configuration as the repository root. A nested repository uses its own configuration. Outside a Git repository, `ghflow` checks `.ghflow/identity.json` in the current directory, then the home configuration file.

The `identity` result includes `source`: `environment` when an explicit `GHFLOW_*` value is selected, otherwise the absolute path of the selected configuration file, or `null` when no configuration file is selected. This field does not include secret values. If a selected configuration file cannot be read or does not contain a JSON object, identity resolution reports an error and does not fall through to a lower-priority file.

Configuration discovery uses local Git metadata and file paths. It does not confirm a GitHub account. The separate `ghflow exec` and board-write paths load credentials and perform any required account confirmation.

Configuration files use this shape:

```json
{
  "login": "MokaGnome",
  "name": "MokaGnome",
  "email": "me+mokagnome@lmorchard.com",
  "token_file": "~/.config/ghflow/mokagnome.token"
}
```

The token file must have mode 600 permissions. The token needs `public_repo`, `project`, and `read:org` scopes.
The selected token file takes precedence over inherited `GH_TOKEN` and `GITHUB_TOKEN` values.
If the selected file is missing, unreadable, or empty, `ghflow exec` stops before it starts the child command.
Without a selected token file, `GH_TOKEN` can supply the token.
`ghflow exec` removes inherited `GITHUB_TOKEN` values.
The selected author name and email replace inherited Git author and committer values.
The selected name falls back to the selected login.
`identity --export` removes inherited `GITHUB_TOKEN` from the shell that evaluates its output.
The `identity` result reports `configured` for configuration presence.
It reports `ready` when a login and non-empty token are available.
`ready` checks local inputs. It does not confirm that GitHub accepts the token.

Inspect the active identity configuration with:

```sh
python3 "$GHFLOW_CLI" identity
```

## Running commands under the identity

Use `ghflow exec` to run Git or `gh` commands with the identity environment:

```sh
python3 "$GHFLOW_CLI" exec -- gh pr create ...
python3 "$GHFLOW_CLI" exec -- git commit -m "..."
python3 "$GHFLOW_CLI" exec -- git push origin BRANCH
```

`ghflow exec` sets:

- `GH_TOKEN` from the selected token file, when one is selected.
- `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME`, and `GIT_COMMITTER_EMAIL` from the selected identity fields.
- `GIT_CONFIG_PARAMETERS` so GitHub HTTPS operations use `gh auth git-credential`.
  Other Git configuration parameters remain available.

Before a direct `git commit`, `ghflow exec` requires a selected author name and email.
This check does not require a GitHub read, so a local commit can remain offline.
The command does not inspect scripts or other arbitrary subprocesses for hidden writes.

Before a GitHub write, confirm that the active token belongs to the selected login.
Run `gh api user` under the selected identity and compare its `login` value.
The CLI confirms this account before its board status writes.
The CLI does not infer write intent in arbitrary `ghflow exec` commands.

The `ghflow` commands `pr-state`, `verify-commit`, and `board set-status` apply the configured identity to their own `gh` calls. They do not need `ghflow exec`.
`board set-status` also checks the authenticated login before it adds or edits a board item.

Alternatively, export the environment into the current shell:

```sh
eval "$(python3 "$GHFLOW_CLI" identity --export)"
```

`identity --export` writes POSIX shell statements. You can evaluate them in a
POSIX-compatible shell, including `sh`, `bash`, or `zsh`. The output quotes each
value so shell characters in the configured identity remain literal.

Do not print, log, or echo raw token content. Do not run `gh auth login`, `gh auth switch`, or `gh auth logout`.

## Personal approval

Do not submit a GitHub APPROVED review as the repository owner from an agent. A formal GitHub approval is the user's personal action.
Follow [Review](review.md) for review sources and requirements.

## Access failures

The machine account needs repository and project access before a task starts. [Machine account access](../../docs/setup.md#machine-account-access) describes setup.
If access is missing, report the required action. Do not switch accounts or change credentials to bypass the failure.

### Sandboxed GitHub checks

A sandbox can block access to the host keyring or GitHub. A failed GitHub check inside a sandbox does not by itself show that the token is invalid.

Run `gh auth status` inside the configured identity. If the command runs in a sandbox, run `gh auth status` in an approved host context without a `GH_TOKEN` override.
Compare the active host account and required scopes with the configured login. If the host check confirms the configured identity, treat the sandbox result as an access limit.
Use that approved host context for authorized GitHub commands when available. Before a write, make sure that `gh api user` returns the configured login.
If the host check cannot confirm the configured identity, report both results and follow the access-failure rule above.
Do not copy tokens between stores or change credentials only because a sandbox check fails.
