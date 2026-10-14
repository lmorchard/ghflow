# Thin unattended pool and the fit table template, decision samples, 2026-10-14

On 2026-10-14 the OpenCode curation applied the unattended-fit conditions from #102. It then filled three slots with issues estimated at 100 to 350 lines, led by the two largest, and skipped the per-condition results. The change makes the requested count a maximum, allows at most one oversized optional pick, and gives the unattended table a template with a column per condition. The scenario gives a thin pool: two small fitting issues, three oversized P1 issues, and one live-service issue. It ran on Claude Sonnet and on the local Qwen model against the old and new text. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-curate-thin-pool-answers.txt) preserve the graded output.

## Source and method

The changed commit is `64bee90` on branch `curate-thin-pool`. The baseline commit is `ed187c3` on the local scratch branch `baseline-curate-thin-pool`, which holds main at `2485385` plus the scenario. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| curate-thin-pool | old text | claude-sonnet-5-5 | `ed187c3` | `48d2d8d7-a368-4ea9-b2e0-47a53bb989a9` | Partial |
| curate-thin-pool | new text | claude-sonnet-5-5 | `64bee90` | `05ec7853-1604-40c2-bb2e-bf01ac1a2460` | Pass |
| curate-thin-pool | new text | claude-sonnet-5-5 | `64bee90` | `a8ce719e-5b09-4592-b0c0-a8e8da096083` | Pass |
| curate-thin-pool | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `ed187c3` | `ses_ec41e040dffe7u52y3arWibDpc` | Partial |
| curate-thin-pool | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `64bee90` | `ses_ec414eca0ffe4bOSYNenWDejp0` | Pass |
| curate-unattended-fit | regression | claude-sonnet-5-5 | `64bee90` | `c4167a54-71c5-4939-b81c-a371af379e55` | Pass |
| curate-for-unattended-run | regression | claude-sonnet-5-5 | `64bee90` | `45ae2889-b55b-41b8-84cc-66aff6c9d809` | Pass |

On the old text, both models proposed the two small issues plus G as a third, without saying the pool was thin. Qwen also offered E and F, which is more than one oversized pick. Both score Partial. Neither reproduced the real curation's failure of proposing only oversized issues, because this scenario includes two small fitting issues. On the new text, every answer proposed the two small issues, named only G as an optional last pick, and said the pool was thin. Both Sonnet answers rendered the template table. The Qwen answer described presenting the table with rejected rows but did not render it, so the template's effect on the local model is unshown.

## Limits

One Qwen sample per text. The scenario's pool differs from the real one, which had fewer small fitting issues. The grades are the author's.

## Checks

`make check` passed on `64bee90`.

```scenario-results
[
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "ed187c3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Proposed H, I, G as a full batch; no thin-pool statement.",
  "order": 1
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "64bee90",
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
  "skill_commit": "ed187c3",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Partial",
  "phase": "old text",
  "note": "Proposed H, I, G and offered E and F too.",
  "order": 1
 },
 {
  "scenario": "curate-thin-pool",
  "date": "2026-10-14",
  "skill_commit": "64bee90",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Pass",
  "phase": "new text",
  "note": "Right decision; described the table without rendering it.",
  "order": 2
 },
 {
  "scenario": "curate-unattended-fit",
  "date": "2026-10-14",
  "skill_commit": "64bee90",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "curate-for-unattended-run",
  "date": "2026-10-14",
  "skill_commit": "64bee90",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
