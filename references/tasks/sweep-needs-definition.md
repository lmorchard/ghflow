# Sweep issues needing definition

Turn `triage:needs-definition` issues into specifications that are concrete enough to implement against current code. The distinct work here is **research and writing**; the classification and the promotion gate follow [Triage state](../shared/triage-state.md).

Apply [Triage state](../shared/triage-state.md), [Triage labels](../shared/triage-labels.md), [Authorization](../shared/authorization.md), and [Evidence](../shared/evidence.md). The parent coordinates; subagents research and write following [Agent identity](../shared/identity.md), and [GitHub writes](../shared/github-writes.md) before changing records.

## List pending issues

```bash
python3 "$GHFLOW_CLI" triage list needs-definition --repo OWNER/REPO
```

If none carry the label, report that the accepted backlog is fully defined and stop.

## Define each issue

Work in bounded slices of 2 to 5. For each issue, dispatch a subagent to apply [Define an issue](define-issue.md), giving it the issue, the current evidence, and the existing authorization.

Start from `ghflow triage status ISSUE` and read the existing assessment. Build on a finding whose source and revision still apply rather than repeating it; recheck it if either has changed.

Use [Decisions](../shared/decisions.md) when facts or choices are missing. Return material product decisions to the parent instead of choosing them in the sweep.

Three outcomes while defining:

- **A decision is needed.** Stop. Apply `triage:needs-input`, post the focused question, return to the parent. Do not choose for the user.
- **The work depends on another open issue** that will change the code or supply a contract. Record the native blocked-by relationship, apply `triage:blocked`, optionally replace the body with an outline, and return. If only part waits, propose a split instead.
- **The definition is solid.** Continue to promotion.

Keep each definition proportional to its goal and its evidence. A definition that restates the issue at length is not more specifiable than the issue was.

## Promote

1. Update the body with the reviewed definition.
2. Verify the evidence before promoting — this is the gate, not a formality:

   ```bash
   python3 "$GHFLOW_CLI" triage status ISSUE --repo OWNER/REPO --verify-evidence
   ```

   If `evidence.verified` is false, do **not** apply `triage:ready`. Leave `triage:needs-definition`, and post a comment naming each citation that did not resolve so the next pass can repair it.
3. On verified evidence, replace `triage:needs-definition` with `triage:ready`.
4. Post a brief comment linking the revised body, per the assessment format.
5. If the issue belongs to a parent theme, update the parent's rollup comment.

## Return

Report per issue: number, title, resulting state, the definition's boundary, any unresolved dependency, and the next useful step.

State which citations verified and which did not. A sweep that reports "all defined" while skipping verification has reported nothing a reader can use.
