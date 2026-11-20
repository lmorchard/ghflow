---
skills: [review-changes]
source: references/tasks/review-changes.md review a correction
---

## Situation

You review a correction. The earlier review at commit A found two blocking findings. Finding 1: the fallback order returns the wrong default. Finding 2: the empty-input test is missing. The correction head is B. The handoff supplies the original base, A, B, the two findings, and the original scope and limits.

## Expected

Give one supported outcome for each finding. Cite the correction change and its evidence for finding 1. Cite the current lines and impact if finding 2 is still present, or name the missing evidence if it is unverified. State that this is a correction review and that it does not cover the whole branch.

## Not acceptable

- One blanket statement that both findings are fixed.
- Dropping the unchanged finding.
- Claiming a complete branch review from the correction diff.
