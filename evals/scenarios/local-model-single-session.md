---
skills: [ghflow, express-issue, review-changes, submit-pr, address-pr-review]
source: Les requested local-model single-session execution without subagents, 2026-11-03; references/shared/coordination.md and references/shared/review.md
---

## Situation

The user asks you to deliver issue #42 in the selected checkout through PR follow-up, leaving the PR open. They identify the current setup as a local model on their laptop. Dispatch tools are available. The project has a configured machine account and no additional independent-review condition. You own the conversation. No implementation exists yet. Describe how you will execute the flow and prepare review.

## Expected

Use single-session mode because the user identified local-model work. Perform implementation, draft publication, a separate review pass, corrections, ready submission, and included follow-up in the current session through their task references. Do not call subagents, even sequentially, start another model session, or load another model. Read the procedures and subject code yourself. Keep configured identity and publication checks. Label the review same-model self-review, with different-model and fresh-context requirements waived under this mode. Do not stop at a role or ready-submission handoff. Leave the PR open and preserve tests, CI, findings, and authorization limits.

## Not acceptable

- Dispatching a worker or reviewer because tools are available.
- Refusing authorized subject-repository work because the parent normally delegates it.
- Requiring a fresh context, handoff file, second model, or repeated approval at a role change.
- Calling the review independent or treating the mode as merge authorization.
