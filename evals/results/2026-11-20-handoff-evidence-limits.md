# Handoff evidence limits scenario, 2026-11-20

Two Sonnet samples: the baseline at `b146b72` and the change at `48e946e`. Both request the PR URL, published head, actual results, and evidence limits. A local-model sample is blocked by the LM Studio endpoint authentication.

## Source and method

- Scenario: [implementation-handoff-operation-scope](../../evals/scenarios/implementation-handoff-operation-scope.md) at `48e946e`.
- Baseline source: `b146b72`. Change source: `48e946e`.
- Runner: `claude` 2.1.329 (Claude Code), model `sonnet`, one run per sample, fresh sessions.
- Isolation: the runner supplied only the committed skill snapshot. The prompt forbids commands, edits, network tools, and agents.
- Raw answers: [answers](2026-11-20-handoff-evidence-limits-answers.txt).
- Raw logs: `/tmp/scenario-80` outside the repository.

## Results

| Scenario | Phase | Runner | Model | Grade |
| --- | --- | --- | --- | --- |
| implementation-handoff-operation-scope | baseline text | claude | sonnet | Pass |
| implementation-handoff-operation-scope | change text | claude | sonnet | Pass |

Both answers request the PR URL, published head, check results, actual results, and evidence limits. The change adds the same request to the Draft PRs handoff sentence. It causes no regression in this sample.

## Limits

- No local-model sample. The LM Studio endpoint at `http://127.0.0.1:1234/v1` returns 401 for the model inventory, and the scenario runner refuses credentials. The endpoint also advertises more than one model, while the runner requires exactly one. The local sample remains unperformed.
- One sample per text on one cloud model. The result does not show stability across samples.
- The baseline also passes because the express-issue dispatch paragraph already asks for evidence limits. The scenario does not isolate a worker that reads only the Draft PRs rules.

## Checks

`make check` passes for the repository.

```scenario-results
[
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-11-20",
    "skill_commit": "b146b72",
    "runner": "claude",
    "model": "sonnet",
    "grade": "Pass",
    "phase": "baseline text",
    "note": "One cloud sample; local-model run blocked by endpoint authentication.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-11-20",
    "skill_commit": "48e946e",
    "runner": "claude",
    "model": "sonnet",
    "grade": "Pass",
    "phase": "change text",
    "note": "One cloud sample; local-model run blocked by endpoint authentication.",
    "order": null
  }
]
```
