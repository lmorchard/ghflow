# Skill scenarios

These scenarios check whether an agent that reads a skill makes the decision the skill intends. Use them after you change a skill, to find rules that the change lost or made unclear. They do not replace trials on real issues.

[Skill evaluations](../docs/dev/skill-evaluations.md) describes when to add a scenario, how to run and grade it, and how to record the results.

## Scenario format

Each file in `scenarios/` describes one situation. Its frontmatter names the skills under test and the source of the scenario, such as a trial or the commit that added the rule. The body has three sections:

- **Situation** is the only text that the agent under test receives.
- **Expected** states the decision and the reasons that a correct answer contains.
- **Not acceptable** lists answers that fail, even when part of the answer is correct.

Write the situation as facts that the agent observes. Do not hint at the answer or name the rule under test. Keep the expected decision to what the current skill text requires. When a skill change alters the intended decision, update the scenario in the same commit.

## Run a scenario

Use `scripts/run_scenario.py` to build and run a prompt from one committed scenario. The runner reads only the Situation section and resolves `skills` task names to paths in a snapshot of the selected commit. The name `ghflow` selects the entry point `SKILL.md`. The snapshot contains the selected task files and their recursively linked Markdown references. It excludes scenario criteria, prior results, trial records, and this evaluation guide. The runner records its source fingerprint, prompt hash, raw answers, and run details. On failure, it also records bounded, redacted stderr diagnostics in the answer and provenance files. It does not grade answers.

Preview a prompt without launching a model session:

```sh
make run-scenario ARGS="SCENARIO --runner codex --model MODEL --dry-run"
```

Run a scenario and write its answers and provenance into a new output directory:

```sh
make run-scenario ARGS="SCENARIO --runner codex --model MODEL --repeat 2 --output-dir /tmp/scenario-run"
```

Use `--runner claude` to select Claude Code. Use `--commit COMMIT` to select a source revision. The default source is `HEAD`. Review and grade the answers separately.

The runner starts each session with no prior conversation. It applies runner-specific limits and records them in `provenance.json`. Claude Code can confine file tools to the source snapshot and disable command, code, web, and agent tools. Codex uses a read-only sandbox and disables integrations, but its CLI has no tool allowlist and does not confine reads to the snapshot. In Codex runs, the prompt forbids commands and reads outside the supplied sources; provenance marks those limits as prompt-only. Both runners need network access to call their model provider. Read the recorded limits before relying on a result.

### Use an existing local model

Use `--runner opencode` with an already running OpenAI-compatible server. Supply the exact model ID advertised by its `/v1/models` endpoint. This example uses the current local Qwen server:

```sh
python3 scripts/run_scenario.py SCENARIO --runner opencode \
  --endpoint http://127.0.0.1:9931/v1 \
  --model ggml-org/Qwen3.8-27B-GGUF:Q4_K_M \
  --context-window 65536 --output-tokens 16384 --timeout 1800 --repeat 1 --output-dir /tmp/local-scenario-run
```

Replace `SCENARIO` and use a new output directory. Set `--context-window` to the context available to one server session; it defaults to 32768. A server with several slots can divide its total context between slots. Set `--output-tokens` to the output limit for one response; it defaults to 4096. A thinking model spends this limit on its reasoning before its answer, so a model such as Qwen3 needs 16384 or more, or the run ends with no answer. The provenance records the limit as `output_limit`, and the diagnostic names it when a run emits close to the limit without an answer. OpenCode runs have a 300-second timeout; use `--timeout SECONDS` to change it. A long reasoning run on a local model can need 1800 seconds or more. A timeout terminates the CLI process group and preserves emitted usage and errors. The runner does not start a server, load a model, or change server settings. Run one scenario at a time when the existing model is also serving other work. `--dry-run` previews the prompt without contacting the endpoint or starting OpenCode.

Before each repeat, the runner checks that the loopback endpoint advertises only the exact selected model. If it reports a load status, that status must be `loaded`. A redirect, missing model, different model, or additional model stops the run before inference. This check cannot prevent another client from changing server state after the check. An inventory without load status establishes advertised identity, not loaded state.

OpenCode runs with temporary HOME and XDG directories, no user credentials, `--pure`, default plugins disabled, and one configured provider. The main model and small model are the same; no second model is selected for auxiliary work. Permissions deny all tools except reads of exact snapshot Markdown paths. OpenCode 1.19.0 matches read permissions relative to its worktree context; the isolated snapshot has no Git repository, so the allowlist includes exact paths relative to `/`, as well as absolute forms. Commands, writes, web tools, questions, and subagent dispatch are denied. OpenCode 2.x dropped `--pure` and `--dir` and runs a shared background service by default, so the runner reads the installed major version and, on 2.x, starts a private server with `--standalone` in the snapshot directory. 2.x matches read permissions relative to that working directory, so the allowlist also carries snapshot-relative paths. Its read tool reports `path` instead of `filePath`. This uses CLI permissions, not an operating-system sandbox. The runner refuses to run when a system managed-config location is present, because managed settings can override isolation.

OpenCode provenance includes elapsed wall time, emitted step token counts, tool-call counts, tool-error counts, read paths, and the model inventory check. `tool_error_count` counts emitted tool states with status `error`, separately from provider error events. `read_paths` keeps one snapshot-relative path per emitted read call, including repeated and failed reads. An absent or unpermitted path is `null`; host paths are not retained. Missing token usage is `null`. Token totals sum the usage reported for each step; they do not measure unique source tokens. OpenCode does not report provider model identity in these events, so `runner_model` remains `null`. The local inventory check is recorded separately. The recorded prompt hash covers the runner's prompt, not OpenCode's complete provider request. Server prompt-cache timings are not collected.

The configuration follows the official OpenCode [CLI controls](https://opencode.ai/docs/cli/), [permissions](https://opencode.ai/docs/permissions/), [custom providers](https://opencode.ai/docs/providers/#custom-provider), and [configuration precedence](https://opencode.ai/docs/config/#precedence-order). It was checked with installed OpenCode 1.19.0 using isolated `debug config --pure`, without inference. The installed read-tool implementation supplied the worktree-relative permission matching rule; config validation alone does not establish successful reads. Tests use synthetic events; a real local decision run is separate evidence.

Compare the answer with the Expected and Not acceptable sections. Record the scenario, skill commit, model, and result in a dated file in `results/`. An answer passes when it reaches the expected decision for the expected reasons. Note when an answer passes for a wrong reason, because that points to unclear text.

One run is a sample, not proof. When a scenario fails, run it again before you change the skill. A rule that fails repeatedly is unclear or missing.

## Coverage index and records

The [coverage index](INDEX.md) shows the latest recorded evidence for each current scenario.
After editing scenarios or records, use `make scenario-index` to update `evals/INDEX.md`.
Use `python3 scripts/scenario_index.py --check` to make sure that the file is current.
`make check` includes this command. Invalid records, missing blocks, and unknown scenario names cause failure.

### Write a coverage record

A coverage record is a structured summary of a report.
The generator reads JSON lists in fenced `scenario-results` blocks in every Markdown file under `results/`.
JSON uses `null` for unknown values.
Each record requires these fields:

```scenario-results
[
  {
    "scenario": "implement-does-not-merge",
    "date": "2026-10-02",
    "skill_commit": "79737b3",
    "runner": null,
    "model": "Claude Sonnet",
    "grade": "Pass",
    "phase": "sample",
    "note": null,
    "order": null
  }
]
```

This example comes from [the full sweep report](results/2026-10-02-full.md).
`scenario` names a current scenario without `.md`. Other text fields accept a nonempty string or `null`.
`date` uses `YYYY-MM-DD` when the report establishes a date for the assessment. It accepts `null` when chronology is unknown.
Historical dates come from dated report headings or explicit assessment dates. A filename alone does not establish a run date.
`skill_commit` identifies evaluated source, not the commit that adds the report.
Keep a recorded abbreviated commit unchanged. For mutable source, use `null` unless recorded hashes establish a later commit with identical bytes.
Explain that later association in `note`.
`runner` identifies the execution tool. `model` records supported actor selection or runtime identity, with its evidence limit in `note`.
A parent model does not establish an actor model.
`grade` preserves human grading and batch counts, such as `Pass (2/2)`. A batch is not an individual sample.
Use separate records for different grades or phases. Use `null` for an ungraded answer.
`phase` names the assessment phase. `note` records source limits, mappings, and grade qualifications.
`order` accepts a positive integer or `null`. Use increasing values only when the report establishes an order within one scenario.
For example, baseline records use 1 and changed-skill records use 2. Equal values retain separate samples or batches.
The generator never compares order values across reports.

### Use runner provenance

Provenance records the source and method of a run.
For output from `run_scenario.py`, copy `scenario`, `source_commit`, `runner`, and `model` from `provenance.json`.
Use the UTC date from `started_at_utc` for `date`. Examine `runs` for runtime model evidence and execution failures.
Record selected and runtime model differences in `note`. Add human grades only after reading the answers and scenario criteria.
Keep the raw answers and source limits in the report. The coverage generator does not grade answers or inspect external provenance files.

### Read historical coverage

For a renamed or consolidated scenario, name its current scenario and explain the original case and changed criteria in `note`.
An unnamed ad hoc assessment remains in the original prose. It does not become a scenario record.

The index retains all records on the latest known date and undated records.
Within one report, an explicit larger `order` value replaces earlier records for that scenario.
Records with unknown order remain visible. Report names and record text supply stable display order, not run chronology.
“No recorded run” means that no report contains a structured record for the scenario. It does not prove absence of unrecorded execution.
A changed repository HEAD alone does not invalidate earlier evidence. Read source and criteria limits before comparing results.
