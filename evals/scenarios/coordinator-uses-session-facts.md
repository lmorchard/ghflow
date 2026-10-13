---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-13-unattended-burndown.md timeline; 2026-10-13 decision to supply session facts from the CLI
---

## Situation

You coordinate an unattended burndown of three Ready issues in OpenCode, through PR review follow-up, without merge, with the user's approved same-model exception. The board traversal is valid. You just ran `facts` from the subject checkout. Its output includes `project_facts` with no stale sources; `base_ci` with `summary: green` on the default branch head; `runtime` with `agent: opencode`, `nested_dispatch: false`, `config_default_model: ollama/qwen3-coder:30b`, and an empty `agent_models`; and `skill_source` with `head: 1dca824`, `up_to_date: true`. Before the first dispatch, you plan to run `gh run list` on the default branch, read `~/.config/opencode/opencode.jsonc` and the project's `opencode.json`, and run `git log` in the skill checkout.

## Expected

Skip all three commands, because the `facts` output already answers each question. Base CI is green, so the red-base halt does not apply. Nested dispatch is false, so coordinate each issue under express-issue yourself instead of dispatching an express-issue subagent. Use `1dca824` as the source revision in each handoff. Do not treat the configured default model as the workers' model, because the session may run another model. Under the same-model exception, record each worker's model from its dispatch result. Dispatch the first implementation worker.

## Not acceptable

- Running any of the three planned commands.
- Treating `ollama/qwen3-coder:30b` as the model the workers will run.
- Dispatching an express-issue subagent when nested dispatch is false.
- Omitting the source revision from the handoff.
