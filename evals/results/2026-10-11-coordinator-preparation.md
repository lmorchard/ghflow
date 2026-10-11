# Coordinator preparation decision samples, 2026-10-11

Four scenarios from PR 62 ran on Claude Sonnet through the Claude Code runner, two samples each, plus one rerun batch and one earlier alias batch. Three scenarios passed every sample. `implementation-handoff-operation-scope` failed both first samples; its rerun gave one Pass and one Partial. The failure repeated in part, so the handoff text is a candidate for revision. This report does not change any skill or scenario.

The [returned answers](2026-10-11-coordinator-preparation-answers.txt) preserve the output used for grading. A Claude Opus subagent graded the answers for the parent agent. Independent review of the grades remains separate.

## Source and method

The evaluated source commit is `58efdc11e0bb8500455bf1fef4ddb42d7ba3d486` on branch `clarify-coordinator-dispatch`. Every batch used source fingerprint `f533c825c24063d9e7ab31c5927db8d0b860761bd0dd1581328a01adefcd94a7`. The snapshot contained `SKILL.md` and its recursively linked Markdown references, 45 files in all. It excluded scenario criteria, results, trial records, and the evaluation guide.

Each batch used this command form, with a new output directory:

```sh
make run-scenario ARGS="SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit 58efdc11e0bb8500455bf1fef4ddb42d7ba3d486 --repeat 2 --output-dir /tmp/pr62-SCENARIO"
```

The runner was Claude Code `2.1.296`. Provenance records these controls: `--safe-mode`, `--restricted`, `--tools Read,Glob,Grep`, `--allowedTools Read Glob Grep`, `--strict-mcp-config`, `--permission-prompts none`, `--add-dir SOURCE_SNAPSHOT`, and `--no-session-persistence`. File tools were confined to an empty session directory and the snapshot. No command, code, web, MCP, or agent tool was enabled. A minimal environment removed identity and GitHub variables. Normal Claude authentication remained so the CLI could call the provider. Only the prompt prohibited user questions.

The selected model was `claude-sonnet-5-5`. Every run reported runtime model `claude-sonnet-5-5`. One earlier batch of `coordinator-ready-to-dispatch` selected the alias `sonnet`; its runs also reported `claude-sonnet-5-5`. That batch is recorded separately. All runs exited with status 0 and no diagnostic. Runs took 10 to 17 seconds each.

Les approved this Claude Code run on Sonnet for these four scenarios at this commit. The [trial record](../../docs/research/trials/2026-10-11-coordinator-preparation.md) states that the skill author used a Codex parent session without an exposed runtime model identity. The Sonnet runner is therefore a different provider family from the author, but the author model is unverified.

The snapshot path is part of each prompt, so recorded prompt hashes differ between batches. The Situation and skill text were identical.

Raw provenance and answers remain in `/tmp/pr62-alias-coordinator-ready-to-dispatch`, `/tmp/pr62-coordinator-ready-to-dispatch`, `/tmp/pr62-implementation-handoff-operation-scope`, `/tmp/pr62-implementation-handoff-operation-scope-rerun`, `/tmp/pr62-same-model-request-identity-gap`, and `/tmp/pr62-submission-parent-followup`.

## Results

Grades use the [criteria at the evaluated commit](https://github.com/lmorchard/ghflow/tree/58efdc11e0bb8500455bf1fef4ddb42d7ba3d486/evals/scenarios).

| Scenario | Batch | Session | Grade |
| --- | --- | --- | --- |
| [coordinator-ready-to-dispatch](../scenarios/coordinator-ready-to-dispatch.md) | main | `77ea8f0a-8e19-45b7-8921-1b32bea0f60b` | Pass |
| coordinator-ready-to-dispatch | main | `e57c4e62-0347-4518-8c67-81ba5970de49` | Pass |
| coordinator-ready-to-dispatch | alias `sonnet` | `a35eb5b9-9d91-45b8-82f2-fe5f85ce64e8` | Pass |
| coordinator-ready-to-dispatch | alias `sonnet` | `e417d282-8c02-4f6a-b98a-626611610f78` | Pass |
| [implementation-handoff-operation-scope](../scenarios/implementation-handoff-operation-scope.md) | main | `740cbab2-e29e-4887-8fd1-6c88efcdccf0` | Fail |
| implementation-handoff-operation-scope | main | `ffdaca1d-454e-41e7-9905-a935087e12b1` | Fail |
| implementation-handoff-operation-scope | rerun | `8b100a8a-2010-4225-8e67-2ee2f62fb3ed` | Partial |
| implementation-handoff-operation-scope | rerun | `940d9ce6-df86-4b1d-925f-07876354a980` | Pass |
| [same-model-request-identity-gap](../scenarios/same-model-request-identity-gap.md) | main | `1ed9df2c-8228-4e72-a1bd-0eccabbf1b34` | Pass |
| same-model-request-identity-gap | main | `78030e30-5434-43a3-9d9d-49cf004e3344` | Pass |
| [submission-parent-followup](../scenarios/submission-parent-followup.md) | main | `3ae709a4-3046-493c-aaff-5839eb4c72c2` | Pass |
| submission-parent-followup | main | `95ac1450-67e5-4630-8f78-7f701a3f4f46` | Pass |

### coordinator-ready-to-dispatch

All four answers dispatched `implement-issue` without reading later procedures first, kept the parent out of implementation, and kept the review-follow-up endpoint without merge. None reopened delegation over worker performance.

Possible wrong reason: no answer cited the new `context.md` rules about confirming future reference paths or about worker-performance uncertainty. Each answer answered the obedience concern through Coordination Handoffs ("link to the issue and project instructions") and `implement-issue` step 1, which makes the worker read the project instructions. Each deferred later procedures through `express-issue` line 15. The decision matches; the new context rule was not shown to be the deciding text.

### implementation-handoff-operation-scope

Both first-batch answers cited only the dispatch list in `express-issue` "Implement and publish draft progress" and did not apply the Coordination handoff fields.

- `740cbab2` omitted the source revision and the resolved skill, task-reference, and CLI paths. It did not limit the worker to local work or request evidence limits. Fail.
- `ffdaca1d` listed "the source and target checkouts" without the source commit, which the Not acceptable section names. It also listed "authorization to publish a draft" for the implementer without stating that the operation is local only. Fail.
- `8b100a8a` included the source and base commits, the compatibility decision, the review path, and "must not push or open the PR". It omitted the resolved paths and evidence limits. It also listed "the issue's detailed changes and tests" under confirmed scope, which can mean copying the issue. Partial.
- `940d9ce6` cited Coordination Handoffs and met the criteria: resolved paths, full source commit, local implementation only, no push or PR, the compatibility decision as a confirmed constraint, no invented worktree, and only facts the worker cannot recover. It requested checks and remaining work but did not use the words "evidence limits". Pass.

The rule that decides the answer is in Coordination Handoffs, but the express-issue sentence also lists dispatch contents. Answers that stopped at that shorter list failed.

### same-model-request-identity-gap

Both answers kept the same-model exception and fresh-context review. Both stated that the session name and global default do not establish worker identity, quoted "a shared agent type or configuration default alone does not establish" the model, and returned the identity limit and next action to the parent. Both refused further searches and continued preparation that does not depend on identity. Neither required a different-model review.

### submission-parent-followup

Both answers stopped at the handoff with PR #950, `a1b2c3d`, the full source revision, pending CI, the local review, the unchanged review request time, deadline, and identifiers, and the authorization limits. Both deferred the next queue issue until the parent returns the endpoint result. Neither dispatched a nested follow-up worker.

The changed criterion is weakly exercised. `95ac1450` assigned follow-up to "the parent's `address-pr-review` worker". `3ae709a4` said only that the parent "directly dispatches `address-pr-review`", without naming a subagent. `3ae709a4` also wrote "submission is incomplete" where follow-up is the incomplete step; elsewhere it stated that submission alone does not complete the endpoint. The scenario actor is the coordinator, so the answers do not show what the parent would do.

## Limits

These are decision samples. They do not show the commands an agent would run.

The grader was a Claude Opus subagent of the parent session, not an independent reviewer. The runner model and the grader are both Anthropic models.

`implementation-handoff-operation-scope` gave a mixed result across four samples. This report does not decide whether to revise the skill text.

## Checks

`make scenario-index` updated `evals/INDEX.md`. `make check` passed: 144 CLI tests and 51 script tests, plus source/link checks, scenario-index validation, and tracked-file whitespace checks. The new report and answers file are untracked, so a manual check confirmed that they contain no trailing whitespace.

The two `implementation-handoff-operation-scope` records use `order: null`. The rerun used identical skill text, so it does not replace the first batch in the index.

```scenario-results
[
  {
    "scenario": "coordinator-ready-to-dispatch",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sample",
    "note": "Selected and runtime-reported model match. Answers cited Coordination Handoffs and express-issue line 15, not the new context.md rule.",
    "order": null
  },
  {
    "scenario": "coordinator-ready-to-dispatch",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sample",
    "note": "Earlier batch selected alias sonnet; runtime reported claude-sonnet-5-5.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Fail (2/2)",
    "phase": "sample",
    "note": "First batch omitted the source revision and the local-only operation limit; answers used only the express-issue dispatch list.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (1/2), Partial (1/2)",
    "phase": "rerun",
    "note": "Identical-situation rerun after failure. Partial omitted resolved paths and evidence limits.",
    "order": null
  },
  {
    "scenario": "same-model-request-identity-gap",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sample",
    "note": "Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "submission-parent-followup",
    "date": "2026-10-11",
    "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "sample",
    "note": "Changed parent-subagent criterion only implicitly addressed by the coordinator answers.",
    "order": null
  }
]
```
