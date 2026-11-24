# Local sufficiency audit

This report gives the tables, findings, and candidate rubric for [index.md](index.md).

## Local attempts

The #1438 trial used the local model on all six `impl:local` children. The #1729 run used the local model on the three `impl:local` children.

| Issue | Label | Size | Shape | Preparation | Local result | Turns and context | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1423 | local | S | Fixture gating | Partial: target removed before the run | DONE | 44 + 16 turns; 59.8k peak | Worker adapted to a stale target |
| #1424 | local | S | OTel reset | Complete | DONE | 66 + 23 turns; 91.7k peak | Clean |
| #1419 | local | M | Test split | Complete | Parked | 2 sessions, no edits | Idle timeout |
| #1420 | local | M | Test split | Complete | DONE | 61 + 29 retry + 34 turns; 137.5k peak | Timeout and retry |
| #1421 | local | M | Test split | Complete | Draft | 60 + 42 retry + 55 turns; 148.8k peak | Floor before ready |
| #1725 | local | S | Network and process limits | Complete | DONE | 70 + 37 turns; 107.7k peak | Clean |
| #1726 | local | S | Reaping | Complete | DONE | 55 + 14 turns; 117.7k peak | Clean |
| #1724 | local | M | Remote command quoting | Complete | Parked | 15 turns; 44.8k peak | Idle timeout |
| #1434 | local | mixed | Enum sweep | Complete | 10 of 10 done | Not per issue | Closed local-only epic |
| #1432 | mixed | mixed | Context classification | Complete | 11 of 11 done | Not per issue | 9 local and 2 strong children |
| #1425 | mixed | mixed | Security and paths | Complete | 6 of 6 done | Not per issue | 4 local and 2 strong children |
| #1426 | local | mixed | Dead code cleanup | Complete | 11 of 11 done | Not per issue | Closed local-only epic |

The #1438 #1422 issue was not started. It is not in the table.

## Strong baselines

The #1729 strong labels used Sonnet and Opus. The local model was not tried on these issues.

| Issue | Label | Size | Shape | Strong result | Turns and context | Local test |
| --- | --- | --- | --- | --- | --- | --- |
| #1723 | strong | M | Host record and cache | DONE | 22 + 15 turns; 100.0k peak | Not run |
| #1727 | strong | S | Isolation docs and manual check | DONE | 7 + 10 turns; 40.3k peak | Not run; likely over-provisioned |
| #1728 | strong | M | Selfcheck on a real host | DONE | 15 + 11 turns; 77.6k peak | Not run; needs a real host |
| #1731 | strong | M | Engine outside decafclaw | DONE | 24 + 19 turns; 98.6k peak | Not run |

## Findings

**1. The local label is not a guarantee.** Local-labeled S tasks passed: #1423, #1424, #1725, and #1726. Local-labeled M tasks were mixed: #1419 parked, #1421 stayed a draft, #1724 parked, and #1420 needed a retry. The local label is useful for S mechanical work and weak for M test splits and remote-command work.

**2. The strong label is mostly untested locally.** #1723, #1727, #1728, and #1731 used Sonnet. The audit cannot tell whether the local model would pass them. #1727 is an S documentation change with a manual check. It is a likely false strong label. #1728 needs a real enrolled host. Environment access confounds it.

**3. Preparation is good in this sample.** The issue bodies have Size, Triage, Problem, Result, Scope, Verify, Tests, and Deps sections. The local failures are not missing-definition failures. #1423 had a stale target, but the worker adapted. The M test splits and the remote-command task were well defined and still failed or stayed a draft.

**4. Task shape and size discriminate better than the label.** S mechanical work is local-friendly. M test splits, remote command quoting, and cross-module design are risky for the local model. The binary label puts S docs and M test splits in different groups, but it also puts S docs in the strong group and M test splits in the local group.

**5. The strong label can encode environment access.** #1727 needs a person at an enrolled Mac. #1728 needs a real enrolled host. The label may mean "needs a manual environment," not "needs a stronger model." Separate environment access from model need.

**6. The user hypothesis is partly supported.** The local model can do most S grunt work. Preparation is necessary, but it is not sufficient. M test splits and remote-command work still need a strong fallback in this sample.

## Candidate rubric

| Shape | Size | Local default | Evidence |
| --- | --- | --- | --- |
| Mechanical docs, dedupe, or small refactor with unit tests | S | Yes | #1423, #1424, #1725, #1726 |
| Mechanical route extraction or dedupe with clear tests | M | Local first; strong on stall | #1434, #1426; mixed epics #1432 and #1425 |
| Test split or large-file restructuring | M | Strong fallback | #1419 parked, #1421 draft, #1420 retries |
| Remote command, quoting, or concurrency | M | Strong fallback | #1724 parked |
| Cross-module design, new API, or contract work | M | Strong | #1723 and #1731 strong; local untested |
| Manual or real-host check | Any | Human or strong, independent of model | #1727, #1728 |

## Decision

- Keep the local default for S mechanical work.
- Use a strong fallback for M test splits, remote-command work, and design work until the local-on-strong test runs.
- Do not reclassify the labels yet. The sample is small and the strong labels are mostly untested locally.
- Run #219 on #1723 and #1731. Add #1727 as a false-strong candidate. Leave #1728 out because it needs a real host.
- Run the #1435 S batch as the local-first test for strong-labeled S tasks.
- After those results, replace or narrow the labels with a shape, size, and environment rubric.

## Evidence limits

- Retrospective sample, not a controlled experiment.
- The strong labels were not tested with the local model.
- Some local results used same-model review.
- #1727 and #1728 need a real host. Environment access confounds their labels.
- #1423 had a stale target. The worker adapted.
- The closed epics #1434, #1432, #1425, and #1426 have no per-issue session data in this audit. #1432 and #1425 have strong children, so their completion does not prove local success on every child.
- The strong model was not tested on the M test splits or remote-command tasks. The strong fallback is a practical default, not a proven result.
- Token counts differ by tokenizer, reasoning style, and tool output.
- Wall time is omitted because it measures hardware and infrastructure.
