# Debugging scenarios, 2026-11-20

Eleven Sonnet samples: three baseline, three change, three second change, and two regression scenarios. All grade Pass. The baseline also passes every new scenario, so the samples do not isolate the new debugging reference. The implementing agent graded; this is not independent. A local-model sample is blocked by the LM Studio endpoint authentication.

## Source and method

- Scenarios: [missing generated file](../scenarios/debug-missing-generated-file.md), [repeated correction failure](../scenarios/debug-repeated-correction-failure.md), [serial and parallel suite](../scenarios/debug-serial-parallel-suite.md). Regressions: [baseline-environment-bound](../scenarios/baseline-environment-bound.md), [one full suite at a time](../scenarios/one-full-suite-at-a-time.md).
- Baseline: skill text at `c7ed38cfea2493b8276c62c006a4b2afd3293933`. Commit `05daf77e56df94a73ccd2df98c62701abd08050f` adds only the new scenario files to that skill text. It is published on the `scenario-baseline-c` branch at origin.
- First change: `a5853027ec7a91aabd36d36d32912e70c937a62f`. Second change and regressions: `6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c`.
- Runner: `claude` 2.1.329 (Claude Code). Requested model `sonnet`; the runner reported no model ID (`runner_model: null`). The actual model identity is unresolved beyond the alias.
- Author model: `otari-mozilla/deepseek-v4.1-flash-1017`.
- Grader: the implementing agent, in the same session. It authored the change, so this is not an independent grade.
- Isolation: the runner supplied only the committed skill snapshot and restricted the tools to Read, Glob, and Grep. It did not allow commands, edits, network tools, or agents.
- Raw answers: [answers](2026-11-20-debugging-answers.txt).
- Provenance logs were in `/tmp/scenario-c` and `/tmp/scenario-c2`, which are not durable. The answers, session IDs, source commits, and the published baseline branch are the durable record.

## Results

| Scenario | Phase | Runner | Model | Session ID | Grade |
| --- | --- | --- | --- | --- | --- |
| debug-missing-generated-file | baseline text | claude | sonnet | 7390f6a4-cb8c-45b3-9f37-09b361993f73 | Pass |
| debug-missing-generated-file | change text | claude | sonnet | 36077f5b-923e-4dee-aa27-5ade9db189f9 | Pass |
| debug-missing-generated-file | second change | claude | sonnet | 13095ac5-7e0f-494d-a1e6-14988479dc1b | Pass |
| debug-repeated-correction-failure | baseline text | claude | sonnet | 336de0c6-87e7-4f0d-b4d6-ef72a4b8c8f3 | Pass |
| debug-repeated-correction-failure | change text | claude | sonnet | 32073a49-d2b1-4927-8de9-f5cae8c730d5 | Pass |
| debug-repeated-correction-failure | second change | claude | sonnet | 0feefd81-ed9e-4af0-9a6e-ecb7260456d2 | Pass |
| debug-serial-parallel-suite | baseline text | claude | sonnet | 63db054c-1c43-4226-95c1-f3c5c3727d65 | Pass |
| debug-serial-parallel-suite | change text | claude | sonnet | c57cd51a-712c-489e-b9ad-532284b6bdc6 | Pass |
| debug-serial-parallel-suite | second change | claude | sonnet | 38adeff8-2b5c-47f7-b893-5c11407c20e4 | Pass |
| baseline-environment-bound | regression | claude | sonnet | 1e35847b-98d1-4334-a527-1dc1c061b92b | Pass |
| one-full-suite-at-a-time | regression | claude | sonnet | 6afe126f-1b3b-494c-9d4b-da0b4dd739f9 | Pass |

The change answers cite [Debugging](../../references/shared/debugging.md) and state a hypothesis, one discriminating experiment, and the result. The baseline answers reach the same decisions through the existing investigation limits, the CI-log rule, and the bounded-baseline rule. The regression answers keep the environment-limit and single-suite decisions.

## Limits

- The baseline passes all three scenarios. The scenarios do not show that the new reference changes the decision for Sonnet. They show the shared method is explicit and that the change does not regress the decisions.
- Two change samples per scenario. The result does not show stability beyond that.
- The author graded the samples, so the grades are not independent.
- The runner reported no model ID. The requested alias is `sonnet`, not a resolved model.
- No local-model sample. The LM Studio endpoint returns 401 for the model inventory, and the scenario runner refuses credentials and requires exactly one advertised model.

## Checks

`make check` passes for the repository, including the whitespace check after the trailing blank lines were removed.

```scenario-results
[
  {"scenario": "debug-missing-generated-file", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-missing-generated-file", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-missing-generated-file", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "debug-repeated-correction-failure", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-repeated-correction-failure", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-repeated-correction-failure", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "debug-serial-parallel-suite", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-serial-parallel-suite", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "debug-serial-parallel-suite", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "baseline-environment-bound", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "regression", "note": "Regression sample; author-graded.", "order": null},
  {"scenario": "one-full-suite-at-a-time", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "regression", "note": "Regression sample; author-graded.", "order": null}
]
```
