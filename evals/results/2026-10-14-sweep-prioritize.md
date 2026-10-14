# sweep-prioritize as the promotion path, decision samples, 2026-10-14

With Ready curation limited to P0 and P1 in #110, `sweep-prioritize` is where issues move between priority tiers. The change gives it that role and adds four things. It re-sweeps the lower tiers when curation reports a thin pool. It adds P4 and uses the board's own Priority options. It reports unattended-fit results as evidence when the re-sweep feeds an unattended run. It changes no field before the user confirms, and then writes with `board set-field`. The scenario asks for a re-sweep for tonight's run over two small fitting issues, one browser-checked issue, and one oversized issue. It ran on Claude Sonnet and on the local Qwen model against the old and new text. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-14-sweep-prioritize-answers.txt) preserve the graded output.

## Source and method

The changed commit was `9a98ffb`, stacked on the #110 branch. It became `3f13829` when rebased onto main after #110 merged, with the same text. The baseline commit is `a6df7e3` on the local scratch branch `baseline-sweep-prioritize`, which holds the #110 branch plus the scenario. It is not for merge. Sonnet ran under the Claude Code runner and Qwen under the OpenCode runner against the local llama server.

## Results

| Scenario | Phase | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- |
| sweep-promotes-for-unattended | old text | claude-sonnet-5-5 | `a6df7e3` | `47fe9115-16ac-4406-b8b9-873a1648d1e4` | Partial |
| sweep-promotes-for-unattended | new text | claude-sonnet-5-5 | `9a98ffb` | `da0596e1-4c5e-4749-ad85-6abfe0c9ff23` | Pass |
| sweep-promotes-for-unattended | new text | claude-sonnet-5-5 | `9a98ffb` | `88256690-e370-48e9-8602-00f79b72da75` | Pass |
| sweep-promotes-for-unattended | old text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `a6df7e3` | `ses_ec37ee815ffejUU6y4cPNHMNjY` | Partial |
| sweep-promotes-for-unattended | new text | ggml-org/Qwen3.8-27B-GGUF:Q4_K_M | `9a98ffb` | `ses_ec3716acbffeHr0DdUhIwpHjCh` | Partial |
| sweep-material-choice | regression | claude-sonnet-5-5 | `9a98ffb` | `8a3e92f6-3c86-4a6a-8ba6-88e55c575926` | Pass |
| curate-p0-p1-only | regression | claude-sonnet-5-5 | `9a98ffb` | `8b4ef632-0bb5-4e13-a34d-d5b5fa187eb7` | Pass |

On the old text, both models ranked the issues sensibly but treated fit as a later curation concern, so neither gave per-condition evidence in the sweep. Neither named a write command. Qwen also called the request a Ready selection that the sweep does not cover. Both score Partial. On the new text, both Sonnet answers gave the fit result per condition beside current and suggested priority. They kept the browser-checked issue in its tier, flagged the oversized one, changed nothing before confirmation, and named `board set-field` with promoted issues left in Backlog. The Qwen answer reached the same decision and fit results, but it described the write as "update the board fields with read-backs" without naming `board set-field`, so it scores Partial.

## Limits

One Qwen sample per text. The grades are the author's.

## Checks

`make check` passed on `3f13829`.

```scenario-results
[
 {
  "scenario": "sweep-promotes-for-unattended",
  "date": "2026-10-14",
  "skill_commit": "a6df7e3",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Partial",
  "phase": "old text",
  "note": "Left fit to curation; no write command named.",
  "order": 1
 },
 {
  "scenario": "sweep-promotes-for-unattended",
  "date": "2026-10-14",
  "skill_commit": "9a98ffb",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass (2/2)",
  "phase": "new text",
  "note": null,
  "order": 2
 },
 {
  "scenario": "sweep-promotes-for-unattended",
  "date": "2026-10-14",
  "skill_commit": "a6df7e3",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Partial",
  "phase": "old text",
  "note": "Treated the request as a Ready selection; no fit evidence; no write command.",
  "order": 1
 },
 {
  "scenario": "sweep-promotes-for-unattended",
  "date": "2026-10-14",
  "skill_commit": "9a98ffb",
  "runner": "opencode",
  "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
  "grade": "Partial",
  "phase": "new text",
  "note": "Right decision and fit results; did not name board set-field.",
  "order": 2
 },
 {
  "scenario": "sweep-material-choice",
  "date": "2026-10-14",
  "skill_commit": "9a98ffb",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 },
 {
  "scenario": "curate-p0-p1-only",
  "date": "2026-10-14",
  "skill_commit": "9a98ffb",
  "runner": "claude",
  "model": "claude-sonnet-5-5",
  "grade": "Pass",
  "phase": "regression",
  "note": null,
  "order": null
 }
]
```
