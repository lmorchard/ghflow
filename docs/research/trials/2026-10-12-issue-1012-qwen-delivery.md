# Issue #1012 delivery on the local model with the merged text, 2026-10-12

This record covers a delivery run of [decafclaw issue #1012](https://github.com/lmorchard/decafclaw/issues/1012) on the local Qwen model with the skill text after PRs #63 through #71 merged. It compares the run with the [issue #997 delivery](2026-10-11-issue-997-delivery.md), which supplied the source for those changes.

## Setup

Les selected the issue and chose a detached launch. The command ran from the decafclaw root:

```sh
opencode run --model llama.cpp/llama --auto --format json \
  --title "Deliver decafclaw issue 1012 with same-model review" "PROMPT"
```

`PROMPT` was the installed `SKILL.md` body, the base-directory line that OpenCode adds when a skill is invoked, and the request `deliver issue 1012 ... and use the same model for implementation and review`, the same shape as the first message of the #997 session. `--auto` approves permissions that the project configuration does not deny; in the #997 session Les approved them by hand. A new `opencode.json` in decafclaw allows external-directory reads of the skill checkout and denies edits to it, as [Setup](../../setup.md#source-access-permissions) prescribes. The installed skill clone was at `62972b3`. The model is `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on the llama server at `http://127.0.0.1:9931/v1`, with the user's configured limits. Session `ses_ed1f92953ffeCdJF1qmogA8NVm`; raw events in `/tmp/qwen-delivery/run.jsonl`, which does not survive a reboot. The worker sessions remain in the OpenCode database.

## Result

[PR #1062](https://github.com/lmorchard/decafclaw/pull/1062) ended ready for review at head `eca206b`, with three hosted checks passed, the issue In review, and no merge. One code commit, `aa8a448`, holds the change: four files, 99 insertions, 7 deletions, within the issue's scope. Five notes-only commits follow it. An independent review in a fresh session covered `0088866` and found no actionable defects. The coordinator applied the conditional follow-up and stopped without an address-pr-review dispatch.

| | #997 run | #1012 run |
| --- | --- | --- |
| Wall clock | 3 h 50 min | 7 h 7 min, with the model shared by a second workload for part of the run |
| Task calls | 7 | 4, of which 3 did work |
| Coordinator preparation before first dispatch | 23 min | 27 min |
| Coordinator read task references it would dispatch | yes | yes |
| Coordinator reviewed the diff itself | yes, about 15 min | no |
| Worker read shared references | no | yes, all eleven named in the handoff |
| Implementation to draft PR | two dispatches | one worker, same session |
| Review time | 47 min | 28 min |
| Review ran new tests against the base | no | yes, in an isolated copy |
| Final follow-up dispatch | yes, with nothing pending | no, conditional rule applied |
| Dominant cost | model speed across seven dispatches | one worker's investigation of a self-inflicted test failure, then a notes-commit loop, both at roughly half throughput |

## Timeline

| Local time | Event |
| --- | --- |
| 19:52 | Session start. The coordinator read fifteen reference files, including three task references it would only dispatch. |
| 20:15 | Coordinator finished preparation: issue read, base `cbe2442` confirmed, identity ready, board state read without a write. |
| 20:19 | First dispatch: one worker for implement-issue, then submit-pr for the draft, in the same session. |
| 20:24 | Worker had read all eleven files the handoff named, read the issue, confirmed the base, and checked identity. |
| 20:25 | Worktree created. |
| 20:3x | First baseline `make test` died at 84 percent with exit 129. The worker relaunched it detached, moved the board to In progress with a confirmed read-back, and created its notes file. |
| 21:24 | Tests written first and run red. Implementation followed. |
| 21:54 | Change complete in four files, formatted, lint and typecheck clean, targeted suite green at 69. Full parallel suite still dying at 84 percent. |
| 22:57 | Full suite green at four workers: 4,511 passed, 2 skipped. |
| 23:08 | Commit `aa8a448` under `MokaGnome`. |
| 23:28 | Explicit `-n 18` run green. The worker concluded that its own concurrent suite runs caused the earlier deaths. |
| 00:26 | Still investigating why `make test` with `-n auto` dies when explicit `-n 18` passes. No push, no PR. |
| 00:49 | Worker moved on without intervention: PR search with JSON output, body file in the notes directory, push under the machine account, `verify-commit --on` for `aa8a448`. |
| 00:50 | Draft PR #1062 by `MokaGnome` at head `aa8a448`. The body states the problem, the resulting behavior, four tests with the red run named, the full suite green at `-n 0`, `-n 4`, `-n 18`, and `-n auto`, and the suite deaths as a pre-existing local flake reproduced on the base commit. |
| 01:05 | Hosted CI green on `0f03da8`, including the required `lint-and-test`, which confirmed the suite deaths as local. |
| 01:08 to 01:18 | Three notes-only commits, `0f03da8`, `411946b`, and `0088866`. Each recorded the CI result or the head in the notes, which moved the head and restarted the wait for CI on it. The worker named the loop itself and made the resume pointer "robust to head moves" in the last one. |
| 01:29 | Worker returned after 5 hours 10 minutes. Its report named the PR and its state, worktree, branch, base, the four commits with the revision each check covers, both `verify-commit` results, the board transition with read-back values, the model identity with its evidence limit, a success-condition table with the red run named, and `make test` as environment-limited with exact counts: thirteen full-suite runs, eight dead at 84 percent including two on the unmodified base, five green. |
| 01:33 | Reviewer dispatched in a fresh session. Between the worker's return and this dispatch the coordinator made one call, a todo update; it did not read the diff. The handoff gave read-only limits, the issue and PR, base and expected head, `pr-state` and `verify-commit --pr-head`, the worktree with a head check before reading the diff, and the same-model exception as a user approval. |
| 02:01 | Reviewer returned after 28 minutes. Head verified with `verify-commit --pr-head` and re-confirmed at the end. Model identities with their evidence limit. No actionable defects; one nit labeled a preference. All five callers traced, 330 caller and registry tests run, the new tests run against the base in a detached temporary worktree and shown to discriminate, a not-tested list, and `pr-state` comments read as an empty list before stating that no feedback existed. |
| 02:04 | Ready submission dispatched to a new session instead of resuming the implementation worker. The call's prompt was the eleven-character word "placeholder", against 8,509 and 5,720 characters for the first two dispatches. The worker answered with a greeting and the task closed with the PR still a draft. A malformed tool call by the model. |
| 02:2x | The coordinator named the malformed dispatch and the missing resume id itself and resumed the implementation worker in its original session. The worker read its notes, ran `pr-state`, confirmed the reviewed head, then recorded the review outcome in the notes, committed, and pushed `61fc1be`, moving the PR head past the reviewed head before marking it ready. |
| 02:37 | PR marked ready at `61fc1be` after CI went green on it. `pr-state`: all three checks passed, no review requests, no reviews, no comments. |
| 02:45 | Board In review. A sixth commit, `eca206b`, recorded the ready read-backs in the notes and moved the head again. |
| 02:54 | Worker returned with the ready report: ready state read back after a separate `gh pr ready`, `verify-commit --pr-head` at `61fc1be`, board In progress to In review with `before`, `after`, `added`, and `readback_matches`, `pr-state` green on the final head, the body file path, and the head move after verification stated as a limit. |
| 02:59 | The coordinator applied the conditional follow-up: "all hosted checks passed on the current head `eca206b`, no requested or pending reviews, no unresolved findings. That read-back is the final follow-up evidence — the flow stops here with the PR open." No address-pr-review dispatch. |
| 03:00 | Final report to the user: PR, issue and board state, the change, test and CI evidence, review coverage with the notes-only delta named, the same-model identity limit, the environment flake, and the merge gate left with Les. |

## What the merged text changed

- **One worker carried implementation and draft publication.** The handoff named both operations, forbade marking ready or requesting review, gave both `verify-commit` forms, the identity gate, the board transition, and the project's worktree setup. The #997 run used separate dispatches for these.
- **The coordinator did not review the diff.** Between the worker's return and the reviewer dispatch it made one call. The #997 coordinator spent about fifteen minutes on its own diff review at the same point.
- **The reviewer ran the new tests against the pre-fix code.** It created a detached temporary worktree, ran the new test class against the base's code, saw the count-only test fail with the old warning and the protected tests pass, removed the worktree, and ran the callers' tests. The #997 reviewer did not do this, and the #997 implementer's tests passed on a dead code path.
- **The reviewer read the PR comments before saying there were none.** `pr-state` returned an empty list and the report said so.
- **The follow-up dispatch did not happen.** The coordinator read the ready report against the three conditions and stopped.
- **The worker read the shared references.** All eleven that the handoff listed, against none in the #997 run.
- **The coordinator recovered from its own malformed dispatch.** It named the placeholder prompt and the missing resume id and resumed the correct session.

## What did not change or got worse

- **The coordinator still read everything first.** Fifteen files before touching the repository, including task references for operations it dispatches, against the context rule that PR #62 added. Preparation took 27 minutes. On this model that rule did not change behavior.
- **An unbounded environment investigation dominated the run.** The full parallel suite died repeatedly at about 84 percent. The worker ran several full suites concurrently while investigating, which it later identified as the cause. It spent about two and a half hours on diagnosis after the change was complete and had a green serial run, and continued after a green run at eighteen workers. implement-issue says to investigate or report a baseline problem and that incomplete verification is not success; express-issue tells a coordinator to report a persisting blocker instead of cycling; no equivalent bound exists for the worker.
- **The parallel-gate caution did not cover this case.** implement-issue warns against running an install at the same time as tests. It does not say to run one full suite at a time.
- **Committed notes that cite the head created a loop.** The project commits session notes. The worker recorded CI results and heads in the notes five times, each commit moving the head and restarting CI, and the last two moved the head past the reviewed commit before and after marking the PR ready. Notes that name the commit they are committed in cannot be exact.
- **The ready step first went to a new session with a placeholder prompt.** A model fault; the skill text had asked for the implementation worker to be resumed.
- **The bash tool's timeout is a runtime limit the skill does not mention.** The first baseline died when the tool call's default two-minute timeout sent a hangup to the process group. A long baseline needs a detached run or a longer tool timeout.

## Candidate changes

1. implement-issue: bound the investigation of a verification-environment failure. When the change is complete and a full run is green in any configuration, report the failing configuration as an environment limit with the run counts and hand off; hosted CI settles it.
2. implement-issue: run one full suite at a time; name concurrent suite runs, not only installs, as a cause of false failures.
3. task-notes or pr-lifecycle: when the project commits notes, record the code commit and the CI it covers, not the notes commit; publish notes once at the end of an operation without waiting for CI on them; do not move the head after the reviewed commit for notes alone before marking ready.
4. context: the "do not pre-load future procedures" rule has no effect on this model; either accept the cost or state it in the coordinator's own task reference where the model reads it.
5. docs/setup: name the bash tool timeout as an OpenCode runtime limit for long baselines.

## Evidence limits

This is one run on one issue and one model. The worker's own concurrency is the established cause of most suite deaths, by its own `-n 18` and `-n auto` results and by hosted CI; the first death on the unmodified base is attributable to the tool timeout. Wall-clock figures come from session timestamps and include model generation on a shared server. Les reports that a second workload was making requests to the same llama server during this run, which roughly halves the tokens per second available to each. The wall-clock total and the per-step durations are therefore not comparable to the #997 run, which had the server to itself; the dispatch count, the decisions, and the order of events are unaffected. The run did not exercise the correction cycle, because the review found no defects, so it does not test the resumed-worker correction path. The comparison with #997 is between different issues of similar size, not a controlled repeat.
