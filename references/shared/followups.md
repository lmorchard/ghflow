# Follow-up findings

A worker records an out-of-scope finding instead of expanding the current task. The coordinator files one issue for each independent finding.

## Record a finding

Name these facts:

- The source: the issue or pull request URL, the commit, and the file and lines.
- The evidence: a short quote or a command result.
- Why the finding is outside the current scope.
- Whether it blocks the current result.

Do not fix the finding in the current task. A worker does not file an issue unless its handoff authorizes it.

## File the issue

- Search open issues for the same finding. Reuse an existing issue.
- File one issue for each independent finding. Keep related findings in one issue.
- Use this body: Problem, Evidence, Source, Scope, Acceptance.
- Link the source issue or pull request and the parent issue.
- Apply the triage label that matches the state: `triage:ready` or `triage:needs-attention`.
- Record the issue URL in the parent issue or the run report.

## Report the follow-ups

- The coordinator writes `followups.md` in the run notes directory. Use one bullet for each finding. State the filed issue URL or why it waits.
- The runner prints this file in its run summary under "Follow-ups".
- Do not close the parent while its required findings are unrecorded.
