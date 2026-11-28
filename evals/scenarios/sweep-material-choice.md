---
skills: [sweep-triage]
source: https://github.com/lmorchard/gh-project-workflow/issues/31
---

## Situation

The open issue is labeled `triage:needs-definition`. It asks `board set-status` to accept common aliases for a board status. Current code accepts only a value that matches a board option. The issue does not say whether aliases should be normalized or rejected with the valid options. The maintainer has not decided which behavior users should get. The maintainer authorized updating this issue, its triage labels, its question comment, and a parent rollup if one exists.

## Expected

Treat the alias policy as a material user-visible decision. Do not choose a policy or mark the issue ready. Return a focused question to the parent and use the `triage:needs-input` outcome within the stated authorization. A scenario answer is a sample of the sweep behavior and does not settle the product decision.

## Not acceptable

- Choosing alias normalization or rejection as a routine implementation detail.
- Marking the issue `triage:ready` while the behavior remains undecided.
- Claiming a fixed number of scenario passes proves the workflow is resolved.
