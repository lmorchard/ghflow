# Handoff evidence limits scenario, 2026-11-20

Two Sonnet samples: the baseline and the change. Both request the PR URL, published head, actual results, and evidence limits. The implementing agent graded both. It wrote the change, so the grade is not independent. A local-model sample is blocked by the LM Studio endpoint authentication.

## Source and method

- Scenario: [implementation-handoff-operation-scope](../../evals/scenarios/implementation-handoff-operation-scope.md) at `48e946e1c0131dc7f8e69dba42d341ff3a5e4bc3`.
- Baseline source: `b146b7298f28b4319b82edbc0d4fa5c8e3a8e3df`. Change source: `48e946e1c0131dc7f8e69dba42d341ff3a5e4bc3`.
- Runner: `claude` 2.1.329 (Claude Code). Requested model `sonnet`; the runner reported `claude-sonnet-5-5`.
- Author model: `otari-mozilla/deepseek-v4.1-flash-1017`.
- Grader: the implementing agent, in the same session. It authored the change, so this is not an independent grade.
- Isolation: the runner supplied only the committed skill snapshot and restricted the tools to Read, Glob, and Grep. It did not allow commands, edits, network tools, or agents.
- Raw answers: [answers](2026-11-20-handoff-evidence-limits-answers.txt).
- Provenance logs were in `/tmp/scenario-80`, which is not durable. The source commits, session IDs, and runner-reported model are recorded here.

## Results

| Scenario | Phase | Runner | Model | Session ID | Grade |
| --- | --- | --- | --- | --- | --- |
| implementation-handoff-operation-scope | baseline text | claude | claude-sonnet-5-5 | e7a8d20d-159b-4d5f-945c-90c1d2550021 | Pass |
| implementation-handoff-operation-scope | change text | claude | claude-sonnet-5-5 | 41c0fd3f-c2b2-4abe-b2cb-370d7160860d | Pass |

Both answers request the PR URL, published head, check results, actual results, and evidence limits. The change adds the same request to the Draft PRs handoff sentence. The change answer says "check results" rather than "actual results"; the Pass grade holds.

## Limits

- No local-model sample. The LM Studio endpoint at `http://127.0.0.1:1234/v1` returns 401 for the model inventory, and the scenario runner refuses credentials. The runner also requires exactly one advertised model. The inventory was unreadable, so its model count is unknown. The local sample remains unperformed.
- One sample per text on one cloud model. The result does not show stability across samples, and the author graded it.
- The baseline also passes because the express-issue dispatch paragraph already asks for evidence limits. The scenario does not isolate a worker that reads only the Draft PRs rules. #80 still needs that scenario and the local sample.

## Checks

`make check` passes for the repository.

```scenario-results
[
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-11-20",
    "skill_commit": "b146b7298f28b4319b82edbc0d4fa5c8e3a8e3df",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline text",
    "note": "One cloud sample; author-graded; local-model run blocked by endpoint authentication.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-11-20",
    "skill_commit": "48e946e1c0131dc7f8e69dba42d341ff3a5e4bc3",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "change text",
    "note": "One cloud sample; author-graded; local-model run blocked by endpoint authentication.",
    "order": null
  }
]
```
