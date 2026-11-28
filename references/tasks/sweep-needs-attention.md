# Sweep issues needing attention

Work through `triage:needs-attention` issues in a live session with the user, one issue at a time. Each session ends with that issue in a terminal state.

Apply [Triage state](../shared/triage-state.md), [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md). The parent agent conducts the conversation; subagents execute writes following [Agent identity](../shared/identity.md), and [GitHub writes](../shared/github-writes.md) before changing records.

## This is a live session, not a sweep

Do not batch. Do not cluster issues to save the user turns. Do not present a list and ask them to work through it.

Take one issue. Finish it. Then ask whether to continue.

The reason is not politeness. A needs-attention issue turns on exactly one decision, and that decision needs the agent's full research on that issue in front of the user when the question arrives. Clustering several issues into one presentation produces a comparison across issues instead of a decision about one, and the answers come back shallower than the queue deserved.

## List pending issues

```bash
python3 "$GHFLOW_CLI" triage list needs-attention --repo OWNER/REPO
```

If none carry the label, report that nothing is waiting on the user and stop.

## Prepare before speaking

Do all of this before the first message about an issue. The user should never be asked to read code, open a diff, or reason from raw evidence.

```bash
python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO
```

1. Read the issue, all its comments, and its latest assessment comment. If `assessment.stale` is set, re-assess first — the question may have moved.
2. Read the current code at the target revision. Confirm where the issue actually stands, not where the assessment said it stood when it was written.
3. Identify the **one** decision blocking readiness. If there are two, find which one gates the other and ask that first.
4. Work out what the evidence already settles. Anything discoverable is the agent's job, not the user's.

If preparation reveals the issue is actually closable, definable, blocked, or a split candidate, do that instead and say so. A needs-attention label is a claim, and preparation is where a stale claim gets caught.

## Present the decision

Give the user a short brief, then one question. The brief is four things:

- **The issue** — number, title, one sentence on what it asks for.
- **Where the code stands** — what exists now, in ordinary words, with no paths to open.
- **The decision** — the specific choice that blocks readiness, and why it blocks.
- **The recommendation** — a position, with the reason, and what changes if the user picks differently.

**Recommend.** The pass already researched this issue; withholding the conclusion and presenting a menu instead is offloading the work back onto the user. State a position and let them disagree.

Name uncertainty honestly. When the evidence genuinely does not separate two answers, say that rather than manufacturing false confidence in one. When it does separate them, say which and why.

Follow [Decisions](../shared/decisions.md) for what counts as the user's call versus the agent's. Reversible implementation choices are the agent's; anything that changes intent, scope, user-visible behavior, compatibility, cost, or permissions is the user's.

Ask one question. Wait for the answer. Do not write the next question until this one is answered.

## After the answer

The answer settles direction. Now finish the issue in this session:

1. **Post the assessment comment** recording the decision and its rationale, with evidence, per [Triage state](../shared/triage-state.md#the-assessment-comment). Put the reason in it, and why the alternative was not chosen.
2. **Write the definition.** Update the body with the scope, the file targets, and the verification criteria the decision implies. Do not leave this for a later pass.
3. **Verify the evidence:**

   ```bash
   python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO --verify-evidence
   ```

4. **Close out** with exactly one of:

| Outcome | Action |
|---|---|
| Defined, and `evidence.verified` is true | remove `triage:needs-attention`, apply `triage:ready` |
| The answer shows it is invalid, or not worth doing | close `not planned`, naming the reason, per the closure rule |
| Too broad, holding several separable goals | file the children per [Splitting](../shared/triage-state.md#splitting), then close the parent as Obsolete-superseded naming every child |

There is no fourth outcome. An issue that leaves the session still unspecified is a session that did not finish.

**If the evidence fails to verify**, do not apply `triage:ready` and do not go back to `needs-attention`. Remove the label and leave the issue `untriaged`, with a comment naming each citation that did not resolve. That is a retry, not a question for the user, and the next autonomous pass will pick it up.

If the answer opens genuinely new technical work that could not have been foreseen, that is a new issue — file it `untriaged` and close this one out. Do not chain the session.

5. **Update the parent rollup** if the issue belongs to a parent theme.

## Continue or stop

After an issue reaches its terminal state, report it in one short line and ask whether to continue to the next one. Do not start the next issue unprompted.

If the user asks to stop, stop. The issues still carrying the label are unchanged, and the next session picks them up.

## Return

Report per issue: number, title, the decision the user made, the outcome, and the comment URL.

List anything that ended `untriaged` because of a failed citation separately, so a reader can tell a retry from a completion.
