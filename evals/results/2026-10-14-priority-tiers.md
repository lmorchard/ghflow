# Priority tiers on the active board columns, decision samples, 2026-10-14

Les stated a board convention on 2026-10-14. Ready, In progress, and In review hold only P0 and P1 issues, and an issue enters Ready only after the user promotes it to P1 or P0. #92 and #102 had said the user's criterion replaces the priority default, which let P2 and P3 issues go straight into Ready that evening. The change adds a Priority tiers rule to board-status. Curation proposes a promotion with each pick below P1 and sets Priority with `board set-field` before the move. The burndown breaks priority ties by ascending issue number and names any Ready issue below P1. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-priority-tiers-answers.txt) preserve the graded output.

## Source and method

The changed commit is `b201c90` on branch `ready-priority-convention`. The baseline commit is `855f89a` on the local scratch branch `baseline-ready-priority`, which holds main plus the updated scenario criteria. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner. The local server was reserved for the third unattended run, so no Qwen samples ran.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| curate-promotes-before-ready | old text | claude-sonnet-5-5 | `855f89a` | `0288a518-4a24-405b-9fc6-75928b1c4ff3` | Pass |
| curate-promotes-before-ready | new text | claude-sonnet-5-5 | `b201c90` | `4089d971-85f7-430f-8e02-cfc53b73e258` | Pass |
| curate-promotes-before-ready | new text | claude-sonnet-5-5 | `b201c90` | `1a611c2e-3457-4861-895c-4e88aa1bfe52` | Pass |
| curate-thin-pool | old text | claude-sonnet-5-5 | `855f89a` | `dd255a34-cf5f-4189-98a5-c4c320d0f7bc` | Partial |
| curate-thin-pool | new text | claude-sonnet-5-5 | `b201c90` | `a855258f-02de-4773-80c2-c2c1bc43f45d` | Pass |
| curate-for-unattended-run | regression | claude-sonnet-5-5 | `b201c90` | `7d1a143c-80e6-471d-9a12-6cd9f5cae314` | Pass |
| board-transition-cli | regression | claude-sonnet-5-5 | `b201c90` | `b2eec7ce-dd78-481e-ac7f-efdb420c8d63` | Pass |

The promotion scenario does not discriminate on Sonnet. Its situation says the user approved "promote to P1", and the old text already let the user decide a Priority. On the old text, the thin-pool answer kept its correct thin-pool decision but proposed the P3 and P2 picks with no promotion, so it scores Partial under the new criteria. On the new text, the answer marked both "pick, promote ... to P1". Both regressions passed.

## Limits

No Qwen sample ran. The tie-break by issue number writes down what the coordinator already did; no scenario covers it yet. The grades are the author's.

## Checks

`make check` passed on `b201c90`.

```scenario-results
[
 {
  "scenario": "curate-promotes-before-ready",
  "date": "2026-10-14",
  "skill_commit": "855f89a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "The situation states the approved promotion.",
  "order": 1
 },
 {
  "scenario": "curate-promotes-before-ready",
  "date": "2026-10-14",
  "skill_commit": "b201c90",
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
  "skill_commit": "855f89a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Correct thin-pool decision; no promotion proposed for the P3 and P2 picks.",
  "order": 1
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "b201c90",
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
  "skill_commit": "b201c90",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "board-transition-cli",
  "date": "2026-10-14",
  "skill_commit": "b201c90",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
