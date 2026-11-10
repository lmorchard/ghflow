# Coordinator-runtime model scenario, 2026-11-10

This sample checks the new `coordinator-runtime-model` scenario at `a0d2f9d`.
The coordinator runs `claude-sonnet-5-5`, and the worker's return names no model.

## Result

| Scenario | Phase | Runner | Model | Grade |
| --- | --- | --- | --- | --- |
| coordinator-runtime-model | new text | claude | claude-sonnet-5-5 | Pass (2/2) |

Both answers record the implementer model as unresolved, cite the dispatch record's agent type `task` with no override as the only source, and reject the coordinator's runtime model. Both state that the review requirement stays unmet and return the review choice to the parent.

## Limits

Both samples use one cloud model. The local-model sample is not run: the OpenCode endpoint at `http://127.0.0.1:9931/v1` did not answer, so no local run started. The scenario's own check is therefore one-model evidence.

```scenario-results
[
  {
    "scenario": "coordinator-runtime-model",
    "date": "2026-11-10",
    "skill_commit": "a0d2f9d",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "new text",
    "note": "Two cloud samples; local-model run not performed because the endpoint did not answer.",
    "order": null
  }
]
```
