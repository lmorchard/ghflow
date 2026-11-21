# Epic #1438 local-model burndown and compact-tags trial, 2026-11-20 to 2026-11-21

This record covers one unattended queue run of `scripts/run_queue.py` on parent [lmorchard/decafclaw#1438](https://github.com/lmorchard/decafclaw/issues/1438) (test suite hygiene). All worker sessions used the pinned local model `lmstudio/qwen3.8-27b-mlx@4bit`. The run also tested the compact tags from [#211](https://github.com/lmorchard/gh-project-workflow/pull/211).

## Facts

- Date: 2026-11-20 17:30 to 2026-11-21 01:16 local (7.8 hours).
- Skills: `ab0d88d499f03d1d9f6d5f96e97b397da84432f1` (workflow main, compact tags merged at 16:51).
- Subject: decafclaw, launch base `3cfa00196c5fba4694221aa21d22e78171c08728`, base CI green.
- Scope: the six open children #1419 to #1424, all `triage:ready` and `impl:local`. Nothing else was selected.
- Endpoint: through review follow-up. The PRs stay open. No merge.
- Runner: `--parent lmorchard/decafclaw#1438 --project lmorchard/6 --model lmstudio/qwen3.8-27b-mlx@4bit --require-label impl:local --hours 8 --floor 30`.
- Notebook: https://github.com/lmorchard/decafclaw/discussions/1607.

## Result

| Issue | PR and head | CI | Review | Outcome |
| --- | --- | --- | --- | --- |
| #1423 | [#1610](https://github.com/lmorchard/decafclaw/pull/1610) `0f20724` | green | clean, same model | ready, In review |
| #1424 | [#1611](https://github.com/lmorchard/decafclaw/pull/1611) `d936f35` | green | clean, same model | ready, In review |
| #1419 | none | not run | not run | parked (blocker), `triage:needs-input` |
| #1420 | [#1614](https://github.com/lmorchard/decafclaw/pull/1614) `9b6d51f` | green | clean, same model | ready, In review |
| #1421 | [#1619](https://github.com/lmorchard/decafclaw/pull/1619) `dcf16807` | green | clean, same model | draft, not ready |
| #1422 | none | not run | not run | not started |

The run summary lists four deliveries: three DONE and one parked. #1421 and #1422 are not in that table. Their states come from GitHub.

## Evidence limits

- One run. The baseline uses different issues, so no controlled comparison is possible.
- The runtime reports no cached-prompt tokens in either run (cache read and write are zero).
- No coverage measurement was made.
- The runner debrief shows zero tags because it reads a truncated shell summary. This report counts tags from the full session log.
- The review is same-model in a fresh session. Different-model review was waived under the standing local-model exception. The waiver does not authorize merge.
- #1421 is a draft. No ready submission or merge occurred.
- #1419 is parked. No code exists for it.

## Skill or runner changes

No skill or runner change was made during this trial. The candidate changes are in [report.md](report.md).
