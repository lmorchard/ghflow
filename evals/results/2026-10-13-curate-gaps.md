# Curate-ready-queue gaps and board set-field, decision samples, 2026-10-13

One new scenario covers the curate-ready-queue changes from the 2026-10-12 curation audit, which the [unattended burndown record](../../docs/research/trials/2026-10-13-unattended-burndown.md) lists as its eighth candidate. It ran on Claude Sonnet once against the old text and twice against the new text. Two board scenarios ran once as regression checks. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-10-13-curate-gaps-answers.txt) preserve the graded output.

## Source and method

The changed commit is `e4b6e76` on branch `curate-gaps-d`. The baseline commit is `0b3d957` on the local scratch branch `baseline-curate-gaps-d`, which holds main at `acbaeb1` plus the scenario. It is not for merge. The model was `claude-sonnet-5-5` under the Claude Code runner with the controls that earlier results record.

## Results

| Scenario | Phase | Commit | Session | Grade |
| --- | --- | --- | --- | --- |
| curate-for-unattended-run | old text | `0b3d957` | `0d2e1fed-000a-4e46-aee9-560c04939900` | Partial |
| curate-for-unattended-run | new text | `e4b6e76` | `8962e7af-8006-4939-b5aa-c1291ca6baff` | Pass |
| curate-for-unattended-run | new text | `e4b6e76` | `36e6ed02-2002-4f05-b729-52d429d78fa7` | Pass |
| board-transition-cli | regression | `e4b6e76` | `95d4a194-6db4-4889-8340-1bef950df1d3` | Pass |
| board-status-no-pre-read | regression | `e4b6e76` | `80a20047-84dd-4861-bc25-b2af717f9743` | Pass |

The old-text answer distrusted the labels and read bodies, but kept the candidate pool at P0 and P1. It offered P2 to P4 items only as an exception that needed the user's explicit decision, and pointed to sweep-prioritize instead. Both new-text answers named the validated traversal, let the user's criterion replace the priority default, recommended moving all three Ready items back with `--allow-backward` and the user's decision as the reason, and waited for approval. The transition regression chose `pr ready` for a draft and `board set-status` for a PR that is already ready, which matches the situation.

## Limits

The `board set-field` command has unit tests against a fake board, not a live write. No sample ran on the local Qwen model. The grades are the author's.

## Checks

`make check` passed on `e4b6e76`, including nine new `board set-field` tests.

```scenario-results
[
  {"scenario": "curate-for-unattended-run", "date": "2026-10-13", "skill_commit": "0b3d957", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Partial", "phase": "old text", "note": "Kept the pool at P0/P1; offered smaller items only as an exception.", "order": 1},
  {"scenario": "curate-for-unattended-run", "date": "2026-10-13", "skill_commit": "e4b6e76", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "new text", "note": null, "order": 2},
  {"scenario": "board-transition-cli", "date": "2026-10-13", "skill_commit": "e4b6e76", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null},
  {"scenario": "board-status-no-pre-read", "date": "2026-10-13", "skill_commit": "e4b6e76", "runner": "claude", "model": "claude-sonnet-5-5", "grade": "Pass", "phase": "regression", "note": null, "order": null}
]
```
