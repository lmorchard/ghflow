# PR comments access decision samples, 2026-10-12

One new scenario for the `pr-state` comments change ran on Claude Sonnet, two samples against the changed text and one against the old text, and on the local Qwen model, one sample against each text. Two related scenarios ran once on Sonnet as regression checks. Every sample passed. The change is a tool capability as much as a rule, so the scenario cannot separate the texts; both models already refused to claim "no comments" without a read when the situation says the comments were never examined. The author graded the answers.

The [returned answers](2026-10-12-pr-state-comments-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `83b22372a4a5fffa8420e4a64d00af446111cbdc` on branch `pr-state-comments`. The baseline commit is `7e4a58b9a057494a3a5fa0dc375249c739f13d25` on the local scratch branch `baseline-pr-comments`. It holds the skill text of main at `fbdd091` plus the new scenario file. It is not for merge.

Sonnet runs used the Claude Code runner with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. Qwen runs used the OpenCode runner with `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` at `http://127.0.0.1:9931/v1`, context and output limits 262144, as the [Qwen comparison](2026-10-12-qwen-rule-comparison.md) describes. Les approved these runs on 2026-10-12. Raw provenance remains under `/tmp/ceremony-runs/pc-*` and `/tmp/ceremony-runs/q[bc]-comments-*`.

## Results

Grades use the criteria at commit `83b2237` for every phase.

| Scenario | Phase | Commit | Session | Seconds | Output tokens | Reads | Grade |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| review-comments-unread | Sonnet, old text | `7e4a58b` | `8e11e6bb-0241-44dc-abe7-fc5ca5f4832f` | 8 | - | - | Pass |
| review-comments-unread | Sonnet, new text | `83b2237` | `c518e4b3-42b2-4b56-b426-440cf5134598` | 9 | - | - | Pass |
| review-comments-unread | Sonnet, new text | `83b2237` | `1b49fa16-0aff-4531-8fd6-0ae27af012db` | 11 | - | - | Pass |
| commented-review-empty | Sonnet, regression | `83b2237` | `954b221d-833e-43b6-99e6-c4e5bcd712ab` | 10 | - | - | Pass |
| review-new-test-nearby-substitute | Sonnet, regression | `83b2237` | `9b23753b-3cb3-4de0-834c-445a8ffe87d8` | 12 | - | - | Pass |
| review-comments-unread | Qwen, old text | `7e4a58b` | `ses_ed2059eddffeCbbnr4IZmwpgwH` | 104 | 2182 | review-changes.md | Pass |
| review-comments-unread | Qwen, new text | `83b2237` | `ses_ed204009dffegJ6LaaiLT8w58x` | 121 | 2460 | review-changes.md, cli.md | Pass |

### Sonnet

The baseline passed by recognizing that the old `pr-state` output did not cover conversation comments and planning a separate fetch of every page, under the old sentence "Include top-level comments and reviews without inline threads." Both changed-text answers passed and quoted the new sentence, split the claim into "no reviews", which the empty list supports, and "no comments", which needs its own read, and named the three outcomes for the `comments` part: empty list, entries to read, or `null` to re-read or report. Both regression answers kept their decisions.

### Qwen

The old-text answer passed in 104 seconds by the same reasoning as Sonnet's baseline, from the old sentence alone, but it had no tool path to the comments and did not name one. The new-text answer passed in 121 seconds, read `cli.md` as well, and gave the same three-outcome plan from the `comments` part, quoting the new sentence and the CLI rule that an empty list means the read found none.

## Limits

The scenario states that the reviewer never looked at the comments, which makes the gap visible in a way the real trial did not; the trial reviewer read a `pr-state` output that had no comments part and did not notice the omission. The change closes that gap by returning the comments in the same read, which a decision scenario cannot exercise. One run per phase is a sample. The grades are the author's.

```scenario-results
[
  {
    "scenario": "review-comments-unread",
    "date": "2026-10-12",
    "skill_commit": "7e4a58b",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-old-text",
    "note": "Old skill text with current scenario file, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "review-comments-unread",
    "date": "2026-10-12",
    "skill_commit": "83b2237",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sonnet-new-text",
    "note": null,
    "order": 2
  },
  {
    "scenario": "commented-review-empty",
    "date": "2026-10-12",
    "skill_commit": "83b2237",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-12",
    "skill_commit": "83b2237",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "review-comments-unread",
    "date": "2026-10-12",
    "skill_commit": "7e4a58b",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario file, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "review-comments-unread",
    "date": "2026-10-12",
    "skill_commit": "83b2237",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  }
]
```
