# Diagnose an exported OpenCode session

Answer one question about an exported session tree from observed events. This task is read-only. Do not change the export, code, or GitHub records.

## Inputs

Require the export directory or session identifier, the reported symptom, and the question to answer. Accept a clear question without another interview. Ask only when missing scope prevents a useful investigation.

If the user supplies a session identifier, reuse `scripts/export-opencode-sessions.py` to create the tree. Treat the exported files as immutable evidence.

## Measure first

Read `index.md` and the parent export. Record file sizes and event counts before reading tool bodies. Follow child session identifiers from dispatch parts. Report a missing child as missing evidence.

## Examine

Start with the parent and the events around the symptom. Read targeted fields and events instead of dumping large tool bodies. Cite the session, message, and part identifiers when present, or a precise JSON path.

Count a reused worker session once in the inventory. Calculate durations from recorded timestamps. Keep overlapping child durations separate from elapsed session time. State which token counters are present. Do not sum incomplete counts as a total or infer prices.

## Report

Separate these sections:

- Observed events.
- Possible explanations.
- Missing evidence.
- A proposed discriminating experiment.

Record each cited file and its hash. Do not infer a historical skill revision from the current checkout. State when the export does not record it.

If the question cannot be answered from the export, say so and name the next useful evidence.
