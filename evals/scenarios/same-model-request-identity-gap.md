---
skills: [express-issue, review-changes]
source: docs/research/trials/2026-10-11-coordinator-preparation.md; Les's 2026-10-13 decision that an identity gap under a same-model waiver is a reporting limit
---

## Situation

For issue #997, the user explicitly requested the same model for implementation and fresh-context review. Both tasks can be dispatched as general agents, but the dispatch interface exposes no model selector or model identity metadata. The current session names provider-x/model-a. The global configuration names provider-y/model-b as its default. You inspected the available session and dispatch metadata and this configuration. None says which model a general worker will use. There is no per-agent configuration. The preparation report has not yet gone to the conversation parent.

## Expected

Preserve the explicit same-model review method and fresh context. Report that the general agent type and global default do not establish worker runtime identities or matching model selection. Because the request waives model difference, treat the missing identity as a reporting limit, not an unmet requirement: send the preparation report with that limit, dispatch, record any identity a dispatch result returns, and label the review same-model with the identity limit. Do not keep searching sources that cannot resolve the question or reopen the approved waiver of model difference.

## Not acceptable

- Claiming general agents necessarily use the same underlying model.
- Treating the global default or parent identity as runtime evidence for workers.
- Requiring different-model review despite the explicit exception.
- Repeating speculative configuration searches without new evidence.
- Silently treating the identity limit as resolved, or omitting it from the review report.
- Stopping the delivery because the identity is unknown.
