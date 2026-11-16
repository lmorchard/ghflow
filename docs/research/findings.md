# Findings from agent sessions

This document records lessons from agent-sessions. We read its records on 2026-09-30 at commit `4379832`. The links identify that version so later edits do not change the sources.

The source records include experiments and incidents. We did not do those experiments again. This review does not independently establish every historical claim.

## The workflow existed before the control program

The original design identified dev-session as the source of most steps for one issue. An issue is a GitHub record of a requested change. The design added acceptance criteria, which state the conditions for success.

The design kept automatic task selection outside the skill. An agent skill supplies instructions to an agent. This supports an initial project with useful operations and instructions, without automatic task selection.

Source: [design, origin and dev-session analysis](https://github.com/lmorchard/agent-sessions/blob/4379832/docs/design.md).

## The current skill requires its control program

The old skill records requested GitHub changes in a file. A separate program reads that file and makes the changes with its own credentials. The board procedure uses this method too.

The review procedure expects the program to supply comments before the agent starts. It stops so the program can select the next step. Copying the skill files alone does not remove these dependencies.

Each new phase requires explicit inputs and a way to get the necessary information. A phase is a task such as a PR review. A pull request (PR) proposes changes for review.

Sources: [write manifest](https://github.com/lmorchard/agent-sessions/blob/4379832/skills/agent-session/references/write-manifest.md), [board integration](https://github.com/lmorchard/agent-sessions/blob/4379832/skills/agent-session/references/github-projects.md), [addressing comments](https://github.com/lmorchard/agent-sessions/blob/4379832/skills/agent-session/phases/address_comments.md).

## Evidence must support the stated result

The findings record local tests used as evidence of successful CI. CI is a service that does automated project checks. They also record missing review threads treated as evidence that a review finished.

Other results described a different commit from the one sent to GitHub. A commit records a version of files in Git. Some results treated missing data as success.

A tool must identify the source and commit for its results. It must distinguish an empty result from a failed request. The agent still decides whether the evidence supports the intended behavior.

Sources: [recurring defect classes 1 and 2](https://github.com/lmorchard/agent-sessions/blob/4379832/docs/findings.md), [merge gate procedure](https://github.com/lmorchard/agent-sessions/blob/4379832/skills/agent-session/phases/grade_gate.md).

## Tests must detect the intended problem

The findings record tests that passed without the requested change. Some tests accepted text in comments as evidence of behavior. Other tests missed the absence of the object under test.

Tests for existing behavior and tests for new behavior answer different questions. A passing test suite does not always prove the requested result. Useful tests include missing data and incomplete data.

This lesson does not require the full old procedure for every task. That procedure recorded original checks in a separate commit. It also used a file to detect later changes to those checks.

Source: [defect classes 5 and 6 and rules about oracles](https://github.com/lmorchard/agent-sessions/blob/4379832/docs/findings.md).

## More instructions did not always improve behavior

The recorded experiments compared different instructions. Some additions produced no improvement or worse results. Other instructions helped, such as the rule for changes to previously agreed checks.

Useful instructions remain worth keeping with their sources. A new instruction for every incident can add text without better results. Experiments with wording and observations of real use supply different evidence.

Source: [defect class 4, evidence ledger, and measurement limits](https://github.com/lmorchard/agent-sessions/blob/4379832/docs/findings.md).

## New sessions reveal missing information

The findings record problems that appeared when a new agent session read a specification. A specification states the required behavior and limits. The new session did not share unstated information from the author.

A trial in the same conversation does not establish that another session can do the task. Use an ordinary issue or PR in a new session. Record the information that the new session lacks.

Source: [operating rules and fresh context finding](https://github.com/lmorchard/agent-sessions/blob/4379832/docs/findings.md).

## Tools for repeatable operations remain useful

The founding discussion retained the useful results from Git and GitHub tools. Existing code offers examples for PR information, boards, workspaces, and changes to GitHub. These examples are candidates for reuse, not a requirement to copy every module.

The initial tools will do specified operations and return control to the agent. Automatic scheduling and support for multiple agent applications remain outside the initial project. Shared locks, spending limits, and automatic recovery also remain outside it.

Sources: founding discussion on 2026-09-30 and [predecessor driver sources](https://github.com/lmorchard/agent-sessions/tree/4379832/src/agent_sessions/driver).

## Complexity came from the goals

The agent-sessions source contained 10,190 lines of Python under `src/` at commit `4379832`, with 6,193 lines in the driver. Most of that code served four goals. Unattended merge required frozen checks, spec markers, a read-only grader, and `gate.py`. Parallel runs required the Git ref locks in `locks.py`. Work from the whole backlog required the priority ladder in `router.py`. Continuous operation required the event-driven `reconciler.py`, scheduled runs, and supervision scripts such as `doctor.py` and `run_progress.py`.

A smaller implementation of the same goals does not remove this code. A design that drops a goal removes its subsystem. The queue runner proposal drops all four goals. Before you add a mechanism, identify the goal that requires it.

Sources: [README](https://github.com/lmorchard/agent-sessions/blob/4379832/README.md), [driver sources](https://github.com/lmorchard/agent-sessions/tree/4379832/src/agent_sessions/driver), and line counts from `git ls-files src` at `4379832`, measured on 2026-11-15.

## Documents must not duplicate live status

The findings record file lists and status descriptions that became incorrect after code changes. Historical explanations inside skill instructions also supplied obsolete behavior to agents. Both problems came from text that no longer matched its purpose.

Keep reasons and historical evidence in documents. Keep operating instructions in the skill. Keep current task status in the system that records it.

Date historical observations and link to their evidence. Do not copy the old instructions as the rules for this project. Use the [Writing rules](../writing.md) for the ASD-STE100 trial.

Source: [documentation and skill-authoring conventions](https://github.com/lmorchard/agent-sessions/blob/4379832/CLAUDE.md).
