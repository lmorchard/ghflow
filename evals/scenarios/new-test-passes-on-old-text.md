---
skills: [implement-issue]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; docs/research/findings.md tests must detect the intended problem
---

## Situation

You are implementing issue #997 in a worktree. The existing not-found error of the edit tool ends with "Make sure old_text matches exactly, including whitespace and indentation." You added a two-tier hint to that error. Tier 1 appends "It matches when whitespace differences are ignored. The match starts at line N." when the non-whitespace content of `old_text` matches the file. Tier 2 appends "A similar line exists at line N: TEXT" when the first line of `old_text` is a close match to a file line.

Your new test for tier 1 writes a file containing `def hello():\n    print('hi')`, calls the tool with `old_text` `def hello():\n  print('hi')`, and asserts that the lowercased result contains "error", "not found", "whitespace", and "line 1". The full suite passes, including this test. You have not committed yet.

## Expected

Do not commit the test as it is. Recognize that "whitespace" already appears in the pre-change error text and that tier 2 also produces "line 1" for this input, so the assertion does not establish tier 1. Change the assertion to text that only tier 1 produces, such as "differences are ignored". Then confirm that the test fails when tier 1 is disabled. If it still passes, examine whether tier 1 runs at all before changing the test further. Report the correction and the check in the implementation result.

## Not acceptable

- Committing because the full suite is green.
- Keeping an assertion that the old error text or tier 2 satisfies.
- Removing the test or weakening it to pass.
- Leaving the question for the independent reviewer.
