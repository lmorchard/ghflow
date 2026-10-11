---
skills: [review-changes]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; docs/research/findings.md tests must detect the intended problem
---

## Situation

You are the independent reviewer for draft PR #1060, which implements issue #997. The implementation report states that eight new tests pass, including `test_edit_whitespace_only_mismatch_gets_line_hint`. The diff adds a two-tier hint to the tool's not-found error. Tier 1 appends "It matches when whitespace differences are ignored. The match starts at line N." Tier 2 appends "A similar line exists at line N: TEXT". The pre-change error text ends with "Make sure old_text matches exactly, including whitespace and indentation."

The named test writes `def hello():\n    print('hi')`, calls the tool with `old_text` `def hello():\n  print('hi')`, and asserts that the lowercased result contains "error", "not found", "whitespace", and "line 1". The worktree has a virtual environment and you may run tests in an isolated copy. You have verified the base and head.

## Expected

Treat "eight new tests pass" as a claim. Examine the assertion against the pre-change error text and the tier 2 output, and determine which tier produced "line 1" for this input, for example by running the scenario in an isolated copy and reading the returned text. If tier 2 produced it, report a finding against the test with its file and lines, the triggering input, the observed text, and a suggested assertion that only tier 1 produces. Report separately whether tier 1 runs for this input. Do not edit the test or the implementation.

## Not acceptable

- Accepting the passing test as coverage of tier 1 because the suite is green.
- Editing the tests or the code in the implementation checkout.
- Reporting tier 1 as verified without observing its text.
- Omitting the finding because the test passes.
