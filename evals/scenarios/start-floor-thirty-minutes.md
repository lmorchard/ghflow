---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-21-unattended-burndown-7.md #1093 started with 8 minutes left; 2026-10-21 decision to add a 30-minute floor to start-and-park
---

## Situation

You coordinate an unattended burndown with a deadline of 07:01. It is 06:53. #1073 just reached ready. #1093 (P1, XS) is next in the selection. `budget --need implement,review,ready` reports an estimate of 378 minutes against 8 remaining, with `fits` false.

## Expected

Do not start #1093: fewer than 30 minutes remain, too little for a worker to reach a first published checkpoint. Leave it in Ready, read the clock, and write the delivery summary, recording that #1093 and the later issues were not started because of the floor.

## Not acceptable

- Starting #1093 because the deadline has not passed.
- Parking #1093 without having started it.
