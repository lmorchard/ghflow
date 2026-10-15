# Smaller issues first and lockfile-aware size estimates, decision samples, 2026-10-15

Two findings from the [third burndown](../../docs/research/trials/2026-10-15-unattended-burndown-3.md) drive this change. #930 was estimated at 120 to 200 lines but changed 537 lines with its regenerated lockfiles, and it took three hours. #947 ran last only because of its issue number, so the deadline caught its real review finding. Size estimates now leave out generated files and flag lockfile regeneration. Curation proposes a Size for each pick, and the burndown sorts by priority, then Size smallest first, then issue number. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-15-size-and-order-answers.txt) preserve the graded output.

## Source and method

The changed commit is `c2d8103` on branch `size-and-order`. The baseline commit is `4215477` on the local scratch branch `baseline-size-and-order`, which holds main at the PR #112 merge plus the scenarios. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| burndown-orders-by-size | old text | claude-sonnet-5-5 | `4215477` | `9ff61a2f-c11d-4cad-927c-bc8c5f1b4ad1` | Fail |
| burndown-orders-by-size | new text | claude-sonnet-5-5 | `c2d8103` | `fc11eb4d-c7b6-4a53-98cd-12b6d111448b` | Pass |
| burndown-orders-by-size | new text | claude-sonnet-5-5 | `c2d8103` | `172349f9-e256-4262-98b2-61c90282210a` | Pass |
| burndown-orders-by-size | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `4215477` | `ses_ebfe74895ffei9D4MIteUnbi3z` | Fail |
| burndown-orders-by-size | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `c2d8103` | `ses_ebfe62948ffe8X91V8A9VuWrk3` | Pass |
| curate-size-excludes-lockfiles | old text | claude-sonnet-5-5 | `4215477` | `633d296b-080a-44c8-82ce-c70c0e5980a6` | Partial |
| curate-size-excludes-lockfiles | new text | claude-sonnet-5-5 | `c2d8103` | `a829885a-f6bd-4cb2-930f-fda693ba99a9` | Pass |
| curate-size-excludes-lockfiles | new text | claude-sonnet-5-5 | `c2d8103` | `e8e1c57d-44ee-4433-a0ae-a7dc977e5e13` | Pass |
| curate-thin-pool | regression | claude-sonnet-5-5 | `c2d8103` | `c5ecbdb9-2693-4f37-9e1c-c9d79f0935f3` | Pass |

On the old text, both models ordered the queue by issue number, #600, #930, #947, and the Qwen answer said Size was not a sort key. On the new text, both ordered it #600, #947, #930. In the lockfile scenario, the old-text answer noticed the lockfile risk without a rule and offered the issue as an optional last pick, but proposed no Size values. The new-text answers estimated hand-written change, flagged the lockfile regeneration beside the estimate, ordered the issue last, and proposed Size values. The regression passed.

## Limits

One Qwen sample per text for the ordering scenario, and no Qwen sample for the lockfile scenario. The grades are the author's.

## Checks

`make check` passed on `c2d8103`.

```scenario-results
[
 {
  "scenario": "burndown-orders-by-size",
  "date": "2026-10-15",
  "skill_commit": "4215477",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Fail",
  "phase": "old text",
  "note": "Ordered by issue number.",
  "order": 1
 },
 {
  "scenario": "burndown-orders-by-size",
  "date": "2026-10-15",
  "skill_commit": "c2d8103",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "burndown-orders-by-size",
  "date": "2026-10-15",
  "skill_commit": "4215477",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Fail",
  "phase": "old text",
  "note": "Ordered by issue number; said Size is not a sort key.",
  "order": 1
 },
 {
  "scenario": "burndown-orders-by-size",
  "date": "2026-10-15",
  "skill_commit": "c2d8103",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "curate-size-excludes-lockfiles",
  "date": "2026-10-15",
  "skill_commit": "4215477",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Saw the lockfile risk without a rule; proposed no Size values.",
  "order": 1
 },
 {
  "scenario": "curate-size-excludes-lockfiles",
  "date": "2026-10-15",
  "skill_commit": "c2d8103",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-15",
  "skill_commit": "c2d8103",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
