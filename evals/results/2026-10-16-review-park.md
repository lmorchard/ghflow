# Review prepare and park commands, decision samples, 2026-10-16

`review prepare`, `review cleanup`, and `park` replace two manual procedures. Reviewers rebuilt a detached worktree at the PR head by hand in every review, and the parking procedure took up to 26 minutes of model time in the [third burndown](../../docs/research/trials/2026-10-15-unattended-burndown-3.md). One new scenario checks that a coordinator parks with the command. Two regressions cover the deadline and uncertainty parks. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-16-review-park-answers.txt) preserve the graded output.

## Source and method

The changed commit is `7b2be50` on branch `cli-review-park`, stacked on #119. The baseline commit is `abcd04d` on the local scratch branch `baseline-cli-review-park`, which holds the #119 branch plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| park-uses-cli | old text | claude-sonnet-5-5 | `abcd04d` | `189fd17c-e4fd-4c3f-b649-8ca3be95f696` | Partial |
| park-uses-cli | new text | claude-sonnet-5-5 | `7b2be50` | `92e32bfe-5ccd-4a03-a5dc-3534e516198c` | Pass |
| park-uses-cli | new text | claude-sonnet-5-5 | `7b2be50` | `296659a2-788f-4364-a51c-ab1d3b4f0fa5` | Pass |
| deadline-ready-step-finishes | regression | claude-sonnet-5-5 | `7b2be50` | `faa750a5-9abc-4077-9f19-3a16fd998158` | Pass |
| unattended-parks-on-uncertainty | regression | claude-sonnet-5-5 | `7b2be50` | `f51c18f8-64c8-4bc2-9819-6b6efdf82bbd` | Pass |

The old-text answer parked correctly but followed the manual steps, so it scores Partial. Both new-text answers ran `ghflow park` with `--kind time` and a remaining-steps file. The uncertainty regression ran `park` with `--kind question`. The deadline regression still let the started ready step finish.

## Limits

The commands have unit tests against temporary Git repositories and a fake GitHub that applies the writes. Neither ran live against the subject repository, which belongs to the OpenCode agent's runs. The grades are the author's.

## Checks

`make check` passed on `7b2be50`.

```scenario-results
[
 {
  "scenario": "park-uses-cli",
  "date": "2026-10-16",
  "skill_commit": "abcd04d",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Right decision; manual steps.",
  "order": 1
 },
 {
  "scenario": "park-uses-cli",
  "date": "2026-10-16",
  "skill_commit": "7b2be50",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "deadline-ready-step-finishes",
  "date": "2026-10-16",
  "skill_commit": "7b2be50",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "unattended-parks-on-uncertainty",
  "date": "2026-10-16",
  "skill_commit": "7b2be50",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
