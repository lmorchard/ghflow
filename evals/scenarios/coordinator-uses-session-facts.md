---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md timeline; 2026-10-13 decision to supply session facts from the CLI
---

## Situation

You coordinate an unattended burndown of three Ready issues in OpenCode, through PR review follow-up, without merge, with the user's approved same-model exception. The board traversal is valid. You just ran `facts` from the subject checkout. Its output includes `project_facts` with no stale sources; `base_ci` with `summary: green` on the default branch head; `runtime` with `agent: opencode`, `nested_dispatch: false`, and an empty `agent_models`; and `skill_source` with `head: 1dca824`, `up_to_date: true`. Before the first dispatch, you plan to run `gh run list` on the default branch, read `~/.config/opencode/opencode.jsonc` and the project's `opencode.json`, and run `git log` in the skill checkout.

## Expected

Skip all three commands, because the `facts` output already answers each question. Base CI is green, so the red-base halt does not apply. Nested dispatch is false, so coordinate each issue under express-issue yourself instead of dispatching an express-issue subagent. Use `1dca824` as the source revision in each handoff. Under the same-model exception, ask each worker for the model ID its runtime states to it and record that as a self-report. Dispatch the first implementation worker.

## Not acceptable

- Running any of the three planned commands.
- Reading configuration to predict the workers' model.
- Dispatching an express-issue subagent when nested dispatch is false.
- Omitting the source revision from the handoff.
