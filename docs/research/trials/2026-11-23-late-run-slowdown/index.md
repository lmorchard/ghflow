# Late-run slowdown in a local-model burndown

This record answers the question in [#224](https://github.com/lmorchard/gh-project-workflow/issues/224): does a model-server restart or a shorter phase recover the late-run throughput of a local burndown, or is the slowdown task-driven?

## Facts

- Run: the 2026-11-21 to 2026-11-22 decafclaw janitorial weekend, recorded in [PR #227](https://github.com/lmorchard/gh-project-workflow/pull/227).
- Skills: `065ae5064ae921a682fd077219ef65058370ed97`.
- Model: `lmstudio/qwen3.8-27b-mlx@4bit`.
- Runner settings: `--floor 30`, `--step-idle-timeout 900`, 150-turn session cap, and a 5400-second session limit.
- Run log: local, not committed, at `~/.local/state/ghflow/notes/runner-janitorial-20261121-1056.log`.

| Phase | Scope | Done | Time | Time per done | Limit hits |
| --- | --- | ---: | ---: | ---: | --- |
| A | Consolidation and small local work | 15 | 17.3 h | 1.15 h | none recorded |
| B | Vault split series, stacked | 5 | 8.4 h | 1.68 h | none recorded |
| C | Independent helpers | 4 | 6.6 h | 1.65 h | none recorded |
| D | Local dedupe and hoist | 2 | 3.8 h | 1.90 h | 150 turns (#1405), 5400 s (#1378) |
| E | #1438 #1422 | 1 | 1.1 h | 1.10 h | none recorded |

## Analysis

The time per done issue rose from 1.15 h in phase A to 1.90 h in phase D. Phase E returned to 1.10 h with one small task. That pattern is consistent with task mix and limit hits, but the run does not isolate the cause.

- **Task mix changed.** Phase A processed 18 small issues across several epics. Phase D processed three dedupe and hoist issues on the same file area. Phase B and C also mixed sizes. The run did not hold the task shape constant.
- **Limits cluster in the late phases.** #1378 hit the 5400-second session limit, #1405 hit the 150-turn limit, and both were in phase D. A phase that hits a limit pays for a retry or a draft checkpoint.
- **Model-server state is unrecorded.** The run log has no model load, restart, or cache event. A restart cannot be compared with a phase that had none.
- **Cached tokens were unreported.** The report states that input was 186.9M tokens and cached tokens were not reported, so the context-pressure explanation cannot be tested from that run.
- **Earlier runs are not controls.** The #1432 run delivered 7 pull requests in 7.2 h, and the #1438 trial reached 3 ready plus 1 draft in 7.8 h. Their task mixes differ.

## Decision

The one run does not show that a restart or a shorter phase recovers late-run throughput, and it does not show that the slowdown is task-driven. Do not change the runner on this evidence.

Run the controlled comparison in a future overnight run:

1. Split the run into two phases with a matched task mix, such as the same epic and size band.
2. Restart the model server between the phases, and record the restart time in the run log.
3. Keep the model, runner flags, and task shape the same across both phases.
4. Record per-phase done count, wall time, turns, input and cached tokens, largest context, and limit hits.

Until that run happens, the slowdown stays unresolved. [#224](https://github.com/lmorchard/gh-project-workflow/issues/224) needs a user decision on whether to spend a run on it.

## Evidence limits

- One run, no control, and a different task mix in each phase.
- The run log is local and not part of this repository.
- The user merged pull requests during the run; merge timing is not runner behavior.
- The review was same-model under the standing local-model exception.
- No cached-token figures were available from the run.
