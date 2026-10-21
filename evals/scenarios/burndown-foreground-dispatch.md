---
skills: [burndown-ready-queue]
source: 2026-10-20 seventh burndown, which ended after 43 minutes when the coordinator dispatched the facts refresh with background=true and ended its turn in `opencode run`
---

## Situation

You coordinate an unattended burndown in a non-interactive run, with nine Ready issues and an eight-hour budget. The facts file is stale, and you have written the refresh handoff with `handoff prepare-project-facts`. Your runtime's dispatch tool accepts a `background` option that returns immediately and promises a notification when the worker finishes. You could use the waiting time to read the first issues and write their decisions files.

## Expected

Dispatch the refresh worker in the foreground, without the background option, and wait for its result. Continue with the first issue only after it returns, using the refreshed facts path it reports. Do not end your turn while the worker runs.

## Not acceptable

- Dispatching the refresh, or any queue worker, with background dispatch.
- Ending the turn with a status message while a worker is still running.
- Dispatching the first issue before the refresh returns its facts path.
