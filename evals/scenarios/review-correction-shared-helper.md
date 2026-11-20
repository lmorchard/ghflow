---
skills: [review-changes]
source: references/tasks/review-changes.md review a correction
---

## Situation

The earlier review found that `parse_limit` accepted a bad unit. The correction changes `parse_limit` in a shared helper. One caller outside the correction diff passes a string that now raises. The previous review covered the helper and its callers.

## Expected

Trace the callers of the changed helper. Report finding 1 as addressed if the evidence supports it. Report the caller defect as a correction-introduced finding with file and lines, trigger, impact, and correction. Do not call the review clean.

## Not acceptable

- Reviewing only the correction diff.
- Assuming the unchanged callers keep their behavior.
- Marking the correction clean.
