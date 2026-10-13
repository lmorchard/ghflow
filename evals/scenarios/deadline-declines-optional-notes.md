---
skills: [burndown-ready-queue, express-issue]
source: docs/research/trials/2026-10-13-unattended-burndown.md; references/tasks/burndown-ready-queue.md deliver issues sequentially
---

## Situation

You coordinate an unattended burndown through PR review follow-up, without merge. The deadline is 02:04, and the time is now 01:30. The third issue's draft PR has a green head, and the fresh-context reviewer just approved it with no actionable findings and two notes it calls optional: one documentation line and one extra regression test. Earlier tonight, a correction worker took 34 minutes for an eight-line wording change, its re-review took 16 minutes, and each ready submission took 20 to 27 minutes. Your own turns between dispatches have taken 8 to 11 minutes each. Hosted CI runs in about two minutes.

## Expected

Decline both optional notes, record them with the reason in the PR description, and dispatch the ready submission for the approved head now. The measured durations show that a correction, a re-review, and the ready step would not fit in the 34 minutes left, and two-minute CI does not change that. The issue reaches the endpoint before the deadline instead of being parked mid-correction.

## Not acceptable

- Dispatching a correction because CI is fast.
- Parking the issue now while an approved head can still reach the endpoint.
- Marking the PR ready without recording the declined notes.
- Asking the user or calling a question tool.
