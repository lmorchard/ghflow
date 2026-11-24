# Local sufficiency audit

This report gives the tables, findings, and rubric for [index.md](index.md).

## The #219 paired trial

The #219 trial compared the local and strong implementations of #1723 and #1731. It also recorded the local-only #1725 and #1726. The #1729 run produced the local PRs for #1723, #1727, #1728, and #1731.

| Issue | Label | Size | Local PR | Local result | Strong PR | Strong result | Local turns/context | Strong turns/context | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| #1725 | local | S | [#1781](https://github.com/lmorchard/decafclaw/pull/1781) | Minor, 0 blocking | Not run | — | 70; 107.7k | — | Local only |
| #1726 | local | S | [#1782](https://github.com/lmorchard/decafclaw/pull/1782) | Minor, 0 blocking | Not run | — | 55; 117.7k | — | Local only |
| #1723 | strong | M | [#1784](https://github.com/lmorchard/decafclaw/pull/1784) | Needs work, 1 blocking | [#1793](https://github.com/lmorchard/decafclaw/pull/1793) | Needs work, 2 blocking | 22; 100.0k | 23; 93.0k | Same main defect; the strong diff has one extra blocking finding |
| #1731 | strong | M | [#1786](https://github.com/lmorchard/decafclaw/pull/1786) | Minor, 0 blocking | [#1794](https://github.com/lmorchard/decafclaw/pull/1794) | Minor, 0 blocking | 24; 98.6k | 26; 109.8k | Same themes |
| #1727 | strong | S | [#1783](https://github.com/lmorchard/decafclaw/pull/1783) | Ready PR, open | Not run | — | 7; 40.3k | — | #1729 local; #219 did not pair it; manual Mac check |
| #1728 | strong | M | [#1785](https://github.com/lmorchard/decafclaw/pull/1785) | Ready PR, open | Not run | — | 15; 77.6k | — | #1729 local; #219 did not pair it; real-host check unverified |
| #1724 | local | M | None | Parked | Not run | — | 15; 44.8k | — | Remote-command quoting |

All six #219 PRs are open and unmerged. The #1723 and #1731 pairs are the quality comparison. The #1725 and #1726 local-only results confirm the local label on S work. The #1727 and #1728 local PRs show that the local model did the strong-labeled work; the #219 trial did not pair them.

## Other local attempts

The #1438 trial used the local model on six `impl:local` children. The weekend run used the local model on the `impl:local` children across the janitorial epics.

| Issue | Label | Size | Shape | Preparation | Local result | Turns and context | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| #1423 | local | S | Fixture gating | Partial: target removed | Ready PR | 44 + 16; 59.8k | Worker adapted |
| #1424 | local | S | OTel reset | Complete | Ready PR | 66 + 23; 91.7k | Clean |
| #1419 | local | M | Test split | Complete | Parked | 2 sessions, no edits | Idle timeout |
| #1420 | local | M | Test split | Complete | Ready PR | 61 + 29 retry + 34; 137.5k | Timeout and retry |
| #1421 | local | M | Test split | Complete | Draft | 60 + 42 retry + 55; 148.8k | Floor before ready |
| #1422 | local | M | Test refactor | Complete | Done, merged | 92 turns; 1.1 h | Weekend phase E; the M refactor succeeded |
| #1409 | local | M | JS extraction | Complete | Done, merged | Not per issue | Weekend run; the M extraction succeeded |
| #1337 | local | S | Dispatch helper | Complete | Parked | Not per issue | Two idle timeouts; strong retry is reasonable |
| #1408 | local | S | Lazy imports | Complete | Parked | Not per issue | Draft #1689; 5400 s limit and idle timeout |
| #1411 | local | XS | Dead listener | Missing: target absent | Parked | Not per issue | Under-prepared; recommend close |
| #1434 | local | mixed | Enum sweep | Not audited per issue | 10 of 10 done | Not per issue | Closed local-only epic |
| #1432 | mixed | mixed | Context classification | Not audited per issue | 11 of 11 done | Not per issue | 9 local and 2 strong children |
| #1425 | mixed | mixed | Security and paths | Not audited per issue | 6 of 6 done | Not per issue | 4 local and 2 strong children |
| #1426 | local | mixed | Dead code cleanup | Not audited per issue | 11 of 11 done | Not per issue | Closed local-only epic |

The #1438 #1422 issue was not started in that trial. It ran in the weekend phase E.

## Findings

**1. The labels do not predict implementation quality.** The #219 paired trial found local and strong comparable. On #1723, both need work; the local diff has one blocking finding and the strong diff has two. On #1731, both are minor. The strong arm was not faster. The strong label is a routing label, not a quality signal.

**2. The local model did the strong-labeled #1729 issues.** It produced #1723, #1727, #1728, and #1731. The strong label did not prevent local work. #1727 and #1728 are local PRs from the #1729 run. #1728 still needs a real-host check.

**3. The local label is not a guarantee.** Local M test splits #1419 and #1421 stalled or stayed a draft. Local remote-command work #1724 parked. The weekend S and XS issues #1337, #1408, and #1411 parked. The failures are stalls, limits, and task shape, not bad code. The M test refactor #1422 and the M extraction #1409 succeeded. The #1438 M test splits stalled. The weekend record says shape predicts better than size.

**4. Preparation is mixed.** #1411 had no target at the run base. #1423 had a stale target. The well-defined M test splits and the remote-command issue still stalled. Preparation is necessary, not sufficient. The user hypothesis is partly supported: the local model does most well-defined work, but some shapes stall.

**5. The strong label can encode environment or manual access.** #1727 needs a person at an enrolled Mac. #1728 needs a real enrolled host. The label may mean "needs a manual environment," not "needs a stronger model." Separate environment access from model quality.

**6. The closed epics do not isolate local success.** #1432 and #1425 have strong children. #1434 and #1426 are local-only. The audit has no per-issue session data for any of them. Use them as context, not as local-label evidence.

## Candidate rubric

| Shape | Size | Local default | Strong fallback | Evidence |
| --- | --- | --- | --- | --- |
| Mechanical docs, dedupe, or small refactor with unit tests | S | Yes | On stall | #1423, #1424, #1725, #1726, #1727 |
| Mechanical extraction or dedupe with clear tests | M | Yes | On stall | #1422, #1409, #1434, #1426; mixed epics #1432 and #1425 |
| Test split or large-file restructuring | M | First, with checkpoint and extraction | On stall | #1420 retry, #1421 draft, #1419 parked; #1422 test refactor done |
| Remote command, quoting, or concurrency | M | First, with focused tests | On stall | #1724 parked |
| Cross-module design, new API, or contract work | M | First; review both | On stall or provider need | #1723 both need work; #1731 both minor |
| Manual or real-host check | Any | No | Person or strong environment | #1727, #1728; environment, not quality |
| Stall-prone S or XS | S, XS | First | On stall | #1337, #1408, #1411; #1411 under-prepared |

## Decision

- **Narrow the labels.** Keep `impl:local` and `impl:strong` as routing labels for provider, cost, privacy, and environment. Remove quality expectations. The #219 record owns the trial. This audit adds the shape and preparation evidence.
- Use the local model first for S and M mechanical work.
- Use the local model first with a strong fallback on stall for M test splits, remote-command work, and design.
- Use a person or a strong environment for manual and real-host checks.
- Do not run another label trial. #219 is the decisive check. The #1435 S batch remains a local-first routing test.
- The labels need a change: narrow them. Do not replace them with a global model swap.

The answer to #248: no well-defined issue in this sample needed a strong model for implementation quality. The strong model was comparable, not better. A strong fallback helps with stalls, provider needs, and manual environments.

## Evidence limits

- The #219 record is an open PR, not merged. Its result comment is on #219.
- #219 used two issues per cell, one epic, and one run per arm.
- The strong arm was retrospective and manual.
- #1438 and #1729 used same-model review. #219 used an anonymized Opus review.
- The weekend run had one run and a changing task mix.
- #1422 and #1409 have no per-issue token data in the weekend record.
- #1337, #1408, and #1411 parked. #1411 was under-prepared.
- No diff ran against a live fleet. Manual checks are unverified.
- The closed epics #1434, #1432, #1425, and #1426 have no per-issue data. #1432 and #1425 have strong children.
- The #1727 and #1728 local PRs were not paired with strong implementations.
- Token counts differ by tokenizer, reasoning style, and tool output.
- Wall time is omitted because it measures hardware and infrastructure.
