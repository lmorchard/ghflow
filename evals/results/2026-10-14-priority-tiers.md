# Ready curation stays in P0 and P1, decision samples, 2026-10-14

Les stated two board decisions on 2026-10-14. The active columns hold only P0 and P1 issues. Curating the Ready column narrows attention to that tier, and rethinking priorities is a separate concern, which `sweep-prioritize` covers. #92 and #102 had said the user's criterion replaces the priority default, which let P2 and P3 issues go straight into Ready that evening. The change keeps curation, including the unattended-fit criterion, to P0 and P1 Backlog items. Curation never changes Priority, and it recommends a `sweep-prioritize` re-sweep when the pool is thin. The burndown breaks priority ties by ascending issue number and names any Ready issue below P1. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-priority-tiers-answers.txt) preserve the graded output.

## Source and method

The changed commit is `049c793` on branch `ready-priority-convention`. It replaces an earlier commit on the same branch that had curation promote picks itself. The baseline commit is `e9e6db8` on the local scratch branch `baseline-ready-priority`, which holds main plus the revised scenario criteria. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner. The local server was reserved for the third unattended run, so no Qwen samples ran.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| curate-p0-p1-only | old text | claude-sonnet-5-5 | `e9e6db8` | `9aecc43c-ffea-49c1-b3cd-1e40fa15dd0a` | Fail |
| curate-p0-p1-only | new text | claude-sonnet-5-5 | `049c793` | `8568d8cf-3b47-4283-979e-dfcf0039aa80` | Pass |
| curate-p0-p1-only | new text | claude-sonnet-5-5 | `049c793` | `05849cfa-06aa-40cc-9358-c4a5c5d0a880` | Pass |
| curate-thin-pool | old text | claude-sonnet-5-5 | `e9e6db8` | `da111a5a-948d-47d7-a6d4-977db15aa27e` | Fail |
| curate-thin-pool | new text | claude-sonnet-5-5 | `049c793` | `306c16af-3103-437b-b973-3ae76469c10c` | Pass |
| curate-for-unattended-run | regression | claude-sonnet-5-5 | `049c793` | `8421d57f-b099-4abb-8841-08d54a75e465` | Pass |
| curate-unattended-fit | regression | claude-sonnet-5-5 | `049c793` | `914562d4-d349-4569-877f-3d55a503a677` | Pass |

On the old text, both answers picked the small P2 and P3 issues. They quoted "replaces the priority default" as their reason. On the new text, every answer limited its picks to P0 and P1, named the lower-tier issues only in the thin-pool note, and recommended a `sweep-prioritize` re-sweep. Both regressions passed.

## Limits

No Qwen sample ran. The tie-break by issue number writes down what the coordinator already did; no scenario covers it yet. The grades are the author's.

## Checks

`make check` passed on `049c793`.

```scenario-results
[
 {
  "scenario": "curate-p0-p1-only",
  "date": "2026-10-14",
  "skill_commit": "e9e6db8",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Picked P2 and P3 issues, citing 'replaces the priority default'.",
  "order": 1
 },
 {
  "scenario": "curate-p0-p1-only",
  "date": "2026-10-14",
  "skill_commit": "049c793",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "e9e6db8",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Picked the P3 issue.",
  "order": 1
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "049c793",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "curate-for-unattended-run",
  "date": "2026-10-14",
  "skill_commit": "049c793",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "curate-unattended-fit",
  "date": "2026-10-14",
  "skill_commit": "049c793",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
