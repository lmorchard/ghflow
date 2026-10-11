# Skill evaluations

This document describes how the project checks that the skills work. It records the practice that the results in `evals/results/` show, and it selects one method where that practice varied. The [scenario format](../../evals/README.md) gives the file format and the run prompt.

## Kinds of assessment

The project uses two kinds of assessment.

A **decision scenario** gives a fresh agent a constructed situation and the skill text. The agent states what it would do and names the rule that decides it. It runs no commands. A scenario tests whether the skill text leads to the intended decision. Scenarios are in `evals/scenarios/`, and their results are in `evals/results/`.

A **trial** gives an agent a real issue or a synthetic fixture and observes its actions. A trial can find failures that a scenario cannot find, such as a wrong command or a wrong account. Trials are in [Trial records](../research/trials/README.md).

Neither kind replaces the other. A trial or a retrospective often supplies the cases for new scenarios. A scenario result is not evidence about the commands that an agent runs. Issue #32 proposes focused execution trials for that purpose.

[Project direction](direction.md) uses both kinds as evidence, with limits stated for each assessment.

## When to add a scenario

Add a scenario when an authorized change alters a decision that a skill makes. [Skill style](skill-style.md) requires this. Typical sources are these:

- A trial or a retrospective that found a wrong decision.
- A decision by Les that changes policy.
- A defect in skill text that an agent misread.

Add the scenario in the same change as the skill revision. Update an existing scenario in the same commit when a skill change alters its intended decision. If two scenarios test the same decision, combine them and record the change in the next result file.

## Write a scenario

Name the file with a kebab-case description of the situation, such as `cleanup-local-commit-ahead.md`.

Use two frontmatter keys:

- `skills` lists the task names under test, such as `[merge-pr]`. Use task names, not file paths.
- `source` names where the case came from. Use a commit, a dated trial, an issue, a reference path with its section, or a decision by Les. `scripts/check.py` makes sure that a reference path in `source` exists.

Write three sections: Situation, Expected, and Not acceptable. The [scenario format](../../evals/README.md) describes them. Put only observable facts in the Situation. Do not hint at the answer or name the rule. Keep Expected to what the current skill text requires.

## Choose a run pattern

Select the pattern that answers the question.

**Baseline, change, and rerun.** Use this pattern for a new rule. Run each new scenario once against the old skill text. The baseline shows that the scenario detects the problem. Then change the skill and run each new scenario twice. Run related scenarios once to find regressions.

**Decision sample.** Use this pattern to check an issue or a PR. Run each affected scenario once. If an answer is surprising, repeat it once with the identical prompt.

**Full sweep.** Use this pattern after a large rewrite of the skills. Run every scenario once.

## Run a scenario

### Isolate the session

Give the agent under test only what a real agent would have. Make sure that the session meets these conditions:

- It has no conversation history.
- Its prompt is the template in the [scenario format](../../evals/README.md), with the Situation and the skill paths filled in.
- It cannot see Expected, Not acceptable, earlier answers, earlier grades, or the author's conversation.
- It runs no task commands, makes no edits, uses no network, dispatches no agents, and asks the user no questions.
- It reads only skill source at the evaluated commit.
- It has no identity or GitHub credentials in its environment.

Enforce these limits with the runner when it can. When the runner cannot enforce a limit, put the limit in the prompt and record that only the prompt enforced it.

### Select the model

Use a model that is different from the model that wrote the skill change, when one is available. A different model gives stronger evidence that the text is clear. Record the selected model. Record also whether the runner reported the model at runtime. Record the model that wrote the change.

### Supply the source

Give the agent paths to the skill files at the evaluated commit. The agent then follows links as a real agent does, so the run tests link discovery. If you paste the text into the prompt, the run does not test link discovery. Say so in the result file.

Use `scripts/run_scenario.py` to create a snapshot at the evaluated commit. The snapshot contains only the selected task files and their linked Markdown references. It excludes scenario criteria, results, trial records, and this evaluation guide. The runner fingerprints the files that it supplies: sort lines of relative path, a zero byte, the file SHA256, and a newline, then hash the result with SHA256.

### Runner limits

The runner checks the installed CLI version and records its isolation controls and limits in `provenance.json`. Review that record with each run. Do not assume a CLI option is available on a different version.

Claude Code runs with restricted file tools, a strict empty MCP configuration, and the selected source snapshot as its only additional file directory. It does not enable command, code, web, or agent tools. It retains normal Claude authentication so it can call the model provider.

Codex runs with an isolated configuration and authentication directory, a read-only sandbox, and integrations disabled. The installed Codex CLI has no tool allowlist. It may run shell commands if it chooses to; the prompt forbids commands, and provenance records this as prompt-only. The read-only sandbox blocks edits and network access, but it does not confine reads to the source snapshot. The prompt and provenance state this source limit.

OpenCode can use an existing local OpenAI-compatible server. It checks the exact singleton model inventory before each repeat, configures the main and small model identically, and uses only source-file reads under deny-all permissions. Temporary HOME and XDG directories isolate user configuration and credentials. It refuses system managed configuration that could override these controls. The [local runner instructions](../../evals/README.md#use-an-existing-local-model) state the model-state and permission limits. Do not launch a second model to run a trial while the user's local model is active.

All runners call their model provider over the network. None receives identity or GitHub credentials. The prompt forbids user questions and agent dispatch; provenance identifies whether a control is enforced by the CLI or only by the prompt.

### Measure local efficiency

Use a small decision sample with the user's actual model, quantization, and runtime before a full sweep. Start with one run at a time. Record elapsed time, emitted token and tool counts, repeated reads, tool failures, and decision quality. OpenCode records source-relative read paths, with `null` for unknown paths, and counts tool errors separately from provider errors. A read call does not establish that the agent used or understood its result. Token usage and elapsed time include the CLI's work; they do not isolate server prompt processing or generation. Inspect server cache timings only when the existing runtime already exposes them. Do not change its settings for a trial without authorization.

A decision scenario starts fresh. It cannot establish whether an agent resumes implementation after context loss. Use a separate interrupted implementation trial for that question, with the issue, draft PR, and notes supplied to the resumed agent. Record repeated research and reopened decisions, as well as whether the task completes.

## Grade the answers

Compare each answer with Expected and Not acceptable. Use these grades:

- **Pass**: the answer reaches the expected decision for the expected reasons.
- **Partial**: the core decision is correct, but the answer omits part of Expected. Name the omission.
- **Fail**: the answer reaches a different decision, or it gives an answer in Not acceptable.

If an answer reaches the right decision for a wrong reason, record it. That result points to unclear skill text, even when the grade is Pass.

Record who graded the answers. If the author of the skill change graded them, state that as a limit. An independent reviewer can correct a grade. Record the correction as a grade change, and keep the original answer.

### After a failure

Repeat a failed or partial answer once with the identical prompt before you change the skill. Change the skill when the failure repeats or when the rule is missing. If you decide not to change the skill, record the reason.

### Change criteria after a run

Change Expected or Not acceptable after a run only when the criterion contradicts the current skill text or a decision by Les. Record that only the criteria changed and who accepted the change. If the skill text or the decision changed instead, run the scenario again.

## Record the results

Name the result file `evals/results/YYYY-MM-DD-TOPIC.md`. Use these sections:

1. A summary paragraph with the number of runs and grades.
2. **Source and method**: the full commit SHA, the runner and its version and flags, the selected and author models, and the isolation limits.
3. **Results**: a table with the scenario, the run or session ID, and the grade.
4. **Limits**: what the runs do not show.
5. **Checks**: the `make check` result, when the change includes files.

Link the scenario criteria at the evaluated commit. Keep the raw answers in `evals/results/YYYY-MM-DD-TOPIC-answers.txt`, with a scenario name and a session ID before each answer. Keep other raw logs outside the repository, and record where they are.

Add coverage records using the [record convention](../../evals/README.md#coverage-index-and-records).
Use `make scenario-index` to update the [coverage index](../../evals/INDEX.md).
`make check` makes sure that the index matches the records.

Link the result file from the trial record or the PR that it supports.

## Known gaps

- Historical coverage records retain unknown values when reports do not establish source, runner, model, or date.
- Same-day assessments from separate reports can have unknown order. The index retains these results together.
- The `unpublished-*.md` scenarios formerly used file paths in `skills`; they now list task names like the other scenarios.
- Earlier result files differ from this guide. They record less provenance and use other grade words. This guide does not require changes to those files.
