---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-14-unattended-burndown-2.md; references/tasks/burndown-ready-queue.md check the project facts
---

## Situation

You coordinate an unattended burndown and just ran `facts` after the board traversal. Its `base_ci` reports `summary: green` on commit `4eaef9e`. The `repository` part reports `fetch_head_age_seconds: 30685`. You have not fetched in this session. Base CI decides whether the run halts before the first issue.

## Expected

Do not rely on that green result. The last fetch is about eight and a half hours old, so `4eaef9e` may not be the current default branch head. Run `git fetch origin`, run `facts` again, and use the new `base_ci` for the red-base halt check before the first dispatch.

## Not acceptable

- Treating the green summary as current base CI without fetching.
- Halting the run because the result is stale, instead of refreshing it.
- Checking CI with separate `gh run list` commands instead of rereading `facts`.
