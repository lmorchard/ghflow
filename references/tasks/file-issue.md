# File an issue

Publish the supplied draft with ghflow commands or `ghflow exec`, add the requested relationships and fields, and confirm the saved result. Do not repeat issue definition or begin implementation.

Apply [Authorization](../shared/authorization.md), [Evidence](../shared/evidence.md), and [Agent identity](../shared/identity.md#running-commands-under-the-identity) throughout. A request to file the draft, or an agreed flow that includes publication, authorizes issue creation. Before changing GitHub records, apply [GitHub writes](../shared/github-writes.md).

## Establish the requested changes

Read the draft and the relevant project instructions. Identify the repository, title, body, and requested metadata: labels, parent issue, project, and project fields. The draft can come from [define-issue](define-issue.md), another tool, or the user.

Take metadata from the user's request or the project's conventions, not from the draft alone. Leave unspecified optional values, such as board status, priority, assignee, and labels, unset.

If a missing decision changes what the issue means, return the question to the parent or user. Do not rewrite scope during filing.

## Inspect GitHub before writing

Run `python3 "$GHFLOW_CLI" identity`. Do not print credentials. Before the first write, confirm that `python3 "$GHFLOW_CLI" exec -- gh api user` returns the configured login. If authentication fails, report the required action.

Check the installed help for the operations you need. Some `gh` versions support parent links and project field names directly, without manual identifier lookups.

Search the target repository for an existing issue with the same request, including closed issues. A matching title does not prove a duplicate; compare intent and scope. If an equivalent issue exists, report it instead of creating another or replacing its body.

If a project is requested, read its identity and fields. Project titles can be ambiguous, so select the board by owner and number.

## Create the issue

Write the body to a UTF-8 file, separate from the title, and pass it with `--body-file`. Preserve the reviewed text, links, commands, and scope. Quote shell arguments safely.

Before the first write, note the operations you intend. A short session note is enough.

Create the issue with `python3 "$GHFLOW_CLI" exec -- gh issue create ...` in the explicit target repository. Include parent or project flags when their targets are unambiguous. Record the returned URL immediately.

Read the saved issue back. Make sure the title and body match the prepared content and the requested relationships exist. Add any missing metadata with `python3 "$GHFLOW_CLI" exec -- gh issue edit ...`. Set a requested project status only after project membership exists, with `python3 "$GHFLOW_CLI" board set-status ...` following [Board status](../shared/board-status.md).

Read back project membership even when no project was requested. A project's auto-add workflow can add the issue on creation. Report membership that nobody requested, and return the choice to remove it to the parent or user.

Establish a parent through the native relationship. Do not edit the parent body or add a comment to create the link. Preserve unrelated metadata.

## Resume after an error

If an issue URL was returned, inspect that issue first. If not, search recent issues and compare their content with the draft before you create anything. If only the parent link or board update failed, retry that step on the existing issue.

## Confirm and report

Read back the title, body, parent relationship, project membership, and requested fields. Report the issue URL and the confirmed changes. Report failed or uncertain steps with what is needed to resume.

Filing does not show that the issue is ready for implementation or that any test passes. If trial notes were requested, record what you learned about the tools without copying live board status into general documentation.
