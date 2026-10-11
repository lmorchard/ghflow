# Coordinator preparation regression, 2026-10-11

This regression sample supports [PR 62](https://github.com/lmorchard/ghflow/pull/62). It ran 25 related scenarios twice each, which gave 50 answers. Twenty-four scenarios passed 2/2. `blocked-child-independent-work` was Partial 2/2, and an identical rerun was also Partial 2/2. That scenario's governing rule did not change in this PR, and its criteria predate it. The result does not indicate a regression from the PR. The new and changed scenarios of this PR are in a [separate report](2026-10-11-coordinator-preparation.md).

## Source and method

The source was commit `58efdc11e0bb8500455bf1fef4ddb42d7ba3d486`, with source fingerprint `f533c825c24063d9e7ab31c5927db8d0b860761bd0dd1581328a01adefcd94a7` for every run. The PR changes `references/shared/context.md`, `references/shared/coordination.md`, and `references/shared/review.md`.

Each scenario ran with this command, with a new output directory for each scenario:

```sh
make run-scenario ARGS="SCENARIO --runner claude --model claude-sonnet-5-5 --commit 58efdc11e0bb8500455bf1fef4ddb42d7ba3d486 --repeat 2 --output-dir /tmp/pr62-regression-SCENARIO"
```

The runner was Claude Code 2.1.296. The selected model was `claude-sonnet-5-5`. Every run reported runtime model `claude-sonnet-5-5` and exit code 0, with no diagnostics. Runs were sequential. Each answer took between 7 and 16 seconds.

Les approved this runner and model for these 25 scenarios at this commit, two runs each. The approval acknowledged that repository guidance and scenario prompts go to Anthropic.

Provenance records these runner controls: `--safe-mode`, `--restricted`, `--tools Read,Glob,Grep`, `--allowedTools Read Glob Grep`, `--strict-mcp-config`, `--permission-prompts none`, `--add-dir SOURCE_SNAPSHOT`, and `--no-session-persistence`. File tools were confined to an empty session directory and the source snapshot. Restricted mode and the tool list blocked commands and edits. No web, code, MCP, or agent tools were enabled. A minimal environment removed identity and GitHub credentials. Normal Claude authentication remained available so the CLI could call the model provider. Only the prompt prohibited user questions; the noninteractive run had no messaging tool.

The model that wrote the PR's skill change was not recorded in the commits. A Claude Opus 5.5 subagent graded the answers. It did not write the skill change. The parent agent and Les have not reviewed these grades.

Raw answers, with session IDs and grades, are in the [answers file](2026-10-11-coordinator-preparation-regression-answers.txt). Provenance for each scenario remains in `/tmp/pr62-regression-SCENARIO/provenance.json`. The rerun is in `/tmp/pr62-regression-blocked-child-independent-work-rerun/`.

## Results

| Scenario and criteria | Sessions | Grade |
|---|---|---|
| [context-read-selected-task](../scenarios/context-read-selected-task.md) | `f4f8b9a6`, `b1fe1c00` | Pass (2/2) |
| [context-reuse-implementation-worker](../scenarios/context-reuse-implementation-worker.md) | `f8154bb6`, `17fd0fab` | Pass (2/2), borderline |
| [context-complete-inventory](../scenarios/context-complete-inventory.md) | `d1ec8f2d`, `18d6c17d` | Pass (2/2) |
| [delivery-early-draft](../scenarios/delivery-early-draft.md) | `46f1b0be`, `a29a54a3` | Pass (2/2) |
| [draft-pr-ready-transition](../scenarios/draft-pr-ready-transition.md) | `a40c22ea`, `de244f50` | Pass (2/2) |
| [draft-pr-resume-progress](../scenarios/draft-pr-resume-progress.md) | `1497f72b`, `fc3a2f66` | Pass (2/2) |
| [task-notes-location-handoff](../scenarios/task-notes-location-handoff.md) | `f7de5c39`, `f88251c5` | Pass (2/2) |
| [task-notes-resume](../scenarios/task-notes-resume.md) | `8ae3cd95`, `6134e857` | Pass (2/2) |
| [parent-delivery-pending-review](../scenarios/parent-delivery-pending-review.md) | `dbc7ba17`, `e2173bb6` | Pass (2/2) |
| [parent-external-head-update](../scenarios/parent-external-head-update.md) | `489d08b4`, `6732abd2` | Pass (2/2) |
| [followup-current-head-pending](../scenarios/followup-current-head-pending.md) | `b39c1e3e`, `3cbc2de2` | Pass (2/2) |
| [implement-does-not-merge](../scenarios/implement-does-not-merge.md) | `ad960779`, `392fa65d` | Pass (2/2) |
| [tackle-issue-delivery](../scenarios/tackle-issue-delivery.md) | `a1ae83fa`, `c1643355` | Pass (2/2); synonym routing not exercised |
| [express-default-endpoint](../scenarios/express-default-endpoint.md) | `dafd3438`, `f6aaa6dd` | Pass (2/2) |
| [capacity-limit](../scenarios/capacity-limit.md) | `f3c920f8`, `53d0a5b7` | Pass (2/2) |
| [reviewer-model-unknown](../scenarios/reviewer-model-unknown.md) | `fa37fbbe`, `a8134c4b` | Pass (2/2) |
| [reviewer-recorded-models](../scenarios/reviewer-recorded-models.md) | `a7ee9f45`, `de803293` | Pass (2/2) |
| [reviewer-author-identity-unknown](../scenarios/reviewer-author-identity-unknown.md) | `6fdc0929`, `638351b8` | Pass (2/2) |
| [reviewer-dispatch-unavailable](../scenarios/reviewer-dispatch-unavailable.md) | `c32fb724`, `560c90ac` | Pass (2/2) |
| [review-exception-local-model](../scenarios/review-exception-local-model.md) | `1ba317f7`, `85def2e7` | Pass (2/2) |
| [review-exception-not-approved](../scenarios/review-exception-not-approved.md) | `e1aa2e3c`, `127642ba` | Pass (2/2) |
| [review-exception-outside-scope](../scenarios/review-exception-outside-scope.md) | `1781f4e3`, `50404f58` | Pass (2/2) |
| [subagent-has-question](../scenarios/subagent-has-question.md) | `29aba47a`, `8797fddf` | Pass (2/2) |
| [unpublished-local-review](../scenarios/unpublished-local-review.md) | `5ccd9981`, `21f6b49f` | Pass (2/2) |
| [blocked-child-independent-work](../scenarios/blocked-child-independent-work.md) | `7e5e467e`, `d64aa75a` | Partial (2/2) |
| [blocked-child-independent-work](../scenarios/blocked-child-independent-work.md), rerun | `a20f3e30`, `dbd68cd5` | Partial (2/2) |

The table shortens session IDs. The answers file has the full IDs.

### Partial result

All four `blocked-child-independent-work` answers recorded #914 as blocked, continued #915, and did not choose the wording. None stopped all delivery. Expected also requires the agent to "return the focused question to the user". Every answer instead deferred the question until no other progress remained. They quoted the skill rule: "When no useful authorized progress remains, stop and return a focused question." One answer said: "I don't stop and ask again about #914 while #915 is still available."

The governing line in `references/tasks/deliver-parent-issue.md` has the same text as at `79737b3`. At that commit, the [full sweep](2026-10-02-full.md) recorded a Pass with Claude Sonnet. The scenario criteria have not changed since then, apart from the `source` path. This PR does not change that task file. Therefore, the Partial grade is not a regression from this PR. It shows a tension between the criteria and the skill text, or a stricter grade than the earlier one. The Situation says that the question was already asked. Les should decide whether Expected or the skill text needs clarification.

### Borderline passes

- `context-reuse-implementation-worker`: Both answers resumed the same worker with the draft PR URL, and both deferred fresh review until implementation finished. Neither answer explicitly listed the notes path or the current revision as handoff fields. Both said that the worker continues from its notes.
- `tackle-issue-delivery`: The scenario supplies only `express-issue`, so the runner gave the agent that task directly. Neither answer explicitly interpreted "tackle" as "deliver". Both proceeded with the default express endpoint without asking. The run does not test the synonym routing in `SKILL.md`.
- `parent-delivery-pending-review` `e2173bb6`: The answer said that the fix created a new head and that CI must be read again. The Situation says that CI passed for the current head. The decision was correct.
- `followup-current-head-pending` `b39c1e3e`: The answer did not explicitly say to read the current state again before the final report. The other parts of Expected were present.
- `task-notes-resume` `8ae3cd95`: The answer kept the notes current, but it did not explicitly carry the notes path through later handoffs.

### Observations on the PR's changes

Several answers used the new context rule. `a1ae83fa` said: "I also locate the linked task references before dispatching, and read each one when its task comes up." `dafd3438` said: "I read the linked task references only when each one becomes relevant." `de803293` said: "I haven't read implement-issue.md, so I haven't confirmed its exact handoff requirements." It nevertheless described the handoff it would send.

`638351b8` (`reviewer-author-identity-unknown`) applied the new `review.md` text: "This is a configuration choice, so I'd record it separately from the actual runtime identity returned at dispatch." That paragraph is written for same-model requests, and this scenario is not one. The principle still applies, and the decision is correct.

Answers in direct sessions dispatched `address-pr-review` from the conversation owner. They did not perform follow-up themselves. This agrees with the revised `coordination.md`.

## Limits

These are decision samples. They do not show the commands that an agent would run. The prompt hashes differ between invocations because each prompt includes a temporary snapshot path. The rerun therefore used the same Situation and source, but its prompt hash was not byte-identical. The runner did not record which files each session read. One subagent graded the answers without independent review. The earlier full-sweep comparison used an unspecified Claude Sonnet version and grader.

## Checks

`make check` passed after this report, the answers file, and the regenerated index were added. Static checks passed again after the final edits.

```scenario-results
[
  {"scenario": "context-read-selected-task", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "context-reuse-implementation-worker", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Borderline: notes path and current revision not named as handoff fields. Selected and runtime-reported model match.", "order": null},
  {"scenario": "context-complete-inventory", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "delivery-early-draft", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "draft-pr-ready-transition", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "draft-pr-resume-progress", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "task-notes-location-handoff", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "task-notes-resume", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "parent-delivery-pending-review", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "One answer misread CI as covering an earlier head; decision correct. Selected and runtime-reported model match.", "order": null},
  {"scenario": "parent-external-head-update", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "followup-current-head-pending", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "implement-does-not-merge", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "tackle-issue-delivery", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Runner supplied express-issue directly; entry-point synonym routing not exercised. Selected and runtime-reported model match.", "order": null},
  {"scenario": "express-default-endpoint", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "capacity-limit", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "reviewer-model-unknown", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "reviewer-recorded-models", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "reviewer-author-identity-unknown", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "reviewer-dispatch-unavailable", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "review-exception-local-model", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "review-exception-not-approved", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "review-exception-outside-scope", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "subagent-has-question", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "unpublished-local-review", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Pass (2/2)", "phase": "regression", "note": "Selected and runtime-reported model match.", "order": null},
  {"scenario": "blocked-child-independent-work", "date": "2026-10-11", "skill_commit": "58efdc11e0bb8500455bf1fef4ddb42d7ba3d486", "runner": "Claude Code 2.1.296", "model": "claude-sonnet-5-5", "grade": "Partial (4/4): focused question deferred", "phase": "regression", "note": "Initial batch and rerun each Partial 2/2. Answers follow the unchanged skill line that defers the question until no progress remains; governing rule identical at 79737b3, where the full sweep recorded Pass. Not a PR regression. Selected and runtime-reported model match.", "order": null}
]
```
