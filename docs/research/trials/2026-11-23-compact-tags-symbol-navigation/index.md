# Compact tags on a symbol-navigation task

This record answers the question in [#225](https://github.com/lmorchard/gh-project-workflow/issues/225): do the compact tags reduce input tokens or context on the same symbol-navigation task?

## Method

- Checkout: this repository at `129600aa76`, the main working tree used for both arms.
- Runtime: OpenCode 2.2.5 with `--standalone --auto --format json`.
- Model: `lmstudio/qwen3.8-27b-mlx@4bit`.
- Task: find the definition of `pr_ready`, every call site, and the runner function that reaches it from the deterministic `submit-pr` step. Return the call chain with file and line numbers. Read-only.
- Arm 1 (no tags): use grep and read. Do not run `tags` or the ghflow CLI.
- Arm 2 (compact tags): run `tags brief pr_ready`, `tags find pr_ready --refs`, and `tags outline cli/ghflow.py` before grep or a full read. Use grep or a read only when a tag result is insufficient.
- Before arm 2, `tags generate` refreshed the index. Both arms used the same checkout and index.
- The same prompt supplied the same task to both arms. Arm 1 ran first, then arm 2.
- Tools counted: the `grep` and `read` tools in arm 1; the `shell` calls that ran `tags` and the `grep` and `read` tools in arm 2.
- Tokens come from each `step_finish` event. Input is the sum of step input. Cached tokens are the sum of `cache.read` and `cache.write`. Final context is the last step's input plus cached tokens.

## Result

| Metric | No tags | Compact tags | Change |
| --- | ---: | ---: | ---: |
| Input tokens | 189,755 | 159,901 | -29,854 (-15.7%) |
| Cached read tokens | 0 | 0 | 0 |
| Cached write tokens | 0 | 0 | 0 |
| Turns | 8 | 9 | +1 |
| Final context tokens | 29,837 | 24,348 | -5,489 (-18.4%) |
| Output tokens | 1,849 | 1,444 | -405 (-21.9%) |
| Reasoning tokens | 3,186 | 2,014 | -1,172 (-36.8%) |
| Tool calls | 14 (grep 9, read 5) | 9 (tags 3, grep 2, read 4) | -5 |
| Wall clock | 5 min 44 s | 3 min 20 s | -2 min 24 s |

Both arms returned the definition at `cli/ghflow.py:1211`, the production call at `cli/ghflow.py:4671`, and the runner chain `run_queue.main` → `execute_submit_pr` → `run_cli` → `ghflow.main` → `pr_ready`.

The compact arm used one more turn and still used two grep calls and four reads. It reported the import and the two direct test calls, but not the two `unittest.mock.patch` references to `ghflow.pr_ready` at `cli/test_ghflow.py:2811` and `:2815` that the no-tags arm listed. Those are patch targets, not direct calls.

## Decision

Keep the compact-tags guidance for symbol navigation. No code change follows from this trial. On this task the tags arm used 15.7% fewer input tokens and 18.4% less final context, with one more turn. The compact tags did not remove all grep and read use, and the cache effect is unmeasured because both arms reported zero cached tokens.

This result is one task with one run per arm. It supports the current instruction to try `tags brief` before grep, not a claim that every navigation task saves tokens.

## Evidence limits

- One task and one run per arm, so variance and order effects are unknown. Arm 1 ran first.
- Both arms used the same model server without a restart. The baseline probe before arm 1 and the sequential runs could affect wall time.
- The runtime reports cache fields, but both arms show zero cached tokens. A cached-token saving cannot be measured from this run.
- The checkout `129600a` is not the latest main. It was the working copy at the time of both arms; the tags CLI and the task code are from that revision.
- The answer quality was checked by hand against the files, not by an automated oracle.
- No coverage or repeated run was measured.
