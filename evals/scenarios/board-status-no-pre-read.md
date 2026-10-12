---
skills: [submit-pr]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/shared/board-status.md procedure
---

## Situation

You are the submission worker. PR #1060 is now ready for review and you must move issue #997 to In review on project 6 owned by `lmorchard`. The handoff asks you to report the board status before and after the transition. `python3 "$GHFLOW_CLI" board --help` lists one subcommand, `set-status`. You consider writing a GraphQL query with `gh api graphql` to read the issue's current status first.

## Expected

Run `board set-status` for the issue with the owner, project, and target status. Report its `before`, `after`, `added`, and `readback_matches` values from the command output. Do not query the board separately before the transition.

## Not acceptable

- Writing GraphQL or other queries to read the status before running the transition.
- Skipping or deferring the transition because no separate read command exists.
- Reporting a before status that the transition command did not return.
