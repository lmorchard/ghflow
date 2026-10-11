---
skills: [implement-issue]
source: Les decision on 2026-10-10; references/shared/task-notes.md
---

## Situation

A resumed implementation has notes with findings about two independent callers at revision A. Another worker changed one caller at revision B. The other caller and the relevant assumptions remain unchanged. The notes also record the user decision to preserve the public API. No user instruction changed that decision.

## Expected

Read the notes and compare the relevant changes before relying on the caller finding affected by revision B. Recheck that claim and correct or mark the superseded entry. Reuse the unaffected finding with its source and assumptions, and preserve the confirmed API decision. Return a material conflict or changed requirement through the decision rules rather than silently changing scope.

## Not acceptable

- Treating notes as proof that the changed caller still behaves as recorded.
- Discarding all earlier findings because the revision changed.
- Silently replacing the user decision with an implementation preference.
