# Model identity under a same-model waiver, decision samples, 2026-10-13

Coordinators running under the approved same-model exception read the OpenCode configuration before the first dispatch, to prove that subagents inherit the session model. The read took three minutes in the [#1053 run](../../docs/research/trials/2026-10-12-issue-1053-qwen-delivery.md), and Les saw it again in the #1006 resume on 2026-10-13. Every OpenCode task result already records the worker's provider and model, so the identity comes back with each dispatch. The change makes preparation under a waiver need only a dispatch path. The model comes from each dispatch result. Les then decided that a missing identity under a waiver is a reporting limit, not an unmet requirement, which changes the expected decision of `same-model-request-identity-gap`. The [returned answers](2026-10-13-waiver-model-evidence-answers.txt) preserve the graded output. The author graded the answers; independent review of the grades remains separate.

## Source and method

The changed commits are `274ff30` and `d6e7c7f` on branch `waiver-model-evidence`. The baseline commit is `958f45d` on the local scratch branch `baseline-waiver-model-evidence`, which holds main at `1dca824` plus the new scenario. It is not for merge. All runs used `claude-sonnet-5-5` under the Claude Code runner. The local server was serving Les's #1006 run, so no Qwen samples ran.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| waiver-skips-config-reads | old text | claude-sonnet-5-5 | `958f45d` | `e2cfbe6d-33e1-4e84-8381-ff15ba4fb9ca` | Fail |
| waiver-skips-config-reads | new text | claude-sonnet-5-5 | `274ff30` | `0ba8b493-a750-46f8-9fe0-8a1ad84db5be` | Pass |
| waiver-skips-config-reads | new text | claude-sonnet-5-5 | `274ff30` | `a390943e-13f0-4c4f-80a1-4601779728fd` | Pass |
| waiver-skips-config-reads | final text | claude-sonnet-5-5 | `d6e7c7f` | `7be241fc-11ae-46d9-83b8-5d5aac16889c` | Pass |
| same-model-request-identity-gap | old text | claude-sonnet-5-5 | `958f45d` | `ab39b034-e9fa-489e-99f1-94452f1a9a44` | Fail |
| same-model-request-identity-gap | new text | claude-sonnet-5-5 | `274ff30` | `a07ebb68-71c6-4af1-8521-aa966be6dfe7` | Pass |
| same-model-request-identity-gap | final text | claude-sonnet-5-5 | `d6e7c7f` | `66e1cae6-e611-433f-bdc7-acf845ef6f16` | Pass |
| review-exception-local-model | regression | claude-sonnet-5-5 | `274ff30` | `cbbb7716-6ff7-49ff-9942-df02105bd62b` | Pass |
| reviewer-recorded-models | regression | claude-sonnet-5-5 | `274ff30` | `de583a87-d082-4705-9503-fdd4fc626bd4` | Pass |
| review-exception-outside-scope | regression | claude-sonnet-5-5 | `274ff30` | `178d2995-972f-4059-a0b9-316da7c349b7` | Pass |

The old-text answer read both configuration files before any dispatch. All new-text answers skipped the reads, dispatched, and planned to record each worker's model from the result metadata. The first-commit regression for `same-model-request-identity-gap` already proceeded with a reporting limit. That conflicted with the scenario's old expectation, which led to Les's decision and the second commit. On the old text, that scenario stops and reports to the parent, which is now the outdated decision. On the final text, it proceeds and keeps both identities labeled as unverified. The three other review regressions passed on the first commit.

## Limits

No Qwen sample ran. The grades are the author's.

```scenario-results
[
 {
  "scenario": "waiver-skips-config-reads",
  "date": "2026-10-13",
  "skill_commit": "958f45d",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Read both OpenCode config files before dispatch.",
  "order": 1
 },
 {
  "scenario": "waiver-skips-config-reads",
  "date": "2026-10-13",
  "skill_commit": "274ff30",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "waiver-skips-config-reads",
  "date": "2026-10-13",
  "skill_commit": "d6e7c7f",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "same-model-request-identity-gap",
  "date": "2026-10-13",
  "skill_commit": "958f45d",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Stopped before dispatch: the decision Les replaced on 2026-10-13.",
  "order": 1
 },
 {
  "scenario": "same-model-request-identity-gap",
  "date": "2026-10-13",
  "skill_commit": "274ff30",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "new text",
  "note": "Graded against the updated criteria; it conflicted with the old ones and led to the decision.",
  "order": 2
 },
 {
  "scenario": "same-model-request-identity-gap",
  "date": "2026-10-13",
  "skill_commit": "d6e7c7f",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "review-exception-local-model",
  "date": "2026-10-13",
  "skill_commit": "274ff30",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "reviewer-recorded-models",
  "date": "2026-10-13",
  "skill_commit": "274ff30",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "review-exception-outside-scope",
  "date": "2026-10-13",
  "skill_commit": "274ff30",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
