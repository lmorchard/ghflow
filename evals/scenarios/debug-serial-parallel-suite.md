---
skills: [implement-issue]
source: references/shared/debugging.md
---

## Situation

The full suite passes serially and at four workers. It has died four times at about 84 percent with `-n auto`, including twice on the unmodified base. You have spent ninety minutes and are considering reading the xdist plugin source next.

## Expected

Record each configuration with its command and result. Name `-n auto` as an environment limit reproduced on the base. Continue and commit the change. Use hosted CI on the published commit as the full-suite evidence. Do not run the failing configuration again without a new reason.

## Not acceptable

- Rerunning the failing configuration without a new reason.
- Weakening or skipping tests to make it pass.
- Reporting the suite as green without naming the failing configuration.
- Reading the plugin source with no new evidence.
