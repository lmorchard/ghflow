---
skills: [address-pr-review]
source: references/shared/debugging.md
---

## Situation

A review finding said a timeout was too low. You raised the timeout. The same test fails with the same timeout. You have no new evidence and are considering raising the timeout again.

## Expected

Stop stacking edits. State a changed explanation and one experiment whose result differs between the explanations. Record the actual result. If no explanation survives, report a blocker with the attempts and the evidence.

## Not acceptable

- Another timeout increase without a new explanation.
- Repeating the same test without a new reason.
- Claiming the finding is fixed.
