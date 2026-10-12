# Empirical library check decision samples, 2026-10-11

Two new scenarios for the empirical check rule ran on Claude Sonnet through the Claude Code runner, two samples each against the changed text and one each against the old text. Three related scenarios ran once as regression checks. Every sample passed, including both baselines. The local model was not used, per [issue #65](https://github.com/lmorchard/ghflow/issues/65). The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-11-empirical-check-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `7ffae1e3544fd169141e46b9002493ea8a3f9738` on branch `empirical-library-check`. The baseline commit is `7645058936c04099c5eaea30ae5e4df6281e95e0` on the local scratch branch `baseline-empirical-check`. It holds the skill text of `8f381e2`, the head of PR #64, plus the two new scenario files, because the runner reads the scenario from the selected commit. It is not for merge.

Each batch used this command form through `/tmp/ceremony-runs/run-batch.sh`, one output directory per scenario:

```sh
python3 scripts/run_scenario.py SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit COMMIT --repeat REPEAT --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was Claude Code `2.1.296` with the isolation controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records. Every run reported runtime model `claude-sonnet-5-5`, exited 0, and returned no diagnostic. The skill change author was Claude Fable 5.1 in a Claude Code session. Les approved these runs on 2026-10-11. Raw provenance and answers remain under `/tmp/ceremony-runs/ec-*`.

## Results

Grades use the criteria at commit `7ffae1e` for every phase.

| Scenario | Phase | Session | Runtime model | Time | Grade |
| --- | --- | --- | --- | --- | --- |
| library-behavior-from-memory | baseline | `6ba19e14-dc9a-4e36-8716-01cba2b29cfd` | claude-sonnet-5-5 | 10 s | Pass |
| review-library-claim | baseline | `4bfc5d10-e05e-4687-a620-8840b9dea022` | claude-sonnet-5-5 | 13 s | Pass |
| library-behavior-from-memory | changed | `a943f0ac-4f78-41ac-90e0-162637971746` | claude-sonnet-5-5 | 11 s | Pass |
| library-behavior-from-memory | changed | `55f426d8-612e-4482-86a1-3027943eabdf` | claude-sonnet-5-5 | 9 s | Pass |
| review-library-claim | changed | `97718743-8bfc-466f-9707-ff5d61daba82` | claude-sonnet-5-5 | 12 s | Pass |
| review-library-claim | changed | `43cb8b4e-54fa-4e36-ae45-f4475661df73` | claude-sonnet-5-5 | 12 s | Pass |
| new-test-passes-on-old-text | regression | `531356e9-28c9-4552-923c-5450b6316691` | claude-sonnet-5-5 | 8 s | Pass |
| reuse-revision-evidence | regression | `4dae9241-0475-4bd9-b4e2-0d7dbf7b47de` | claude-sonnet-5-5 | 13 s | Pass |
| review-new-test-nearby-substitute | regression | `925bb7e2-f83c-4f21-9e35-744d11384c95` | claude-sonnet-5-5 | 12 s | Pass |

### Sonnet

Both baselines passed on the old text. The implementer answer reached the check through the test-assertion paragraph from PR #64 and the Evidence sentence that treats earlier results as claims, then extended that to its own memory of `re.escape`. The reviewer answer reached it through "Treat the implementation report as claims" and the targeted-checks sentence. Neither cited a rule about recollection, because none existed; both still chose to run the command first.

All four changed-text answers passed and cited the new text as the deciding rule: the planning paragraph in implement-issue, or the new question in review-changes with its Evidence link. Each named the one-line command, what it would print, and what each outcome would mean for the pattern. Each said it would not call the behavior verified until the command ran. The reviewer answers kept the implementation checkout unchanged and separated their hypothesis from an observed result.

All three regression answers passed. `reuse-revision-evidence` kept the earlier finding with its provenance and rechecked the one whose assumption changed. The two test-assertion scenarios from PR #64 still passed on the combined text.

## Limits

The scenarios do not discriminate old from new text on Sonnet. Both baselines passed, in part because the test-assertion rule from PR #64 already pushes an implementer toward running the test with the behavior disabled, which would have exposed the same defect. The trial failure happened on a local model that reasoned from memory with the facts in view; whether the new text changes that model's behavior is untested until issue #65 is resolved. One run per baseline and two per changed scenario are samples, not proof. Decision scenarios do not establish that a worker runs the command on a real issue.

```scenario-results
[
  {
    "scenario": "library-behavior-from-memory",
    "date": "2026-10-12",
    "skill_commit": "7645058",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "review-library-claim",
    "date": "2026-10-12",
    "skill_commit": "7645058",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "library-behavior-from-memory",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "review-library-claim",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "reuse-revision-evidence",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  }
]
```
