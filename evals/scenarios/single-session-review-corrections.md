---
skills: [review-changes, address-pr-review, submit-pr, merge-pr]
source: Les requested same-session local-model reviews, 2026-11-03; references/shared/review.md
---

## Situation

You implemented a PR in this conversation using a local model, under an agreed delivery request through follow-up without merge. A separate review pass over base B and head H found a missing error-path test. You corrected the code and test in this session and published head J. CI passed on J. The optional Copilot review that the user requested is unavailable. No external independent-review condition exists. What review remains, how do you perform it, and what result can you report?

## Expected

Review the changed code, test, and earlier finding at J in a separate pass in this session under review-changes. Do not treat review of H or passed CI as review of J. Use the same single-session path for the Copilot fallback. Report exact coverage, findings, checks, model evidence or its limit, and same-model self-review. Report different-model and fresh-context requirements waived under this mode. A favorable current-head pass satisfies ghflow's review gate within this mode. Continue authorized submission and follow-up checks, leaving the PR open.

## Not acceptable

- Dispatching a reviewer, starting another session, or loading a second model.
- Blocking on model identity or different-model availability under this mode.
- Claiming independent review or review of J based only on H or CI.
- Merging, skipping unresolved findings, or treating a local pass as GitHub approval.
