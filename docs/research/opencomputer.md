# OpenComputer: runner lessons for ghflow

This document records a review of [OpenComputer](https://github.com/diggerhq/opencomputer) on 2026-11-22, at commit [`40bd39d`](https://github.com/diggerhq/opencomputer/tree/40bd39dc4cd581d254daa1b2b7ffe020375f1585).
The sections below are proposals and observations. They are not project decisions.

## What OpenComputer is

OpenComputer is a self-hosted coding agent that people use from Slack. Most of the repository is a sandbox platform: virtual machines, checkpoints, billing, a dashboard, and SDKs. That part does not apply to ghflow.

The relevant part is **Calvin**, in `computer/`. Calvin is a gateway that runs one agent session for each Slack thread. Each session gets its own git worktree on a new branch, and its work ends as a pull request (PR). Calvin has no workflow layer: no issue definition, review gate, or project board. So it does not overlap with the ghflow skills. Its runner mechanics are more developed than the ghflow queue runner.

The top-level README says that Calvin supports Claude Code, Codex, and OpenCode. At this commit, `computer/src/runner/harness/` contains only `claude/` and `codex/`. There is no OpenCode support to learn from.

## Proposals filed as issues

### A fake model for runner integration tests

Calvin's [`fake-model.mjs`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/src/dev/fake-model.mjs) replaces the model API in development checks. It has no dependencies. If a message contains `call <tool> <json>`, it answers with a call to that tool, and `GET /calls` returns the calls it kept. The checks run the real runner and the real agent harness with no model and no credential.

The ghflow runner tests mock `subprocess.Popen` with handwritten OpenCode events. Those events cannot detect a change in the OpenCode event format. Several runner failures occurred at that boundary. Filed as [#214](https://github.com/lmorchard/ghflow/issues/214).

### A commit trailer that links commits to sessions

Calvin's [`prepare-commit-msg`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/hooks/knowledge/prepare-commit-msg) hook adds `Session: $SP_SESSION_ID` to each commit with `git interpret-trailers`. Without the variable, the hook does nothing. It never fails a commit.

The ghflow runner deletes each OpenCode session after it writes the session log. No commit identifies its log. Filed as [#215](https://github.com/lmorchard/ghflow/issues/215), with the hook installation question left open.

## Other observations

### Rules that hooks enforce

Calvin states hook-enforced rules to the agent as facts, not as requests. [`knowledge.ts`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/src/workspaces/knowledge.ts) says: "The rules a hook enforces ... are stated as what happens, not asked of the agent." Its [`pre-push`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/hooks/knowledge/pre-push) hook refuses a duplicate work item number, and the message names the number to use. If the hook itself fails, it refuses nothing.

This is the ghflow rule of [deterministic steps](../dev/direction.md#deterministic-steps-in-unattended-delivery), applied at the git layer. Possible ghflow uses are a refusal to push to the default branch, or a refusal of a commit without an issue reference. No trial has shown a need for either.

### Long blocking commands

Calvin's [system prompt](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/src/runner/system-prompt.ts) tells the agent not to block in the foreground on slow commands, such as `gh run watch`, sleep loops, or `--wait` flags. [`held-steer.ts`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/src/runner/held-steer.ts) posts a note when a user message waits more than 8 seconds behind a running step.

ghflow sessions do not take messages during a run. But a local-model session that waits on CI uses the session time budget. The runner could find long `gh run watch` calls in the session log. This observation needs evidence from a trial before it becomes a proposal.

### File-size ratchet

Calvin's [`max-lines.mjs`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/scripts/max-lines.mjs) warns at 400 lines and fails at 600 lines. It lists files that were already too large with their size at that time. Those files can only become smaller. `scripts/run_queue.py` is the largest ghflow script. A ratchet is a code-health choice for Les, not a workflow need.

## Deferred

Two isolation mechanisms are stronger than the current machine-account token. They matter only if ghflow runs sessions that are not trusted, or sessions for more than one person.

- [`tokens.ts`](https://github.com/diggerhq/opencomputer/blob/40bd39dc4cd581d254daa1b2b7ffe020375f1585/computer/src/host/tokens.ts) relays short-lived GitHub App tokens to each session through a socket that the host owns. The host, not the session, names the session that a token is for.
- `oc-modelproxy` (`computer/modelproxy/`) keeps model credentials out of the session environment. The session holds a placeholder. The host binds each runner to its credential.

[Agent identity](agent-identity.md) records the earlier GitHub App research.

## Not applicable

The Slack interface, the virtual machine and Podman infrastructure, and the `.agents/{design,work,done}/` work items do not apply. The work items are a file-based form of what ghflow does with GitHub issues and the project board.
