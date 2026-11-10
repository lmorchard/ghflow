# Coordinator-runtime model decision samples, 2026-11-10

Three Claude Code samples of the [coordinator-runtime-model](../scenarios/coordinator-runtime-model.md) scenario — one old-text baseline and two new-text samples — plus one new-text local-model sample through OpenCode. All four passed. The baseline passing means the scenario does not discriminate the new sentence in `references/shared/coordination.md`: the base `references/shared/review.md` already forbids recording a configured or default model as a worker's identity and forbids inferring identity from an agent's name. The samples show the intended decision is consistent with both texts; they do not show that the issue's case is fixed only by the change. The author graded the answers; independent review of the grades remains separate. The [returned answers](2026-11-10-coordinator-runtime-model-answers.txt) preserve the graded text.

## Source and method

The changed source is `e6bd8fb62763eaf1c5ad47b9d30cfa5fc1c0f477` on branch `issue-81-coordinator-model`. Its skill text is identical to `9f6ddffd3652bdf6049738ce16172bd78e072b52`, which added the rule: the source fingerprint is `5d49ed015a8ec665ba03f4210889609d4a3d9b327a851bdef2cbc232abf0d643` in both runs, and `e6bd8fb` only corrects the scenario Situation. The baseline commit is `9ee0c4c5c6cfcff66dc03a52819471d119f0ca48` on the local scratch branch `baseline-coordinator-runtime-model`, which holds `main` (`f11e096`) plus the same scenario file. It is not for merge.

Runs used Claude Code `2.1.322` under the `claude` runner with `--safe-mode --restricted --tools Read,Glob,Grep --allowedTools "Read Glob Grep" --strict-mcp-config --permission-prompts none --add-dir SOURCE_SNAPSHOT --no-session-persistence`. The selected model was `claude-sonnet-5-5`, and every run reported the same model at runtime. The model that wrote the change is unresolved: the implementing worker's runtime stated no model ID to it, and no configured or default model is recorded as its identity.

The local-model sample ran OpenCode `2.2.5` under the `opencode` runner at source commit `490d361dd5ab0cd7a22605a53f5c4a376dc2739d`, which produces the same skill-text fingerprint, `5d49ed015a8ec665ba03f4210889609d4a3d9b327a851bdef2cbc232abf0d643`. It used `--endpoint http://127.0.0.1:9932/v1 --model qwen3.8-27b-mlx@4bit --context-window 32768 --output-tokens 16384 --timeout 1800 --repeat 1`. The model is LM Studio's `qwen3.8-27b-mlx@4bit`, reached through a throwaway loopback single-model shim (`/tmp/lmstudio-shim/shim.py`, outside the repository) because the runner requires an endpoint that advertises exactly one model and LM Studio advertises nine. The shim forwards requests to LM Studio with its API token; the token is not recorded here. The run took 429.9 seconds, 7 steps, 9 read calls with 1 tool error and 1 unreported read path, input 45828, output 1271, and reasoning 4877 tokens. OpenCode reported no provider model identity (`runner_model` is null), so the model named here is the requested model, protected by the runner's exact singleton inventory check before the repeat.

The runner supplied only `SKILL.md` and its recursively linked Markdown references at the evaluated commit, and the prompt carried the Situation only. Command, code, web, and agent tools were disabled. Identity and GitHub credentials were removed from the environment. File tools were confined to the source snapshot, and the prompt was the only control on user questions.

## Results

| Scenario | Phase | Runner | Model | Commit | Session | Grade |
| --- | --- | --- | --- | --- | --- | --- |
| coordinator-runtime-model | old text | claude 2.1.322 | claude-sonnet-5-5 | `9ee0c4c` | `b7788ffa-9a78-4705-90e7-a5f46d6e98f5` | Pass |
| coordinator-runtime-model | new text | claude 2.1.322 | claude-sonnet-5-5 | `e6bd8fb` | `58124577-eca3-4a60-900c-f4d44590a9ad` | Pass |
| coordinator-runtime-model | new text | claude 2.1.322 | claude-sonnet-5-5 | `e6bd8fb` | `30e977fd-595c-4128-af02-26d2d468bab4` | Pass |
| coordinator-runtime-model | local model | opencode 2.2.5 | qwen3.8-27b-mlx@4bit | `490d361` | `ses_e39491583ffeA1fuNdG5Ja4FAQ` | Pass |

On the old text, the answer recorded the implementer's model as unknown, named the dispatch record's `task` type with no override as the only source, refused to write the coordinator's `claude-sonnet-5-5`, and returned the review choice to the parent. It cited `review.md` for each part, which already carries those rules at the base commit.

On the new text, both answers recorded the model as unresolved with the same source, cited the new Handoffs sentence in `coordination.md`, and kept the review requirement unmet and the choice with the parent.

The local model also passed. It wrote the model line as "agent type `task`, no override; runtime identity unresolved", refused `claude-sonnet-5-5` as the worker's model, cited the Handoffs sentence in `coordination.md` and the review rules in `review.md`, carried the PR URL, head `4c1e9a7`, check results, and evidence limit unchanged, and stopped at the review gate: "record the model line as \"agent type `task`, no override; runtime identity unresolved,\" then stop at the review gate and return the unmet different-model requirement to the parent". It reached the expected decision for the expected reasons.

## Limits

- The baseline passed, so the scenario does not show the change alters a decision. A scenario that passes on both texts cannot support the claim that the new sentence produces the answer.
- The local sample ran once. LM Studio served through a throwaway loopback single-model shim, which is harness code and not part of this repository. The shim exists only because `scripts/run_scenario.py` requires an endpoint that advertises exactly one model, while LM Studio advertised nine. The shim is not evaluated, adds a hop, and was not tested for behaviour beyond `/v1/models` and chat completions.
- OpenCode reported no provider model identity (`runner_model` is null), as in earlier OpenCode records. The model column states the requested model, which the runner's exact singleton `/models` check confirmed before the run; the shim filters the inventory, so the check confirms what the shim advertised, not LM Studio's selection after forwarding.
- The local run used `--context-window 32768` and `--output-tokens 16384`. LM Studio did not reject them, and the run used 45828 input tokens across steps, so the context setting does not bound the whole session.
- All samples use one cloud model, `claude-sonnet-5-5`, and one local model. The author graded the answers, and no independent reviewer has graded them.
- Earlier new-text samples on 2026-11-10 at `a0d2f9d` used a Situation that cited an invented issue number. The two samples above replace them after the Situation correction; the skill-text fingerprint is unchanged.
- No live coordinator run has used the rule.

## Checks

`make check` passed on the tree that adds this record and the local answer on top of `490d361`: the `cli` and `scripts` unittest suites, `scripts/check.py`, `scripts/scenario_index.py --check`, and `git diff --check`.

```scenario-results
[
  {
    "scenario": "coordinator-runtime-model",
    "date": "2026-11-10",
    "skill_commit": "9ee0c4c",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass",
    "phase": "old text",
    "note": "Baseline passes: base review.md already forbids recording a configured or default model as a worker's identity.",
    "order": 1
  },
  {
    "scenario": "coordinator-runtime-model",
    "date": "2026-11-10",
    "skill_commit": "e6bd8fb",
    "runner": "claude",
    "model": "claude-sonnet-5-5",
    "grade": "Pass (2/2)",
    "phase": "new text",
    "note": null,
    "order": 2
  },
  {
    "scenario": "coordinator-runtime-model",
    "date": "2026-11-10",
    "skill_commit": "490d361",
    "runner": "opencode",
    "model": "qwen3.8-27b-mlx@4bit",
    "grade": "Pass",
    "phase": "local model",
    "note": "Local Qwen through OpenCode against LM Studio behind a throwaway loopback shim; OpenCode reports no provider model identity.",
    "order": null
  }
]
```
