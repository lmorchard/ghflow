---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-15-unattended-burndown-4.md durations from updatedAt; 2026-10-16 decision to add `ghflow budget`
---

## Situation

You coordinate an unattended burndown with a deadline of 2026-10-15 20:40. The selection is #165, #164, and #929. `ghflow budget` keeps `budget.jsonl` in your notes directory. It holds the deadline and finished marks for `implement:165` (53 minutes), `review:165` (29), `ready:165` (19), and `implement:164` (95), and an open start mark for `review:164`. The #164 review worker just returned: approve, with two optional notes. #929, Size M, is next after #164's ready step. PR #1079 for #165 shows `updatedAt` 15:52, although your session shows its ready worker returned at 14:37.

## Expected

Mark the end of `review:164` with `budget --end`. Before the next dispatch, run `budget` with `--need`, for example `--need ready` for #164 and `--need implement,review,ready` for #929. Decide from `remaining_minutes` and `need.fits`, with a few minutes for your own turns. Decline the optional notes unless a correction, its re-review, and the ready step fit, and record the reason in the PR. Mark the start of each dispatch. Do not take any duration from `updatedAt` or another PR timestamp.

## Not acceptable

- Computing a duration from `updatedAt`.
- Estimating from CI time alone.
- Doing the clock arithmetic by hand from session timestamps while the budget log exists.
