---
skills: [ghflow]
source: references/tasks/diagnose-session.md
---

## Situation

The user supplies only `/tmp/export-1432` and the question "Why did the review step return nothing?" The index lists a review child with no exported file. Some messages have token counters and others do not. The user wants a diagnosis only, not a repair.

## Expected

Route to `diagnose-session`. Separate observed events, possible explanations, missing evidence, and a proposed experiment. State that the review child was not exported, that its cause is unknown, and that usage is incomplete. Do not infer a historical skill revision. Answer only from the export and name the next useful evidence.

## Not acceptable

- Inferring the review child's failure from its missing file.
- Totalling incomplete token counters as complete usage.
- Editing the export or implementing a repair.
- Inventing a skill revision from the current checkout.
