# Session diagnosis scenarios, 2026-11-20

Eight Sonnet samples: two scenarios against the baseline, the change, a second change, and a final change. The change, second change, and final change pass both scenarios. The baseline fails both because it does not route to `diagnose-session`; it still reaches a reasonable diagnosis through the shared evidence and debugging rules. The implementing agent graded. This is not independent. A local-model sample is blocked by the LM Studio endpoint authentication.

## Source and method

- Scenarios: [routing](../scenarios/diagnose-session-routing.md), [incomplete evidence](../scenarios/diagnose-session-incomplete-evidence.md).
- Baseline: `749123ba5a70f02f65a9f0d543848989331bfcee` with the two scenario files added in `284ce9154a0b634e76e70fee930f32a2ea4957e6` on the `scenario-base-d` branch at origin. The baseline `SKILL.md` has no diagnosis route or task.
- Change and second change: `bbe00d47ed19f75ad00890bfe21a004213c8b4c9`. Final change: `d8ecca6a0273f5bbdab91ef6bf63da35e8e9a44c`, which adds the missing parent/user, present-day, unique-context, and report-location rules.
- Runner: `claude` 2.1.329 (Claude Code). Requested model `sonnet`; the runner reported no model ID (`runner_model: null`). The actual model identity is unresolved beyond the alias.
- Author model: `otari-mozilla/deepseek-v4.1-flash-1017`.
- Grader: the implementing agent, in the same session. It authored the change, so this is not an independent grade.
- Isolation: the runner supplied only the committed skill snapshot and restricted the tools to Read, Glob, and Grep. It did not allow commands, edits, network tools, or agents.
- Raw answers: [answers](2026-11-20-session-diagnosis-answers.txt).
- Provenance logs were in `/tmp/scenario-d`, which is not durable. The answers, session IDs, source commits, and the published baseline branch are the durable record.
- The manual fixture trial and its report are in [docs/research/trials/2026-11-20-session-diagnosis](../../docs/research/trials/2026-11-20-session-diagnosis/report.md).

## Results

| Scenario | Phase | Runner | Model | Session ID | Grade |
| --- | --- | --- | --- | --- | --- |
| diagnose-session-routing | baseline text | claude | sonnet | 4d513590-cf56-4299-a192-46387e17f348 | Fail |
| diagnose-session-routing | change text | claude | sonnet | 1e14ac34-2749-41c5-ab2a-2990c4bfebf8 | Pass |
| diagnose-session-routing | second change | claude | sonnet | 18503f7e-b764-4b28-b5c6-47a350e6def4 | Pass |
| diagnose-session-routing | final change | claude | sonnet | 9b26edfb-8de4-44fc-a494-2e2f66f05a09 | Pass |
| diagnose-session-incomplete-evidence | baseline text | claude | sonnet | b2ecdc83-569c-4771-b26a-bb06ed4cecaa | Fail |
| diagnose-session-incomplete-evidence | change text | claude | sonnet | d90533db-3120-45fc-950f-6658fde5607c | Pass |
| diagnose-session-incomplete-evidence | second change | claude | sonnet | b3bae49f-093d-4969-8b87-30eb6415093b | Pass |
| diagnose-session-incomplete-evidence | final change | claude | sonnet | a09a8939-7804-4c39-b5b0-92bcc57ce9ef | Pass |

The baseline answers say the task table has no diagnosis operation and use the shared evidence and debugging rules instead. They do not route to `diagnose-session`, so they fail the scenario. The change answers name the route and follow "Measure first", missing-child, partial-token, and read-only rules. The final change answers also apply the parent/user, present-day, unique-context, and report-location rules.

## Limits

- The baseline fails the routing criterion but still produces a plausible diagnosis through other shared rules. The scenario detects the missing route, not a failure to diagnose at all.
- Three change samples per scenario. The result does not show stability beyond that.
- The author graded the samples, so the grades are not independent.
- The runner reported no model ID. The requested alias is `sonnet`, not a resolved model.
- No local-model sample. The LM Studio endpoint returns 401 for the model inventory, and the scenario runner refuses credentials and requires exactly one advertised model.
- The manual fixture trial was performed by the implementing agent and graded by the same agent. It has no fresh model session.

## Checks

`make check` passes for the repository.

```scenario-results
[
  {"scenario": "diagnose-session-routing", "date": "2026-11-20", "skill_commit": "284ce9154a0b634e76e70fee930f32a2ea4957e6", "runner": "claude", "model": "sonnet", "grade": "Fail", "phase": "baseline text", "note": "Baseline has no diagnosis route; author-graded.", "order": null},
  {"scenario": "diagnose-session-routing", "date": "2026-11-20", "skill_commit": "bbe00d47ed19f75ad00890bfe21a004213c8b4c9", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "Routes to diagnose-session; author-graded.", "order": null},
  {"scenario": "diagnose-session-routing", "date": "2026-11-20", "skill_commit": "bbe00d47ed19f75ad00890bfe21a004213c8b4c9", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "diagnose-session-routing", "date": "2026-11-20", "skill_commit": "d8ecca6a0273f5bbdab91ef6bf63da35e8e9a44c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "final change", "note": "Final change sample with the added rules; author-graded.", "order": null},
  {"scenario": "diagnose-session-incomplete-evidence", "date": "2026-11-20", "skill_commit": "284ce9154a0b634e76e70fee930f32a2ea4957e6", "runner": "claude", "model": "sonnet", "grade": "Fail", "phase": "baseline text", "note": "Baseline has no diagnosis route; author-graded.", "order": null},
  {"scenario": "diagnose-session-incomplete-evidence", "date": "2026-11-20", "skill_commit": "bbe00d47ed19f75ad00890bfe21a004213c8b4c9", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "change text", "note": "Routes to diagnose-session; author-graded.", "order": null},
  {"scenario": "diagnose-session-incomplete-evidence", "date": "2026-11-20", "skill_commit": "bbe00d47ed19f75ad00890bfe21a004213c8b4c9", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "second change", "note": "Second change sample; author-graded.", "order": null},
  {"scenario": "diagnose-session-incomplete-evidence", "date": "2026-11-20", "skill_commit": "d8ecca6a0273f5bbdab91ef6bf63da35e8e9a44c", "runner": "claude", "model": "sonnet", "grade": "Pass", "phase": "final change", "note": "Final change sample with the added rules; author-graded.", "order": null}
]
```
