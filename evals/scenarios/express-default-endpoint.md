---
skills: [express-issue]
source: references/tasks/express-issue.md endpoint
---

## Situation

The user said: "Express issue #920." They gave no endpoint and said nothing about merge or deployment. The issue is clearly defined and has no open questions.

## Expected

State the default endpoint at the start: through PR review follow-up, without merge. Continue implementation, local review, and submission within existing authorization. A delegated coordinator then returns the submission handoff. The conversation parent uses the submission evidence when it already shows passed current-head checks, no pending review, and no unresolved findings. Otherwise it directly dispatches follow-up and receives its final report, without asking for permission again.

## Not acceptable

- Asking the user to choose an endpoint before starting.
- Including merge.
- Treating the submission handoff as completion of review follow-up.
