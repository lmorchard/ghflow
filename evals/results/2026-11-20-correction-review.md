# Correction review scenarios, 2026-11-20

Seventeen Sonnet samples: five baseline, five change, five second change, and two regression scenarios. All grade Pass. The baseline also passes every new scenario, so the samples do not isolate the new correction section. The implementing agent graded; this is not independent. A local-model sample is blocked by the LM Studio endpoint authentication.

## Source and method

- Scenarios: [two findings](../scenarios/review-correction-two-findings.md), [shared helper](../scenarios/review-correction-shared-helper.md), [missing evidence](../scenarios/review-correction-missing-evidence.md), [head change](../scenarios/review-correction-head-change.md), [scope claim](../scenarios/review-correction-scope-claim.md). Regressions: [reviewer-recorded-models](../scenarios/reviewer-recorded-models.md), [review-note-not-finding](../scenarios/review-note-not-finding.md).
- Baseline: skill text at `c7ed38cfea2493b8276c62c006a4b2afd3293933`. Commit `05daf77e56df94a73ccd2df98c62701abd08050f` adds only the new scenario files to that skill text. It is published on the `scenario-baseline-c` branch at origin.
- First change: `a5853027ec7a91aabd36d36d32912e70c937a62f`. Second change and regressions: `6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c`, which adds the remaining-uncertainty and broader-review wording.
- Runner: `claude` 2.1.329 (Claude Code). Requested model `sonnet`; the runner reported no model ID (`runner_model: null`). The actual model identity is unresolved beyond the alias.
- Author model: `otari-mozilla/deepseek-v4.1-flash-1017`.
- Grader: the implementing agent, in the same session. It authored the change, so this is not an independent grade.
- Isolation: the runner supplied only the committed skill snapshot and restricted the tools to Read, Glob, and Grep. It did not allow commands, edits, network tools, or agents.
- Raw answers: [answers](2026-11-20-correction-review-answers.txt).
- Provenance logs were in `/tmp/scenario-c` and `/tmp/scenario-c2`, which are not durable. The answers, session IDs, source commits, and the published baseline branch are the durable record.

## Results

| Scenario | Phase | Runner | Model | Session ID | Grade |
| --- | --- | --- | --- | --- | --- |
| review-correction-two-findings | baseline text | claude | sonnet | 459b626c-c87c-4c1a-8fd4-ee472e3d3b27 | Pass |
| review-correction-two-findings | change text | claude | sonnet | 380d9cb5-51ec-43a6-a040-6fb205497d9c | Pass |
| review-correction-two-findings | second change | claude | sonnet | d32f0d5f-dfd7-44ec-8657-97b177154bb2 | Pass |
| review-correction-shared-helper | baseline text | claude | sonnet | 5b360358-0cdd-4370-944c-b9a553db2642 | Pass |
| review-correction-shared-helper | change text | claude | sonnet | 68ab2850-adb1-417d-a509-f674b9b7ad05 | Pass |
| review-correction-shared-helper | second change | claude | sonnet | fc7561e2-b63e-454e-83ee-d46dfee78c8f | Pass |
| review-correction-missing-evidence | baseline text | claude | sonnet | d18c61f3-7923-4495-a333-695ffe45d7ef | Pass |
| review-correction-missing-evidence | change text | claude | sonnet | ba111266-e922-414b-bbca-f196194351ba | Pass |
| review-correction-missing-evidence | second change | claude | sonnet | 13645af1-3c9d-4255-9964-c4089a40d212 | Pass |
| review-correction-head-change | baseline text | claude | sonnet | f88380ad-ba97-490a-af3d-d8ab0134d9f9 | Pass |
| review-correction-head-change | change text | claude | sonnet | 85ed4173-519e-4d17-a223-096f7639d896 | Pass |
| review-correction-head-change | second change | claude | sonnet | 53d3e1d5-d503-463b-8fcc-b507b43fe7c3 | Pass |
| review-correction-scope-claim | baseline text | claude | sonnet | fa4c5bd8-d10c-44e4-bfb7-d0f64223b243 | Pass |
| review-correction-scope-claim | change text | claude | sonnet | a2b6d117-f833-4fa3-bd97-556cf3f1e0a1 | Pass |
| review-correction-scope-claim | second change | claude | sonnet | 9c16dc53-dba1-46a2-bc48-b5b075f7cf54 | Pass |
| reviewer-recorded-models | regression | claude | sonnet | 4f8da5a7-8516-46e0-b5b1-b6b5a3930130 | Pass |
| review-note-not-finding | regression | claude | sonnet | 71b8efd4-58cc-4f82-ab07-d9acc7da9339 | Pass |

Both change samples give per-finding outcomes, trace affected callers, state the correction's coverage limit, and name the remaining uncertainty. The regression samples keep the model-identity and note-versus-finding decisions. The baseline reaches the correction decisions through "Examine the change", `shared/evidence.md`, and the express-issue dispatch.

## Limits

- The baseline passes all five new scenarios. The scenarios do not show that the new section changes the decision for Sonnet. They show that the section states the contract explicitly and that the change does not regress the decisions.
- Two change samples per scenario. The result does not show stability beyond that.
- The author graded the samples, so the grades are not independent.
- The runner reported no model ID. The requested alias is `sonnet`, not a resolved model.
- No local-model sample. The LM Studio endpoint returns 401 for the model inventory, and the scenario runner refuses credentials and requires exactly one advertised model.

## Checks

`make check` passes for the repository, including the whitespace check after the trailing blank lines were removed.

```scenario-results
[
  {"scenario": "review-correction-two-findings", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-two-findings", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-two-findings", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "review-correction-shared-helper", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-shared-helper", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-shared-helper", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "review-correction-missing-evidence", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-missing-evidence", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-missing-evidence", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "review-correction-head-change", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-head-change", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-head-change", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "review-correction-scope-claim", "date": "2026-11-20", "skill_commit": "05daf77e56df94a73ccd2df98c62701abd08050f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "baseline text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-scope-claim", "date": "2026-11-20", "skill_commit": "a5853027ec7a91aabd36d36d32912e70c937a62f", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "One sample; author-graded; baseline also passes.", "order": null},
  {"scenario": "review-correction-scope-claim", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "reviewer-recorded-models", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "regression", "note": "Regression sample; author-graded.", "order": null},
  {"scenario": "review-note-not-finding", "date": "2026-11-20", "skill_commit": "6d2b3c9ee4bb700f4bbceba01b48adecd2d23a6c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "regression", "note": "Regression sample; author-graded.", "order": null}
]
```
