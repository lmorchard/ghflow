# Issue #1012 delivery on the local model with the merged text, 2026-10-12

This record is in progress. It covers a delivery run of [decafclaw issue #1012](https://github.com/lmorchard/decafclaw/issues/1012) on the local Qwen model with the skill text after PRs #63 through #71 merged. It compares the run with the [issue #997 delivery](2026-10-11-issue-997-delivery.md), which supplied the source for those changes.

## Setup

Les selected the issue and chose a detached launch. The command ran from the decafclaw root:

```sh
opencode run --model llama.cpp/llama --auto --format json \
  --title "Deliver decafclaw issue 1012 with same-model review" "PROMPT"
```

`PROMPT` was the installed `SKILL.md` body, the base-directory line that OpenCode adds when a skill is invoked, and the request `deliver issue 1012 ... and use the same model for implementation and review`, the same shape as the first message of the #997 session. `--auto` approves permissions that the project configuration does not deny; in the #997 session Les approved them by hand. A new `opencode.json` in decafclaw allows external-directory reads of the skill checkout and denies edits to it, as [Setup](../../setup.md#source-access-permissions) prescribes. The installed skill clone was at `62972b3`. The model is `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on the llama server at `http://127.0.0.1:9931/v1`, with the user's configured limits. Session `ses_ed1f92953ffeCdJF1qmogA8NVm`; raw events in `/tmp/qwen-delivery/run.jsonl`.

## Timeline

| Local time | Event |
| --- | --- |
| 19:52 | Session start. The coordinator read fifteen reference files, including three task references it would only dispatch. |
| 20:15 | Coordinator finished preparation: issue read, base `cbe2442` confirmed, identity ready, board state read without a write. |
| 20:19 | First and only dispatch: one worker for implement-issue, then submit-pr for the draft, in the same session. |
| 20:24 | Worker had read all eleven files the handoff named, read the issue, confirmed the base, and checked identity. |
| 20:25 | Worktree created. |
| 20:3x | First baseline `make test` died at 84 percent with exit 129. The worker relaunched it detached, moved the board to In progress with a confirmed read-back, and created its notes file. |
| 21:24 | Tests written first and run red. Implementation followed. |
| 21:54 | Change complete in four files, formatted, lint and typecheck clean, targeted suite green at 69. Full parallel suite still dying at 84 percent. |
| 22:57 | Full suite green at four workers: 4,511 passed, 2 skipped. |
| 23:08 | Commit `aa8a448` under `MokaGnome`: four files, 99 insertions, 7 deletions, within the issue's scope. |
| 23:28 | Explicit `-n 18` run green. The worker concluded that its own concurrent suite runs caused the earlier deaths. |
| 00:26 | Still investigating why `make test` with `-n auto` dies when explicit `-n 18` passes. No push, no PR. |

## Observations so far

- **The ceremony change took.** The coordinator dispatched one worker for implementation and draft publication together. The handoff named both operations, forbade marking ready or requesting review, gave both `verify-commit` forms, the identity gate, the board transition, and the project's worktree setup. It summarized the issue rather than pasting it.
- **The coordinator still read everything first.** Fifteen files before touching the repository, including task references for operations it dispatches, against the context rule that PR #62 added. Preparation took 27 minutes, against 23 in the #997 session. On this model that rule did not change behavior.
- **The worker read the shared references this time.** The #997 worker opened only its task reference. This worker read all eleven files the handoff listed. The handoff listing them is the likely cause.
- **The worker followed the merged text closely.** Identity gate before the board write, board transition with read-back, notes file with a `Resume here` block, tests written first and run red, formatter and lint and typecheck before commit, commit under the machine account, no push before the suite was green.
- **The dominant cost was an unbounded environment investigation.** The full parallel suite died repeatedly at about 84 percent. The worker ran multiple full suites concurrently while investigating, which it later identified as the cause. It spent about two and a half hours on diagnosis after the change was complete and had a green serial run, and it continued after a green run at eighteen workers. implement-issue bounds nothing here: it says to investigate or report a baseline problem and that incomplete verification is not success. express-issue tells a coordinator to report a persisting blocker instead of cycling; no equivalent sentence exists for the worker.
- **The parallel-gate caution did not cover this case.** implement-issue warns against running an install at the same time as tests. It does not say to run one full suite at a time. The worker read the warning and overlapped three suite runs.
- **The bash tool's timeout is a runtime limit the skill does not mention.** The first baseline died when the tool call's default two-minute timeout sent a hangup to the process group. A long baseline needs a detached run or a longer tool timeout. The worker worked this out itself.

## Evidence limits

This is one run on one issue and one model. The worker's own concurrency is the likely cause of the suite deaths; the record will state the final diagnosis when the run ends. Wall-clock figures come from session timestamps and include model generation time on a shared server. The run had not reached review, ready submission, or follow-up at the time of the last entry, so it does not yet test the conditional follow-up rule or the fresh-reviewer dispatch.
