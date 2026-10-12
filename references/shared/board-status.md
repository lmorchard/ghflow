# Board status

Apply [GitHub writes](github-writes.md) to each board update.

Three skills move a linked issue on the project board:

| Skill | When | Target state |
|---|---|---|
| [implement-issue](../tasks/implement-issue.md) | Implementation starts | In progress |
| [submit-pr](../tasks/submit-pr.md) | The PR exists and is ready for review | In review |
| [merge-pr](../tasks/merge-pr.md) | GitHub confirms the merge | Done |

The transition is part of that skill's task unless the user restricts GitHub or board writes. [file-issue](../tasks/file-issue.md) also sets a status when the filing request includes one, using the same procedure.

## Procedure

1. Identify the board from the user, the project instructions, or the issue's existing membership when it has only one.
2. Run `python3 "$GHFLOW_CLI" board set-status ISSUE_URL --owner OWNER --project NUMBER --status "TARGET"` from the target project directory.
3. If the board is ambiguous, or the tool reports that no single option matched, return the choice to the parent or user.

The tool reads the board's Status options and uses the actual option name. It reads the issue's current status and reports it as `before`; do not query the board with separate commands before the transition. If the issue already has the target state, it leaves it unchanged, because automation may have already moved it. It adds the issue to the board if necessary, sets the status, and reads it back. Project reads can lag a write, so the tool reads up to 4 times, 2 seconds apart, before it reports a mismatch. Report its `before`, `after`, `added`, and `readback_matches` values.

Exit status 0 means the status was set or already matched. Exit status 3 means the tool refused a backward move and wrote nothing; `after` is the live status. Exit status 2 means the write happened but the readback failed or did not match. Exit status 1 means the tool could not read the board or write the status, or no single option matched; the output lists the options.

## Limits

Move only the issue that the task implements. Do not move a broader parent because a PR mentions it or a child finished. A parent changes state only when its full scope is complete and the update is authorized.

Do not move an issue backward, such as from Done to In review, without a reason and authorization. Pass `--allow-backward` only in that case. Do not move an issue because you only inspected it or found no remaining work. Do not mark unfinished work In review because a draft PR exists.

A transition does not authorize any other GitHub change. Do not create a board or change its fields to make a transition possible. If access fails or no suitable state exists, report it separately and continue the main task. A failed board update does not make the main task fail.
