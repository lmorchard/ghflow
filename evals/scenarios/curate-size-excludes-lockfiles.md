---
skills: [curate-ready-queue]
source: docs/research/trials/2026-10-15-unattended-burndown-3.md; references/tasks/curate-ready-queue.md unattended fit
---

## Situation

You curate the Ready column for tonight's unattended burndown, two or three issues. One P1 candidate pins direct npm dependencies exactly in two `package.json` files and adds a policy check script, a docs page, and tests. You estimate about 150 lines of hand-written change. Pinning will regenerate both `package-lock.json` files. The other P1 candidates are a 60-line test guard and a 30-line config test, both settled and gate-verified.

## Expected

Estimate the npm candidate at about 150 lines of hand-written change and note beside it that it regenerates two lockfiles, which makes it likely to run long. Order it last. Propose a Size for each pick, smaller for the two test issues, so that the burndown runs them first. Wait for the user's approval before any board change.

## Not acceptable

- Treating the npm candidate as a typical 150-line change without the lockfile note.
- Adding the lockfile lines into the size estimate as hand-written work.
- Ordering the npm candidate first.
- Omitting proposed Size values.
