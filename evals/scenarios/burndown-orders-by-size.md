---
skills: [burndown-ready-queue]
source: docs/research/trials/2026-10-15-unattended-burndown-3.md; references/tasks/burndown-ready-queue.md audit the ready queue
---

## Situation

You coordinate an unattended burndown with an eight-hour budget. The validated traversal shows three Ready issues, all P1: #600 with Size XS, #930 with Size M, and #947 with Size S. No other item is in Ready. You are recording the selection order before the first dispatch.

## Expected

Order the selection #600, #947, #930: all are P1, so Size decides, smallest first, and issue number only breaks a tie within the same Size. Record that order in the notes and dispatch #600 first.

## Not acceptable

- Ordering by issue number alone, as #600, #930, #947.
- Ordering by the board's card position.
- Starting with the largest issue.
