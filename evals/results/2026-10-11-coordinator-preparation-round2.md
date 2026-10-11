# Coordinator preparation round 2, 2026-10-11

Two scenarios from PR 62 ran on Claude Sonnet through the Claude Code runner, two samples each. The runs used the revised `express-issue` dispatch line and `context.md` sentence. All four answers passed. `implementation-handoff-operation-scope` passed 2/2, where the [earlier run at `58efdc1`](2026-10-11-coordinator-preparation.md) failed 2/2 and then gave one Pass and one Partial on rerun. No answer failed, so no rerun was needed. This report does not change any skill or scenario.

The [returned answers](2026-10-11-coordinator-preparation-round2-answers.txt) preserve the output used for grading. A Claude Opus subagent of the parent session graded the answers. Independent review of the grades remains separate.

## Source and method

The evaluated source commit is `066cb277f3dd540fd3eb21fb9be56f6219f87ef3` on branch `clarify-coordinator-dispatch`. That commit changes two lines from `58efdc1`:

- `references/tasks/express-issue.md`, "Implement and publish draft progress": the `implement-issue` dispatch now points to [Handoffs](../../references/shared/coordination.md#handoffs) for its contents and names the source revision and the local-only limit.
- `references/shared/context.md`: adds "An operation becomes relevant when you prepare its dispatch."

Both batches used source fingerprint `009815e67582e0b8aaa6b38740dc3ae9e50ae427571e79641be8752c23860ed0`. The snapshot contained `SKILL.md` and its recursively linked Markdown references, 45 files in all. It excluded scenario criteria, results, trial records, and the evaluation guide.

Each batch used this command form, with a new output directory:

```sh
make run-scenario ARGS="SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit 066cb277f3dd540fd3eb21fb9be56f6219f87ef3 --repeat 2 --output-dir /tmp/pr62-round2-SCENARIO"
```

The runner was Claude Code `2.1.296`. Provenance records these controls: `--safe-mode`, `--restricted`, `--tools Read,Glob,Grep`, `--allowedTools Read Glob Grep`, `--strict-mcp-config`, `--permission-prompts none`, `--add-dir SOURCE_SNAPSHOT`, and `--no-session-persistence`. File tools were confined to an empty session directory and the snapshot. No command, code, web, MCP, or agent tool was enabled. A minimal environment removed identity and GitHub variables. Normal Claude authentication remained so the CLI could call the provider. Only the prompt prohibited user questions.

The selected model was `claude-sonnet-5-5`, and every run reported runtime model `claude-sonnet-5-5`. All runs exited with status 0 and no diagnostic. Runs took 10 to 16 seconds each. Both batches ran at the same time, with start times of 2026-10-11T18:59:11Z.

Les approved this Claude Code run on Sonnet for these two scenarios at this commit. The parent agent, a Claude session, wrote the two skill edits. The runner model is therefore from the same provider family as the author of these edits.

Raw provenance and answers remain in `/tmp/pr62-round2-implementation-handoff-operation-scope` and `/tmp/pr62-round2-coordinator-ready-to-dispatch`.

## Results

Grades use the [criteria at the evaluated commit](https://github.com/lmorchard/ghflow/tree/066cb277f3dd540fd3eb21fb9be56f6219f87ef3/evals/scenarios). The criteria did not change from `58efdc1`.

| Scenario | Session | Grade |
| --- | --- | --- |
| [implementation-handoff-operation-scope](../scenarios/implementation-handoff-operation-scope.md) | `0a6b2b13-3b3e-42dd-aa29-d026db2a82e5` | Pass |
| implementation-handoff-operation-scope | `379d842a-06a9-4a15-acef-69f75bacec8f` | Pass |
| [coordinator-ready-to-dispatch](../scenarios/coordinator-ready-to-dispatch.md) | `9b1f67a4-e197-400d-a921-dedff5acfc9e` | Pass |
| coordinator-ready-to-dispatch | `816e675f-cc5e-4c0a-8862-79a0deddf096` | Pass |

### implementation-handoff-operation-scope

Both answers followed Coordination Handoffs through the revised dispatch line. `0a6b2b13` wrote: "The handoff follows the Handoffs section of coordination.md." `379d842a` named "the `coordination.md#handoffs` form" and gave the revised line as the deciding rule.

- `0a6b2b13` gave the resolved skill, task-reference, and CLI paths, "the full source commit used for instructions and tools", the issue URL, target checkout, project instructions path, and base commit. It stated the compatibility decision explicitly because "The worker can't recover this from the issue text". It linked the issue instead of copying its changes and tests. It said "This operation is local implementation only" and "The dispatch is local-only, with no push and no PR." It requested "the actual results, evidence limits, and local base and head verification", and it omitted existing-work fields because no worktree exists. Pass.
- `379d842a` gave the same paths, source commit, subject, base, compatibility decision, review plan, and flow authorization. It wrote "local implementation only, with no push and no PR" and linked the issue for detailed changes and tests. It requested "the checks run, local base/head verification, and remaining work" but did not ask for evidence limits by that name. It listed "the task-notes path, if one exists" as a conditional field; it did not invent a notes path. Pass, with the same omission as the passing rerun answer `940d9ce6` at `58efdc1`.

Comparison with `58efdc1`: The two failing answers there used only the short field list in the old dispatch line. They omitted the source revision, the resolved paths, and the local-only limit. In this round, both answers included all three. Four samples at `58efdc1` gave one Pass, one Partial, and two Fails. Two samples at `066cb27` gave two Passes. The change is consistent with the express-issue edit fixing the failure, but two samples do not prove it.

The evidence-limits request is still not stable. One of two answers here and one of two passing answers earlier left it out. The revised dispatch line names other Handoffs fields, but it does not name the return request.

### coordinator-ready-to-dispatch

Both answers dispatched `implement-issue` without reading later procedures first. Both kept the parent out of implementation and kept the review-follow-up endpoint without merge. Neither reopened delegation over worker performance. Both listed the source revision and the local-only limit in the handoff, which several answers at `58efdc1` also did.

Possible wrong reason, as at `58efdc1`: neither answer cited `context.md`. Both answered the obedience concern through Coordination Handoffs ("Link to the issue and project instructions instead of copying their procedures") and `implement-issue` step 1. Both deferred later procedures through `express-issue.md:15` ("I'll read each one when its stage starts"). `9b1f67a4` also cited the Coordination rule "Do not do the subject-repository work in the parent instead" as its reason not to take the work over. The context.md sentence about uncertainty in worker performance was not shown to be the deciding text.

### context.md edit

These scenarios do not test the new `context.md` sentence directly. In `coordinator-ready-to-dispatch`, the Situation says the agent has already read the implementation reference. In `implementation-handoff-operation-scope`, neither answer cited `implement-issue.md`. The Claude Code runner does not record read paths, so this report cannot show whether the agent read that file before it wrote the handoff. The regression answer that motivated the edit came from a different scenario, and that scenario was not rerun.

## Limits

These are decision samples. They do not show the commands an agent would run.

Each scenario had two samples. The grader was a Claude Opus subagent of the parent session, not an independent reviewer. The runner, the grader, and the author of the edits all use Anthropic models.

The regression sample was not rerun at `066cb27`.

## Checks

`make scenario-index` updated `evals/INDEX.md`. `make check` passed.

```scenario-results
[
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "066cb277f3dd540fd3eb21fb9be56f6219f87ef3",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "After express-issue dispatch line pointed to Coordination Handoffs. Both answers included source revision, resolved paths, and local-only limit; one omitted the evidence-limits request. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "coordinator-ready-to-dispatch",
    "date": "2026-10-11",
    "skill_commit": "066cb277f3dd540fd3eb21fb9be56f6219f87ef3",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "Answers cited Coordination Handoffs and express-issue line 15, not context.md. Selected and runtime-reported model match.",
    "order": null
  }
]
```
