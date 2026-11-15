---
ghflow_project_facts: 1
written: 2026-11-15
sources:
  - AGENTS.md a888d729eac1b24607b942a2c784d1b1a91a9f58
  - Makefile 90e5a29d6a7d19ec7d016cfab95b2afd8ee32be7
  - .github/workflows/ci.yml 77fb7ad896922530cfca8dcf36e81d38a2da55ce
---
# Project facts

- **Worktree setup**: create worktrees under `.claude/worktrees/<branch>` inside the checkout root; standard Python 3 standard library environment with no extra dependencies to install.
- **Gates**: `make check` is the full gate; runs `python3 -m unittest discover -s cli`, `python3 -m unittest discover -s scripts`, `python3 scripts/check.py`, `python3 scripts/scenario_index.py --check`, and whitespace diff check against the empty tree.
- **Tests**: `make test` runs `python3 -m unittest discover -s cli` and `python3 -m unittest discover -s scripts`. Run a single test with `python3 -m unittest discover -s cli -k TEST_NAME`.
- **Session notes**: task workers write notes under `docs/dev-sessions/{timestamp}-{slug}/notes.md` inside their worktree; queue and delivery coordinators write notes under `~/.local/state/ghflow/notes/{timestamp}-{slug}/notes.md`.
- **Commits and PRs**: commit author/committer must match configured identity (`MokaGnome`); use Conventional Commits style (e.g. `fix: ...`, `feat: ...`, `docs: ...`).
- **Board**: GitHub project board owner `lmorchard`, project number `12`, columns `Backlog`, `Ready`, `In progress`, `In review`, `Done`.

Live state is not stored here; run `python3 cli/ghflow.py facts --issue ISSUE_URL` on demand.
