# Unattended-fit criterion for curation, decision samples, 2026-10-14

On 2026-10-13 we agreed to write an unattended-fit criterion into curate-ready-queue after the [second burndown](../../docs/research/trials/2026-10-14-unattended-burndown-2.md). Two curations had spelled the same criterion out in their requests. The OpenCode curation ranked #149 as an alternate, although its acceptance criterion needs a running dev server. #540, estimated at 150 to 240 lines, took twice as long as the other picks. The scenario gives the short request "for tonight's unattended burndown" and four candidates modeled on those cases. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-unattended-fit-answers.txt) preserve the graded output.

## Source and method

The changed commits are `b4ba72a` and `e4e7ef1` on branch `unattended-fit`. The second makes size a flag that orders a candidate last, not a condition. The baseline commit is `86262b7` on the local scratch branch `baseline-unattended-fit`, which holds main plus the scenario. It is not for merge. Runs used `claude-sonnet-5-5` under the Claude Code runner.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| curate-unattended-fit | old text | claude-sonnet-5-5 | `86262b7` | `ea4969af-6abe-4722-b76f-7d518025cbfb` | Pass |
| curate-unattended-fit | new text | claude-sonnet-5-5 | `b4ba72a` | `c9fd39ce-4119-4d10-95d6-08a17c6ea1ec` | Partial |
| curate-unattended-fit | new text | claude-sonnet-5-5 | `b4ba72a` | `ef34c2bd-2bae-49de-b7cd-649ec3631091` | Pass |
| curate-unattended-fit | final text | claude-sonnet-5-5 | `e4e7ef1` | `7833142f-d50f-492d-9d41-01dd24636171` | Pass |
| curate-unattended-fit | final text | claude-sonnet-5-5 | `e4e7ef1` | `24182b5b-58ab-429f-aff2-67d9c9a27b09` | Pass |
| curate-for-unattended-run | regression | claude-sonnet-5-5 | `b4ba72a` | `edf4e0fd-ea9c-4f9a-b76b-b1611fb268c1` | Pass |

On the old text, Sonnet already rejected the dev-server issue and put the large one last, so the scenario does not discriminate on Sonnet. The failure was on the local model. On the first changed commit, one sample rejected the large issue outright as over size. That was stricter than the 2026-10-13 decision to take #540 as a flagged third pick, and it led to the second commit. On the final commit, both samples rejected C on its first condition, offered D last with the size risk named, and waited for approval. The regression passed.

## Limits

No Qwen sample ran. The local model's curation is where the #149 miss happened, so the next curation in OpenCode is the real test. The grades are the author's.

## Checks

`make check` passed on `e4e7ef1`.

```scenario-results
[
 {
  "scenario": "curate-unattended-fit",
  "date": "2026-10-14",
  "skill_commit": "86262b7",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "old text",
  "note": "Sonnet reaches the decision without the criterion.",
  "order": 1
 },
 {
  "scenario": "curate-unattended-fit",
  "date": "2026-10-14",
  "skill_commit": "b4ba72a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial / Pass",
  "phase": "new text",
  "note": "One sample rejected D on size; led to e4e7ef1.",
  "order": 2
 },
 {
  "scenario": "curate-unattended-fit",
  "date": "2026-10-14",
  "skill_commit": "e4e7ef1",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "final text",
  "note": null,
  "order": 3
 },
 {
  "scenario": "curate-for-unattended-run",
  "date": "2026-10-14",
  "skill_commit": "b4ba72a",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
