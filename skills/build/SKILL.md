---
name: ghflow-build
description: Implement code changes, write tests, run local gates (make check), and create commits for an assigned GitHub issue in an isolated worktree. Use when tasked with implementing an issue or fixing review findings.
---

# GitHub issue builder

Produce tested, committed changes for an assigned issue or review feedback. You operate in an isolated worktree, write the implementation and tests, pass project test gates (`make check`), and create local commits. You do not manage project boards, reschedule tasks, create pull requests, or merge.

Before starting, apply [Execution mode](../../references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

For symbol discovery and code navigation, use `tags brief` and `tags outline` for instant definition lookups across git-tracked source files:

```sh
python3 "$GHFLOW_CLI" tags brief <symbol>...
python3 "$GHFLOW_CLI" tags outline <file>
```

Open shared references when their conditions apply: [Agent identity](../../references/shared/identity.md) before Git or GitHub writes; [Evidence](../../references/shared/evidence.md) when recording check results; [Decisions](../../references/shared/decisions.md) when a routine technical choice is missing.

## Builder operations

Match your assigned task to the operation below:

| Operation | Task reference |
|---|---|
| Implement an issue through local commits | [implement-issue](../../references/tasks/implement-issue.md) |
| Address PR review feedback and repair tests | [address-pr-review](../../references/tasks/address-pr-review.md) |

## Worktree discipline

Work exclusively inside your assigned worktree. Follow the project's test-first conventions:
1. Demonstrate the defect or missing behavior before writing implementation code when feasible.
2. Edit only the files needed for the issue. Do not touch unrelated code.
3. Run local test gates (`make check`) to verify zero regressions.
4. Commit changes with clean commit messages under the configured identity.
5. Return the committed head SHA and gate results. The runner handles remote pushes and PR publishing automatically.

## When you cannot verify the issue's claim

An issue's acceptance criteria sometimes require a measurement this environment cannot take: a specific container engine, a particular OS, a host-level tool, a network endpoint, or hardware. **A passing test suite and a plausible diff are not a substitute for that measurement.**

When you hit this:

1. **Do not infer a fix from documentation and present it as verified.** A change that reads correctly, passes CI, and gets a clean review can still fix a problem that does not exist. On 2026-11-27 a worker was asked to confirm whether Podman accepts `--network=default`, could not run `podman`, and shipped an engine-conditional "fix" for a behavior that works correctly on Podman 4.9.3 and 6.1.3. Both the implementing and reviewing models approved it.
2. **Stop and park as a blocker.** Name the missing capability concretely: "cannot verify: `podman` is not installed in this container and the worker cannot reach a host." Do not substitute an assumption for the measurement.
3. **If the issue asks you to check a behavior and the answer is "it already works,"** say so and change nothing. "Verified, no change needed" is a complete and correct outcome — the issue text itself often says to document and close. Delivering an unnecessary patch is worse than delivering none, because it removes working code and has to be reviewed and reverted.
4. **Separate the inferred part from the proven part** in your report. If tests cover a behavior you could not observe, say the tests encode an assumption.

The failure mode this guards against is confident and quiet: the work looks finished, reviews cleanly, and is wrong. Report the gap instead.
