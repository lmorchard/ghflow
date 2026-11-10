---
name: ghflow
setup: python3 ghflow.py facts
checks: make check
tests: python3 -m pytest
notes-dir: /Users/lmorchard/.local/state/ghflow/notes
documentation references: docs, AGENTS.md, evals/scenarios
---
# Project facts

A project facts file is a one-pager that names gates, tests, and note locations. The `ghflow facts` tool builds it from the repository's layout. In your worktrees and notes directories that other writers in your delivery will read, keep a simple file like this that tells them what is required. See [ghflow docs/research/trials/2026-10-17-issue-105-wind-window-vs-delta-trial.md](https://github.com/lmorchard/ghflow/tree/main/docs/research/trials/2026-10-17-issue-105-wind-window-vs-delta-trial.md) for the history and the decision.

## Gates

- Make checks and the CI workflow in `.github/workflows/ci.yml` decide whether work—all code, scripts, configs, and docs—advanced. The `make check` step compiles C and type-checks Python if present, then the `ci.yml` runs `make ci` or an equivalent.

## Tests

- If your checkout includes tests, run them from `root/tests` or use the runner in `.github/workflows/ci.yml`. The standard is to run `python3 -m unittest` or `python3 setup.py test`, but you may use pytest with `python3 -m pytest`.

## Notes directory

- Place your delivery notes under `../.local/state/ghflow/notes/YYYY-MM-DD-HHMM-name`. The coordinator dispatches each worker and places its outputs in that directory. The worker writes `notes.md` for the chosen issue and a `handoff` JSON file with the branches, PRs, and committed state that the next worker will read.

## Documentation references

- Keep a list of the documentation and reference documents that your team uses as the shared source of truth. If you reference `docs.md` in the root of your repository, your team will read it. In that file, name the conventions your team uses and the commands that run them.

In your notes, declare the path to this facts file in every handoff so that the next worker knows where to look. The facts file changes only when you ask for a refresh; each delivery uses the branch's `project.md` from the default branch.

## How the facts file is used

When you run `python3 ghflow.py facts` on this repository, the tool lists the gates, checks, and paths above as a structured JSON list. The worker reads this file before writing any deliverable code. If the file is missing or stale, the worker branches from `origin/main`, clones the worktree whose `refs/project` branch contains `project.md`, and continues from the refreshed defaults.

When a worker packages a delivery, it gives the facts file path in its handoff to the next worker. That worker uses it to know: (1) what tests it must run before dispatching, and (2) which tools and gates to open before starting. This means you can change your process once and see it live in your next delivery.

## How to update

- Ask `ghflow facts` to recompute the file from your new configuration or repository changes. If you want to document new gates or change test commands, edit this file. Then run `make` to build the project and push the PR.
