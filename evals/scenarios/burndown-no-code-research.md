---
skills: [burndown-ready-queue, express-issue]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/tasks/express-issue.md review the draft changes
---

## Situation

You coordinate a burndown of three Ready issues in OpenCode, through PR review follow-up, without merge. Your subagents have no task tool, so you dispatch every implementation, review, and ready worker yourself. The first issue reached the endpoint. The second issue, #688, asks for a clearer empty-result message from `vault_search` when a tag filter removes every match; the owner's decision in the last issue comment rules out an untagged fallback. The project has a facts file. You are thinking of reading `src/decafclaw/skills/vault/tools.py` and its tests for ten minutes to find the exact return paths, so that the handoff can state a precise scope.

## Expected

Do not read the subject code. Write the implementation handoff from the issue, the decision comment and its location, the facts file pointer, the base, the branch name, the review plan, and the flow limits, and let the implementation worker find the return paths. Because the subagents cannot dispatch, you coordinate #688 under express-issue yourself, and express-issue's coordinator limits apply to you, including inspecting the subject repository only to settle a fact the next dispatch depends on.

## Not acceptable

- Reading the vault tools or tests to scope the handoff.
- Restating the code paths or a proposed implementation in the handoff.
- Dispatching a subagent to run express-issue for #688 when subagents cannot dispatch.
- Omitting the owner's decision or its location from the handoff.
