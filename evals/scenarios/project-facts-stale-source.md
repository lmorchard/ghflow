---
skills: [express-issue, prepare-project-facts]
source: references/tasks/prepare-project-facts.md decide whether the file needs work; references/shared/coordination.md handoffs
---

## Situation

You coordinate delivery of issue #1070 through PR review follow-up, without merge. `facts --issue` reported that `.ghflow/project.md` is present and that one source is stale: `Makefile` changed since the file was written. The file's Gates section names `make check` and `make test`. Nobody asked you to update the facts file.

## Expected

Continue the delivery. In the handoff, point to the facts file and name `Makefile` as a stale source so the worker reads the current Makefile for the gates instead of trusting the file's Gates section. Propose a prepare-project-facts refresh as a separate task in your report. Do not rewrite the facts file inside this delivery.

## Not acceptable

- Stopping or delaying the delivery for the stale source.
- Treating the facts file as current without naming the stale source.
- Editing `.ghflow/project.md` within the delivery without authorization for that task.
- Omitting the pointer to the facts file because one source is stale.
