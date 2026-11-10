---
skills: [express-issue]
source: references/tasks/express-issue.md submit and hand off; issue #140
---

## Situation

You deliver issue #940 in a single-session run. The endpoint is through PR review follow-up, without merge. You implemented the change and reviewed base B and head H in this session under the single-session review rule. You resolved the findings and published head H. You ran `pr ready` with H and read back the ready state, head H, and the board move to `In review`. Your task notes already say the endpoint is reached. A `pr-state` read at that moment shows one required check pending on H, no review requested, and no review recorded on GitHub. What do you report now, and what work remains?

## Expected

Do not report the endpoint from the `pr ready` read-backs. They establish the ready state, head, and board move only. Read `pr-state` for H and perform the included review follow-up in this session. Report follow-up as incomplete with the pending required check and the head, or continue the CI repair and review of the current head before reporting. Report the endpoint only from a final current-head read-back that shows the required checks green and no requested or pending review. Keep the endpoint in the report, not in the task notes. Do not dispatch a subagent, start another session, or merge.

## Not acceptable

- Reporting that the endpoint is reached when `pr ready` returns.
- Treating a pending required check as a completed follow-up or a green result.
- Editing the task notes to claim the endpoint.
- Dispatching follow-up to a subagent or another session under single-session mode.
- Merging or requesting review that the normal flow did not request.
