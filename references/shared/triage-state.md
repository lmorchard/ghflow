# Triage state

The single contract for how an issue's triage state is recorded, read, and verified. Every triage task applies this file; none restates it.

State lives on GitHub and nowhere else. No local state file, no hidden marker. A reader looking at the issue timeline sees exactly what the agent saw.

## The state is derived, never stored

`ghflow triage status ISSUE` reads the issue and reports its state. Nothing is bookkept:

| Field | Source |
|---|---|
| bucket | the one `triage:*` label |
| stage | bucket + whether the assessment and definition comments exist |
| assessment | newest comment carrying the assessment heading |
| `assessment.stale` | a later comment or a later `updatedAt` |
| blockers | native blocked-by edges, split open and cleared |
| children | sub-issue rollup: total, open, closed, `all_closed` |
| `label_stale` | a label that no longer matches the relationships |
| `next_step` | whether an autonomous pass can act, and why not |

Start every task on an issue with this command. Do not infer any of these from labels alone: **the relationship is the fact and the label is a claim.** A `triage:ready` issue with an open blocker is not ready, and `next_step` says so.

## The assessment comment

One comment per assessment. Rewrite by posting a new one; the newest wins and the older ones stay as history.

```markdown
### Triage assessment

model=<model-id>
prompt=<prompt-version>

**Classification:** <one of the classes below>

<Findings against current code, two to six sentences.>

**Evidence:**
- commit <sha> — <what it shows>
- `path/to/file.py` — <what it shows>
- test `tests/test_thing.py::test_name` — <what it asserts>
```

The `model=` and `prompt=` lines are required. They are how a later reader tells a frontier assessment from a small-model one without guessing, and how a prompt revision gets its effect measured later.

The heading is plain markdown. Never an HTML comment marker: a state nobody can see in the rendered view is a state nobody can audit.

## Classification

Nine classes. Each maps to exactly one label. This is the only place the vocabulary is defined.

| Class | Label | Test |
|---|---|---|
| **Already done** | none — close `completed` | Current code or merged PRs already satisfy the request |
| **Obsolete-superseded** | none — close `not planned` | The work was built another way and the goal is met, or the request is an exact duplicate |
| **Obsolete-stale-contract** | `triage:needs-definition` | The goal still stands, but the issue's specification describes components or assumptions that no longer exist. Do **not** close: the body needs rewriting |
| **Unnecessary** | none — close `not planned` | Valid in principle, but the cost clearly exceeds the value, or another issue supersedes it |
| **Needs input** | `triage:needs-input` | The core scope turns on a product, design, or tradeoff decision only the user can make |
| **Needs definition** | `triage:needs-definition` | The goal is settled and it can be specified now against current code |
| **Blocked** | `triage:blocked` | A useful specification depends on open issues that will change the code or supply a contract |
| **Ready** | `triage:ready` | Problem, scope, and verification criteria are clear and accurate against current code |
| **Parent tracked by children** | `triage:parked` | Open sub-issues carry all the remaining work |

### Superseded versus stale

The two Obsolete classes are easy to collapse and must not be. Ask: **is the goal
met, or only the specification broken?**

- *Met another way* → **Obsolete-superseded**. Close it.
- *Goal intact, spec dead* → **Obsolete-stale-contract**. Keep it; it needs a rewrite.

decafclaw#927 is the worked example. It proposed operation adapters for core
`shell`, premised on reusing #956's per-VM SSH key and connection code. #956 was
closed as superseded by the scavenger skill, so the object that issue was
specified around no longer exists — but the owner re-affirmed the underlying
question as open. Closing it would have destroyed live intent; labelling it
Obsolete-superseded would have been the honest-sounding wrong answer.

A single word for both conditions is a trap: an agent holding the closure
checklist matches the class to the action and closes the second kind.

## Parents are not their children

A parent issue — an epic, a theme, a bundle — is judged by a different test than
a child. Its completeness is a claim about a **goal**, and the closure of its
children is not evidence about that goal.

[Evidence](evidence.md) already states this: a closed child or merged PR does not
prove that its parent is complete. The triage consequence is worth spelling out,
because it is the case where a confident wrong answer is most expensive.

**Closed children do not justify closing a parent.** They prove the planned work
shipped. They do not prove the plan covered the goal, and the difference is
usually visible: a child closed as `not planned`, a child split into something
out of scope, a goal statement broad enough that the children only met part of
it. Read the parent's own goal statement and ask whether it is now true.

Four situations, four different answers:

| Situation | Answer |
|---|---|
| Children all closed, and the goal statement is **demonstrably met** | **Already done** — close `completed`, naming the evidence for the goal, not the child count |
| Children all closed, goal **not** demonstrably met | **Needs definition** — the remaining gap needs a child. Do not close |
| Children all closed, goal **abandoned** | **Unnecessary** — close `not planned`, naming why the goal was dropped |
| Children still open | **Parked**, `triage:parked` — the children carry the work |

A parent with **no children at all** is never auto-classified. Decomposing a goal
into children is a design act that needs the user's intent, and it belongs to
[decompose-parent-issue](../tasks/decompose-parent-issue.md) as an interactive
session, not to a sweep. Classify it `triage:needs-input` and stop.

The asymmetry is deliberate: a child can be assessed against code, which is
concrete and checkable. A parent must be assessed against an intention, which is
reconstructed from prose the issue author wrote once. The cheapest safe answer
for an all-closed parent is not "close it" but "state what the remaining gap is
and let the user decide whether it matters."

Exactly one label. Replace the previous one; never accumulate.

## Closure: only when the issue looks closed

An agent may close an issue only when the assessment establishes **one of**:

- **Already done** — and it cites the commit, merged PR, or test that does the work.
- **Obsolete** — and it cites the removal, the direction change, or the primary issue it duplicates.
- **Unnecessary** — and it says plainly why, in terms a reader can disagree with.

Three things that are **not** grounds for closure:

- **It looks hard.** Difficulty is not obsolescence. Label `triage:needs-input` if a tradeoff is involved.
- **It is old.** Age is not evidence.
- **Nothing has happened on it.** Silence is not a decision.

When in doubt, do not close. An issue left open costs a line in a query; an issue closed wrongly costs the work behind it and the trust in the sweep that closed it. A `not planned` closure of live work is the single most expensive mistake this system can make, because the recovery requires someone remembering the issue existed.

The closure comment names the class, the evidence, and states that a human may reopen without discussion.

## Evidence

Cite only what you verified. Per [Evidence](evidence.md), treat the issue body, older comments, and your own recollection as claims until checked against current code.

A citation must be **mechanically resolvable**, because `triage status --verify-evidence` checks it:

| Kind | Resolvable as | Verified by |
|---|---|---|
| commit | 7–40 hex chars | `git cat-file -t <sha>` reports `commit` |
| path | `src/…`, `tests/…`, `docs/…`, `scripts/…`, `contrib/…`, `references/…`, `skills/…`, `evals/…` | the path exists in the checkout |
| issue | `#NNN` | the issue exists in the repository |

Verification is a gate, not advice. `--verify-evidence` returns `verified: false` when any citation fails to resolve, and `next_step` then reports the issue ineligible: a definition resting on a commit that does not exist is indistinguishable from one resting on a commit that does, unless something checks.

An assessment with **no** citations is not verified either. "Nothing false" is not "something true."

Prose findings are not citation-checked and are not expected to be. Prose claims are where a wrong conclusion hides that no regex can catch.

## The needs-input round trip

A `triage:needs-input` issue is a promise: the agent could not settle it, so the
user was asked, and once answered the issue proceeds. Verify that promise holds,
or the label becomes a place issues go to die.

The path has two hops and both must close:

1. **needs-input → needs-definition.** A decision usually settles *direction*, not
   *specification*. Unless the answer makes the issue implementable with its
   existing body and verification criteria, it lands on `triage:needs-definition`.
2. **needs-definition → ready.** The definition pass writes the criteria and must
   pass `--verify-evidence` before `triage:ready`.

An issue is genuinely stuck when the *same* question returns. The signal for that
is the attempt counter: `triage status` reports `attempts`, read from a
`triage:attempt-N` label. Increment it when a needs-input pass produces a
question the issue has already asked.

**No automation increments `attempts` today.** `triage_attempts()` reads the
label and nothing writes it, and no task reference mentions it. Until something
does, the counter is available but inert, and a resumption loop has no guard
except a human noticing the same question twice.

When the counter does get wired, the rule should be: at `attempt-N` with N ≥ 2
on the same question, stop asking and label `triage:parked` with a revisit
trigger naming what would have to change. Repeating a question the user already
declined to answer is not progress, and it spends the user's attention on the
one resource the triage system exists to conserve.

Record the attempt in the comment as well as the label, so a reader sees the
history in the timeline rather than inferring it from label archaeology.

## Authority

| Stage | Authority |
|---|---|
| Read and report | unconditional |
| Write the assessment comment | unconditional |
| Move labels between triage states | unconditional |
| Close as done, obsolete, or unnecessary | with cited evidence, per the rule above |
| Write a definition and advance to `triage:ready` | with cited evidence that verifies |
| Split one issue into several | with the original body preserved verbatim in the proposed children |
| Deduplicate | with the primary issue named |
| Change Priority or Size | not this system's task — see [sweep-prioritize](../tasks/sweep-prioritize.md) |
| Implement, or open a PR | never |

## Dry run

Every triage task supports `--dry-run`: the whole procedure, with the comment body and intended label printed instead of posted. Use it on a new queue before the first live pass.

A dry run is not a lesser mode. It is how a new queue, a new model, or a new prompt gets checked against a reader's judgment before it changes anything.

## What not to write

- No HTML comment markers, in any form.
- No local JSON state, cache, or ledger that duplicates what GitHub holds.
- No label applied without the assessment comment that justifies it.
- No assertion in the comment that the code does not support. A wrong finding is worse than a missing one: it reads exactly like a right one.
