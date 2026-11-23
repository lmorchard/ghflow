# Decafclaw janitorial weekend burndown, 2026-11-21 to 2026-11-22

This record covers one unattended weekend run of the queue runner over the local-model janitorial work in decafclaw. It tested the runner fixes merged before the run: the floor exemption, the gate-generated path restore, the checkpoint instruction, the tags signal, and the stale-source injection.

## Facts

- Dates: 2026-11-21 10:55 to 2026-11-22 00:13 local (37.3 hours).
- Skills: `065ae5064ae921a682fd077219ef65058370ed97` (workflow main, the five fixes merged).
- Subject: `lmorchard/decafclaw`, launch base `9c02ef43efb46f7a9b7106e9f216627d000dc937`.
- Scope: 33 `triage:ready` + `impl:local` children across the janitorial epics #1427 to #1437, plus #1438's #1422. The `impl:strong` children were out of scope.
- Model: `lmstudio/qwen3.8-27b-mlx@4bit`.
- Endpoint: review follow-up. The user merged 23 pull requests during the run. No auto-merge occurred. The four open ready pull requests and the two drafts were left for wrap-up.
- Runner: a five-phase supervisor. Phase A used no stack. Phase B used `--stack` for the vault split series. Phase C ran the independent helpers. Phase D used `--stack` for the HTTP dedupe. Phase E ran #1422.
- Result: 27 done of 33. 23 merged and 4 open ready. 2 drafts with committed work. 3 parked. 1 not started.

## Evidence limits

- One run. The task mix differs from the earlier #1432 and #1438 runs, so the throughput comparisons are not controlled.
- The review was same-model in a fresh session. The standing local-model exception allowed it. No different-model review occurred.
- No coverage measurement was made.
- The user merged pull requests during the run. Their merge order and timing are not part of the runner's behavior.
- The run log is local and not committed: `~/.local/state/ghflow/notes/runner-janitorial-20261121-1056.log`.
- The final wrap-up (the four open ready pull requests, the two drafts, and the parks) is pending.

## Skill or runner changes

No skill or runner change was made during the run. The run tested the five fixes merged before it. The follow-up issues are #219 to #226. [report.md](report.md) records the evidence for each.

The 2026-11-23 wrap-up session finished the loose items; [report.md](report.md#wrap-up) records its merges, final states, and remaining decisions.
