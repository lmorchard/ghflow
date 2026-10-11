---
skills: [express-issue, deliver-parent-issue, burndown-ready-queue, submit-pr]
source: Constructed scenario for issue 13; references/shared/coordination.md PR follow-up ownership
---

## Situation

You are a delegated Ready queue coordinator.
Les authorized delivery through review follow-up, leaving each pull request (PR) open.
Your express worker returns PR #950 with published commit `a1b2c3d` and an independent local review of that commit.
Its CI, the hosted service that checks commits, still has a required check pending.
Submission used source revision `b47c9d5088f471da5d7b35a56ecda6078dee02be`.
A requested review has a recorded request time, deadline, and prior review identifiers.
The next queue issue is independent and ready.

## Expected

Relay the submission handoff and remaining queue scope to the conversation parent, then stop.
Include the PR, published commit, exact source revision, check and review evidence, request time, deadline, identifiers, and authorization limits.
Identify follow-up as incomplete.
The parent directly dispatches address-pr-review to a subagent and receives its final report within existing authorization.
Follow-up ownership does not permit the parent to perform subject-repository work.
Resume queue delivery from the verified endpoint result.

## Not acceptable

- Dispatching a nested follow-up worker from the queue or express coordinator.
- Selecting the next issue before the chosen endpoint finishes.
- Calling submission or pending CI a completed follow-up result.
- Asking Les to authorize the included follow-up again.
- Replacing the original review deadline at the handoff.
- Performing follow-up in the conversation parent because it owns that task.
