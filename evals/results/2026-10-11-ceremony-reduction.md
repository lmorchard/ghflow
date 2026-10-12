# Ceremony reduction decision samples, 2026-10-11

Seven new or updated scenarios from the express ceremony reduction ran on Claude Sonnet through the Claude Code runner, two samples each against the changed text. Five of them also ran once against the old skill text as a baseline. Five related scenarios ran once against the changed text to find regressions. Every changed-text and regression sample passed. Four of five baselines failed on the reversed decision, so the scenarios detect the change. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-11-ceremony-reduction-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

The changed source commit is `1058e20ddcac4948272364ef762d3b7d7647fb1b` on branch `reduce-express-ceremony`, with source fingerprint `4f41a5174642638b08eb608370f19713869affa9cbfa566394df9046f43b050b`. The baseline commit is `2c75b205aea75f0dc11e6645ee4775ad46172f15` on the local scratch branch `baseline-997-scenarios`, with fingerprint `49e8ac17fbf94bb1e814ef0d59b0b34e6dc7212203ae8458c6f0f10eb8b50e13`. The baseline commit holds the skill text of main at `48b4c68` plus the current scenario files, because the runner reads the scenario from the selected commit. It is not for merge. Each snapshot contained `SKILL.md` and its recursively linked Markdown references, 45 files in all.

Each batch used this command form through `/tmp/ceremony-runs/run-batch.sh`, one output directory per scenario:

```sh
python3 scripts/run_scenario.py SCENARIO --runner claude --model claude-sonnet-5-5 \
  --commit COMMIT --repeat REPEAT --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was Claude Code `2.1.296`, with the same isolation controls that the [coordinator preparation report](2026-10-11-coordinator-preparation.md) records. Every run reported runtime model `claude-sonnet-5-5`, exited 0, and returned no diagnostic. Runs took 8 to 17 seconds. The skill change author was Claude Fable 5.1 in a Claude Code session, so the Sonnet runner is a different model from the author.

Les approved these runs on 2026-10-11. Raw provenance and answers remain under `/tmp/ceremony-runs/`.

## Results

Grades use the criteria at commit `1058e20` for every phase, including the baselines, which test whether the old text reaches the new decisions.

| Scenario | Phase | Session | Runtime model | Time | Grade |
| --- | --- | --- | --- | --- | --- |
| corrections-same-worker | baseline | `69f7611c-da54-4f6d-9463-eff320ef5422` | claude-sonnet-5-5 | 9 s | Fail |
| delivery-early-draft | baseline | `dfe8ba08-b236-4308-b1b7-72d386b9799e` | claude-sonnet-5-5 | 12 s | Fail |
| express-complete-return | baseline | `b070b5a4-dcb7-42c1-b561-f49a99cb1e40` | claude-sonnet-5-5 | 10 s | Pass |
| followup-already-green | baseline | `313dd0da-36a4-45dc-a6f7-9ad0068f6e3d` | claude-sonnet-5-5 | 11 s | Fail |
| implementation-handoff-operation-scope | baseline | `92a12b60-674d-4088-bcf0-99cd6ce8500c` | claude-sonnet-5-5 | 10 s | Fail |
| corrections-same-worker | changed | `34bb961a-1d3e-4c9f-99ae-ccadb1592d81` | claude-sonnet-5-5 | 8 s | Pass |
| corrections-same-worker | changed | `c5bea2f0-ec76-4c98-95bb-f5882a9f68e9` | claude-sonnet-5-5 | 8 s | Pass |
| delivery-early-draft | changed | `0baf465f-6b0d-40cf-a2ab-48efc9cf4b12` | claude-sonnet-5-5 | 17 s | Pass |
| delivery-early-draft | changed | `cd05a70d-726a-4d2e-997c-5e5557619798` | claude-sonnet-5-5 | 14 s | Pass |
| draft-pr-ready-transition | changed | `cf6f91e0-37fe-42c7-ad4e-484e86fe44c7` | claude-sonnet-5-5 | 10 s | Pass |
| draft-pr-ready-transition | changed | `a0f52a18-714a-4c3e-8e43-250bea2e173d` | claude-sonnet-5-5 | 9 s | Pass |
| express-complete-return | changed | `e7e66e88-e498-4d64-aae9-9781f1e3ae04` | claude-sonnet-5-5 | 11 s | Pass |
| express-complete-return | changed | `48a071d9-68ac-4e0b-8e1a-9aa10f55a65b` | claude-sonnet-5-5 | 10 s | Pass |
| express-default-endpoint | changed | `2e63ff7d-1a62-4301-91e0-089f57a3ac46` | claude-sonnet-5-5 | 8 s | Pass |
| express-default-endpoint | changed | `3ece1722-9fd2-4124-9db1-c6a4554be656` | claude-sonnet-5-5 | 8 s | Pass |
| followup-already-green | changed | `78711ffe-85e4-4421-bf01-dcec402b2aa5` | claude-sonnet-5-5 | 11 s | Pass |
| followup-already-green | changed | `e1c34cbd-d2d7-42b9-a951-804e1a59bf8d` | claude-sonnet-5-5 | 10 s | Pass |
| implementation-handoff-operation-scope | changed | `fa777121-5537-471b-98b6-4a9e452cbd59` | claude-sonnet-5-5 | 12 s | Pass |
| implementation-handoff-operation-scope | changed | `f0794a08-2093-4132-8be5-c7b74c55a421` | claude-sonnet-5-5 | 10 s | Pass |
| capacity-limit | regression | `c9133784-6f0c-401d-b9b7-46d04994132f` | claude-sonnet-5-5 | 11 s | Pass |
| context-reuse-implementation-worker | regression | `49948143-0b5b-49d8-bdf1-81aececc688f` | claude-sonnet-5-5 | 10 s | Pass |
| coordinator-ready-to-dispatch | regression | `0728793d-02ab-426e-bce4-34f6af87365c` | claude-sonnet-5-5 | 16 s | Pass |
| implementation-local-only | regression | `4d123a5a-01d9-4844-9afc-906f2738a670` | claude-sonnet-5-5 | 9 s | Pass |
| submission-parent-followup | regression | `39f38e7e-1fe9-4b9f-927f-bf4ed41a24ed` | claude-sonnet-5-5 | 13 s | Pass |


### Baselines against the old text

- `followup-already-green` dispatched `address-pr-review` because submission alone did not complete the endpoint. Fail, as intended.
- `corrections-same-worker` returned the finding to the same worker with a local-only limit and planned a separate `submit-pr` dispatch to publish the fix. Fail on the separate publication worker.
- `implementation-handoff-operation-scope` assigned local implementation only and planned a separate draft dispatch. Fail, as intended; this was the decision PR 62 expected.
- `delivery-early-draft` dispatched `submit-pr` as a separate worker for the checkpoint. Fail on the separate publication worker.
- `express-complete-return` dispatched the reviewer without reading the diff, which the old text also supported. Pass. Its later steps named a separate `submit-pr` dispatch for the ready step, which the scenario does not grade.

### Changed text

All fourteen answers reached the expected decision and cited the new text as the deciding rule: the resumed implementation worker for corrections and ready submission, the same-session continuation into `submit-pr`, the no-self-review sentence, and the conditional follow-up in "Continue to the endpoint in the parent". Both `implementation-handoff-operation-scope` answers named `implement-issue` then `submit-pr` as two operations for one worker, wrote out the compatibility decision, and linked to the issue instead of copying it. Both `followup-already-green` answers reported and stopped, kept the same-model label, and took the facts from the worker's read-back.

Possible wrong reason: one `draft-pr-ready-transition` answer opened with "resume the implementation worker, or act as it if I am that worker", which blurs the coordinator and worker roles before reaching the correct sequence. One `implementation-handoff-operation-scope` answer said the coordinator continues to `address-pr-review` in a direct session "unless the ready-submission read-back already shows the final follow-up evidence", which is the intended rule.

### Regression

All five passed. `coordinator-ready-to-dispatch` and `context-reuse-implementation-worker` cited the new worker-reuse and no-self-review text as support, without changing their decisions. `capacity-limit` kept independent review pending and handed off to the parent. `implementation-local-only` kept the explicit local-only limit and did not read the new continuation sentence as permission to publish. `submission-parent-followup` kept follow-up incomplete because a required check was pending.

## Limits

One model and one run per baseline is a sample, not proof. The baselines used current scenario criteria against old text, so a Fail there shows that the scenario discriminates, not that the old text was wrong on its own terms. No run exercised a local model, which is the runtime that produced the trial. Decision scenarios do not establish fewer dispatches or less wall clock on a real issue.

```scenario-results
[
  {
    "scenario": "corrections-same-worker",
    "date": "2026-10-11",
    "skill_commit": "2c75b20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Fail",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "delivery-early-draft",
    "date": "2026-10-11",
    "skill_commit": "2c75b20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Fail",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "express-complete-return",
    "date": "2026-10-11",
    "skill_commit": "2c75b20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "followup-already-green",
    "date": "2026-10-11",
    "skill_commit": "2c75b20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Fail",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "2c75b20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Fail",
    "phase": "baseline",
    "note": "Old skill text with current scenario files, scratch commit not on main.",
    "order": 1
  },
  {
    "scenario": "corrections-same-worker",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "delivery-early-draft",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "draft-pr-ready-transition",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "express-complete-return",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "express-default-endpoint",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "followup-already-green",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "implementation-handoff-operation-scope",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "changed",
    "note": null,
    "order": 2
  },
  {
    "scenario": "capacity-limit",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "context-reuse-implementation-worker",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "coordinator-ready-to-dispatch",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "implementation-local-only",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  },
  {
    "scenario": "submission-parent-followup",
    "date": "2026-10-11",
    "skill_commit": "1058e20",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "regression",
    "note": null,
    "order": 2
  }
]
```
