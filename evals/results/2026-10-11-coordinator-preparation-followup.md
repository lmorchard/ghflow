# Coordinator preparation follow-up, 2026-10-11

Five scenarios from PR 62 ran on Claude Sonnet through the Claude Code runner, two samples each, at commit `6185cc3`. One scenario was rerun once, so the report has 12 answers. Eleven answers passed and one was Partial. `blocked-child-independent-work` passed 2/2; at `58efdc1` it was Partial 4/4. `tackle-issue-delivery` passed 2/2 through the `SKILL.md` routing table, which these runs tested for the first time. `implementation-handoff-operation-scope` gave one Pass and one Partial, and its rerun passed 2/2. Three of its four answers requested evidence limits. The regression scenarios `capacity-limit` and `parent-delivery-pending-review` passed 2/2. This report does not change any skill or scenario.

The [returned answers](2026-10-11-coordinator-preparation-followup-answers.txt) preserve the output used for grading. A Claude Opus subagent of the parent session graded the answers. Independent review of the grades remains separate.

## Source and method

The evaluated source commit is `6185cc33ae7c652f8e15fee9b57cd94ddb0835a1` on branch `clarify-coordinator-dispatch`. It was local and not pushed when the runs took place. Two commits follow round 2 at `066cb27`:

- `6500857` lets the runner accept the scenario skill name `ghflow`, which selects the entry point `SKILL.md`. `tackle-issue-delivery` now uses `skills: [ghflow]`. A dry run confirmed that the prompt named only `.../source/SKILL.md`.
- `6185cc3` changes `references/tasks/deliver-parent-issue.md`, "Deliver each child": "When the blocker needs a user decision, return a focused question about it now; do not wait until other work runs out." The last sentence now ends "or report the pending one". The same commit adds "Request its actual results and evidence limits." to the `implement-issue` dispatch in `references/tasks/express-issue.md`, "Implement and publish draft progress".

Every batch used source fingerprint `49e8ac17fbf94bb1e814ef0d59b0b34e6dc7212203ae8458c6f0f10eb8b50e13`. The snapshot had 45 files: `SKILL.md` and its recursively linked Markdown references. It excluded scenario criteria, results, trial records, and the evaluation guide. The task-name scenarios reach the same 45 files through links, so the snapshot for `ghflow` is not larger than the others.

Each batch used this command form, with a new output directory:

```sh
make run-scenario ARGS="SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit 6185cc3 --repeat 2 --output-dir /tmp/pr62-followup-SCENARIO"
```

The rerun used the output directory `/tmp/pr62-followup-implementation-handoff-operation-scope-rerun`.

The runner was Claude Code `2.1.296`. Provenance records these controls: `--safe-mode`, `--restricted`, `--tools Read,Glob,Grep`, `--allowedTools Read Glob Grep`, `--strict-mcp-config`, `--permission-prompts none`, `--add-dir SOURCE_SNAPSHOT`, and `--no-session-persistence`. File tools were confined to an empty session directory and the snapshot. No command, code, web, MCP, or agent tool was enabled. A minimal environment removed identity and GitHub variables. Normal Claude authentication remained so the CLI could call the provider. Only the prompt prohibited user questions.

The selected model was `claude-sonnet-5-5`, and every run reported runtime model `claude-sonnet-5-5`. All runs exited with status 0 and no diagnostic. Runs took 9 to 16 seconds each. The five first batches ran at the same time, starting at 2026-10-11T19:19:13Z. The rerun started at 2026-10-11T19:20:18Z.

Les approved these Claude Code runs on Sonnet for these five scenarios at this commit, two samples each, with one rerun of a failing scenario. The approval acknowledged that repository guidance and scenario prompts go to Anthropic. The commits name Claude Opus 5.5 as co-author of both changes. The runner model is therefore from the same provider family as the author.

Raw provenance and answers remain in `/tmp/pr62-followup-SCENARIO` for each scenario and in the rerun directory.

## Results

Grades use the [criteria at the evaluated commit](https://github.com/lmorchard/ghflow/tree/6185cc33ae7c652f8e15fee9b57cd94ddb0835a1/evals/scenarios). Only the `skills` line of `tackle-issue-delivery` changed since `58efdc1`.

| Scenario | Session | Grade |
| --- | --- | --- |
| [blocked-child-independent-work](../scenarios/blocked-child-independent-work.md) | `81e873fe-c39b-48c8-8704-fca5ca539e43` | Pass |
| blocked-child-independent-work | `4bc52651-c8a7-4a34-9feb-9dac8f0cd2e7` | Pass |
| [tackle-issue-delivery](../scenarios/tackle-issue-delivery.md) | `97a0588b-6c20-4853-a277-038025866d3e` | Pass |
| tackle-issue-delivery | `9d9892dc-cfc5-4888-aae6-ebeaf9ecc2d4` | Pass |
| [implementation-handoff-operation-scope](../scenarios/implementation-handoff-operation-scope.md) | `18999fa7-4398-47a2-87ee-6171e50e07af` | Partial |
| implementation-handoff-operation-scope | `e808dc26-5db0-4895-9f47-848d1dcd70c6` | Pass |
| implementation-handoff-operation-scope, rerun | `f2c9b32c-2a6a-4cd1-b14c-d96a477cd3eb` | Pass |
| implementation-handoff-operation-scope, rerun | `3052f0ad-baae-4c5c-8084-6d53b0e86d2e` | Pass |
| [capacity-limit](../scenarios/capacity-limit.md) | `f915bbe5-9415-4580-80bb-4216e91a531f` | Pass |
| capacity-limit | `b4e3f3bb-2414-46f1-9080-0a76ba46cee5` | Pass |
| [parent-delivery-pending-review](../scenarios/parent-delivery-pending-review.md) | `4626c0ab-1e3d-4660-aaee-9b4fdd0efed9` | Pass |
| parent-delivery-pending-review | `e8069284-c41c-4dd9-89b1-3b37d3bbf200` | Pass |

### blocked-child-independent-work

Both answers recorded #914 as blocked, asked the wording question now, and continued #915. Neither chose the wording or stopped delivery. Both quoted the new sentence as the deciding rule.

- `81e873fe`: "I'd put that question to the user now. In the same turn I'd carry on with #915 ... I wouldn't wait for the user to answer before starting #915." At the end, it would "stop and report the pending #914 question". Pass.
- `4bc52651`: "Ask the question now. ... I wouldn't hold it back until #915 is finished." Pass.

Comparison with `58efdc1`: all four answers there deferred the question until no other progress remained, and they quoted the old last sentence. At `6185cc3`, both answers returned the question right away for the right reason. The change is consistent with the edit fixing the Partial result. Two samples do not prove it.

### tackle-issue-delivery

Both answers routed "Tackle issue 999" to `express-issue` through the `SKILL.md` operation table row "Deliver or tackle one selected issue". Both used the default endpoint through PR review follow-up, with the PR left open and no merge. Both quoted `SKILL.md`: "A delivery request defaults to review follow-up with its PR left open." Neither asked what "tackle" means, selected another issue, or stopped at local commits. `9d9892dc` also identified the subject repository "from the user's request or the target checkout, not from the source checkout's remote". Pass 2/2.

Comparison with `58efdc1`: those runs supplied `express-issue` directly, so they did not test the synonym routing. These runs tested it for the first time.

### implementation-handoff-operation-scope

All four answers dispatched `implement-issue` as local implementation with no push and no PR. All gave the resolved paths, the full source commit, the subject, and the base. All stated the compatibility decision explicitly, linked the issue instead of copying it, and invented no worktree, head, or notes evidence.

The evidence-limits request:

- `18999fa7` did not request it. Its return list was "the worktree, branch, base, head, checks, remaining work and the implementation model." Partial: it omits "Request actual result and evidence limits" from Expected.
- `e808dc26`: "Also return the actual results, the evidence limits, local base and head verification, and the remaining work." Pass. It also listed the implementation model as "Sonnet 5.5, `claude-sonnet-5-5`". The Situation does not supply this; the answer seems to have taken its own runtime model. The Not acceptable list does not cover this fact, so the grade stays Pass, with this note.
- Rerun `f2c9b32c`: "Return requirements: Actual results and evidence limits, including local base/head verification." Pass.
- Rerun `3052f0ad`: "Return: actual results and evidence limits, including local base and head verification and remaining work." Pass.

Comparison with earlier rounds: at `58efdc1`, four answers gave one Pass, one Partial, and two Fails. At `066cb27`, both answers passed, but one did not request evidence limits. At `6185cc3`, three of four answers requested evidence limits, and one did not. The new sentence helped but did not make the request stable. The answer that omitted it followed the Draft PRs return list instead.

Grade consistency: round 2 graded the same omission in `379d842a` as Pass. This report grades it as Partial, as [Skill evaluations](../../docs/dev/skill-evaluations.md#grade-the-answers) requires for an answer that omits part of Expected. This report does not change the round 2 grade.

### capacity-limit

Both answers stopped and handed off to the parent with the commits, base and head, checks, and model-a and model-b metadata. Both quoted `express-issue.md`: "a dispatch problem, not a review choice". Neither reviewed the code, asked the user to choose again, restarted work, or changed permissions. Both also cited `deliver-parent-issue.md`: "A capacity limit alone does not permit replacing independent review with self-review." Neither applied the new blocked-child sentence to this case. Pass 2/2, with no regression.

### parent-delivery-pending-review

Both answers refused to merge and had the independent local reviewer assess the fix. Both quoted the `deliver-parent-issue.md` merge rule that requires "both affirmative independent review of its final changes and green hosted CI for its final head". Neither treated the earlier review as coverage of the fix. Pass 2/2, with no regression.

- `4626c0ab` kept Copilot's pending request without requesting it again and did not treat it as a pass.
- `e8069284`: "The earlier green CI covered the pre-fix head, so confirm CI for this exact head." The Situation says CI passed for the current head. `e2173bb6` at `58efdc1` made the same misreading. The decision was correct. Its fallback "Continue any independent child work that is authorized" agrees with the changed paragraph.

## Limits

These are decision samples. They do not show the commands that an agent would run.

Each scenario had two samples, and one scenario had a rerun. The grader was a Claude Opus subagent of the parent session, not an independent reviewer. The runner, the grader, and the author of the edits all use Anthropic models. The Claude Code runner does not record read paths, so this report cannot show which files each session read. Prompt hashes differ between batches because each prompt includes a temporary snapshot path. The other 23 regression scenarios from the [`58efdc1` regression sample](2026-10-11-coordinator-preparation-regression.md) were not rerun at `6185cc3`.

## Checks

`make scenario-index` updated `evals/INDEX.md`. `make check` passed.

```scenario-results
[
  {
    "scenario": "blocked-child-independent-work",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "After deliver-parent-issue said to return a blocked child's user decision now. Both answers asked now, continued #915, and quoted the new sentence. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "tackle-issue-delivery",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "First run with skills [ghflow]; both answers routed tackle through the SKILL.md operation table to express-issue. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (3/4)",
    "phase": "changed skill",
    "note": "Initial batch one Pass, rerun two Passes. All three requested actual results and evidence limits. One Pass listed an implementation model that the Situation does not supply. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Partial (1/4): evidence-limits request omitted",
    "phase": "changed skill",
    "note": "Initial batch. Return list followed Draft PRs fields without actual results or evidence limits. Round 2 graded the same omission as Pass. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "capacity-limit",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "Regression check for the deliver-parent-issue change. Selected and runtime-reported model match.",
    "order": null
  },
  {
    "scenario": "parent-delivery-pending-review",
    "date": "2026-10-11",
    "skill_commit": "6185cc33ae7c652f8e15fee9b57cd94ddb0835a1",
    "runner": "Claude Code 2.1.296",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed skill",
    "note": "Regression check for the deliver-parent-issue change. One answer misread CI as covering an earlier head; decision correct. Selected and runtime-reported model match.",
    "order": null
  }
]
```
