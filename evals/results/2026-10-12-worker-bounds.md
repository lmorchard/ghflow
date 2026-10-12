# Worker bounds decision samples, 2026-10-12

Three new scenarios for the worker-bounds change ran on Claude Sonnet, two samples each against the changed text and one against the old text, and on the local Qwen model, one sample against each text. Four related scenarios ran once on Sonnet as regression checks. Every sample passed, including every baseline. On Qwen the new text halved the time and the output tokens across the three scenarios. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-worker-bounds-answers.txt) preserve the output used for grading. The source is the [issue #1012 delivery record](../../docs/research/trials/2026-10-12-issue-1012-qwen-delivery.md).

## Source and method

The changed source commit is `21faf2c305c2d37a95d47034920b6b595c2e4a87` on branch `worker-bounds`. The baseline commit is `08c0c1af663fa2b57ce6488465e1b0af1ad0c23e` on the local scratch branch `baseline-worker-bounds`. It holds the skill text of main at `6cc6f46` plus the three new scenario files. It is not for merge.

Sonnet runs used the Claude Code runner with the controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records; every run reported `claude-sonnet-5-5`. Qwen runs used the OpenCode runner with `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` at `http://127.0.0.1:9931/v1`, context and output limits 262144, one at a time, with the server otherwise idle, as the [Qwen comparison](2026-10-12-qwen-rule-comparison.md) describes. Les approved these runs on 2026-10-12. Raw provenance remains under `/tmp/ceremony-runs/wb-*` and `/tmp/ceremony-runs/q[bc]-bounds-*`.

## Results

Grades use the criteria at commit `21faf2c` for every phase.

| Scenario | Phase | Commit | Session | Seconds | Output tokens | Reads | Grade |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| baseline-environment-bound | Sonnet, old text | `08c0c1a` | `db7d49a8-7c76-4f5c-aaa1-6db2a0c6ee60` | 11 | - | - | Pass |
| one-full-suite-at-a-time | Sonnet, old text | `08c0c1a` | `4fd346b6-9147-4843-ae1d-70c4ccd8087a` | 15 | - | - | Pass |
| notes-commit-after-review | Sonnet, old text | `08c0c1a` | `96aa17b7-1eb7-4648-bef6-a03a06afdc13` | 18 | - | - | Pass |
| baseline-environment-bound | Sonnet, new text | `21faf2c` | `9f01f3ce-dcf3-414b-b73b-5afcf3fa7a5e` | 10 | - | - | Pass |
| baseline-environment-bound | Sonnet, new text | `21faf2c` | `1b5dcd13-7ae8-4dcb-acd7-74074404abaa` | 10 | - | - | Pass |
| one-full-suite-at-a-time | Sonnet, new text | `21faf2c` | `943b580d-f685-44f2-b787-74cc6a58a9c6` | 7 | - | - | Pass |
| one-full-suite-at-a-time | Sonnet, new text | `21faf2c` | `a2579373-884e-4551-b1d6-f2f65bd51cb3` | 7 | - | - | Pass |
| notes-commit-after-review | Sonnet, new text | `21faf2c` | `afcb94f7-d321-4873-b5e3-03fa23d8bccf` | 16 | - | - | Pass |
| notes-commit-after-review | Sonnet, new text | `21faf2c` | `a0026f2a-f243-433f-9a03-59fc9e4ca326` | 15 | - | - | Pass |
| implementation-local-only | Sonnet, regression | `21faf2c` | `7f8647bf-dad0-4a37-8692-1c25ac8c9121` | 9 | - | - | Pass |
| draft-pr-ready-transition | Sonnet, regression | `21faf2c` | `b77518d8-d783-4d10-ab9c-8527b9ba64da` | 10 | - | - | Pass |
| notes-result-before-run | Sonnet, regression | `21faf2c` | `afe5fcb8-a7da-41b7-91a5-b54d395a324a` | 11 | - | - | Pass |
| new-test-passes-on-old-text | Sonnet, regression | `21faf2c` | `5f81b48d-0ecb-4c15-a05d-7c5f06a4892b` | 9 | - | - | Pass |
| baseline-environment-bound | Qwen, old text | `08c0c1a` | `ses_ecf7f1b4effeQY6YBiVBwWnLU9` | 149 | 3134 | implement-issue.md | Pass |
| one-full-suite-at-a-time | Qwen, old text | `08c0c1a` | `ses_ecf7ccef7ffeO6Umnb7RwZPT73` | 247 | 4418 | implement-issue.md | Pass |
| notes-commit-after-review | Qwen, old text | `08c0c1a` | `ses_ecf7902b8ffeLNhyH7djj4cyew` | 512 | 9292 | implement-issue.md, submit-pr.md | Pass |
| baseline-environment-bound | Qwen, new text | `21faf2c` | `ses_ecf712cb3ffe33x1AtPv26OSaC` | 152 | 2707 | implement-issue.md | Pass |
| one-full-suite-at-a-time | Qwen, new text | `21faf2c` | `ses_ecf6ed212ffeKrOQExXFPn1kwB` | 98 | 1727 | implement-issue.md | Pass |
| notes-commit-after-review | Qwen, new text | `21faf2c` | `ses_ecf6d4eebffeJ6OcY4mCo5YAdB` | 182 | 3078 | implement-issue.md, submit-pr.md, task-notes.md, github-writes.md | Pass |

### Qwen, old versus new

| Scenario | Old s / tokens | New s / tokens |
| --- | ---: | ---: |
| baseline-environment-bound | 149 / 3,134 | 152 / 2,707 |
| one-full-suite-at-a-time | 247 / 4,418 | 98 / 1,727 |
| notes-commit-after-review | 512 / 9,292 | 182 / 3,078 |
| Total | 908 / 16,844 | 432 / 7,512 |

All six Qwen answers reached the expected decision. On the old text they reasoned from the baseline sentence, the targeted-first sentence, and "a review that covers an earlier commit does not qualify". On the new text they quoted the new paragraphs. The environment-bound scenario cost the same either way; the other two cost less than half.

### Sonnet

All three baselines passed from the existing sentences, with the one-suite baseline noting that "no single line forbids a concurrent run" and deciding from three rules together. All six changed-text answers passed and quoted the new sentences. The four regression answers kept their decisions; the notes-result-before-run answer added "with one full suite at a time" to its plan unprompted.

## Limits

The scenarios do not discriminate old from new text on either model. Each scenario states the facts the worker lacked in one place during the real run: the green configurations and the time spent, the two suites side by side, or the full notes plan with its CI waits. The #1012 worker had those facts spread across two and a half hours and did not stop; a decision scenario cannot reproduce that. What the Qwen pairs show is that the named rules cut the cost of reaching the decision, which matched the empirical-check result from the previous comparison. One run per baseline is a sample. The grades are the author's.

```scenario-results
[
  {
    "scenario": "baseline-environment-bound",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "one-full-suite-at-a-time",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "notes-commit-after-review",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "baseline-environment-bound",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sonnet-new-text",
    "note": null,
    "order": 2
  },
  {
    "scenario": "one-full-suite-at-a-time",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sonnet-new-text",
    "note": null,
    "order": 2
  },
  {
    "scenario": "notes-commit-after-review",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sonnet-new-text",
    "note": null,
    "order": 2
  },
  {
    "scenario": "implementation-local-only",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "draft-pr-ready-transition",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "notes-result-before-run",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "sonnet-regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "baseline-environment-bound",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "one-full-suite-at-a-time",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "notes-commit-after-review",
    "date": "2026-10-12",
    "skill_commit": "08c0c1a",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "baseline-environment-bound",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "one-full-suite-at-a-time",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "notes-commit-after-review",
    "date": "2026-10-12",
    "skill_commit": "21faf2c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  }
]
```
