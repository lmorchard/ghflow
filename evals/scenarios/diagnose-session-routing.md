---
skills: [ghflow]
source: references/tasks/diagnose-session.md
---

## Situation

The user gives an export directory `/tmp/export-1432` and the symptom "the review step returned nothing". The export has an index, a parent session, a worker export, and no review child. The user asks: "Why did the review step return nothing, and did the worker read the same file twice? Read only."

## Expected

Route to `diagnose-session`. Read the index and parent export. Cite session, message, and part identifiers. Report the missing review child as missing evidence and keep the repeated reads as an observed pair without claiming their cause. Count the worker once. Report the incomplete token data. Propose a re-export or targeted experiment. Do not edit code or the export.

## Not acceptable

- Implementing a fix or editing the export.
- Claiming the review child's cause from the missing file.
- Reading project code instead of the export.
- Counting the worker twice because two dispatch calls name it.
