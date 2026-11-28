---
skills: [sweep-triage]
source: references/tasks/sweep-triage.md; decafclaw triage sweep, 2026-10-08
---

## Situation

You are defining issue #964, a Discord chat adapter, which is labeled `triage:needs-definition`. Its comments record the user's decision that Discord waits for #1007, an open issue that will introduce a transport interface, and #163, an open issue that will move the existing chat modules into a new package. The user has no open questions about Discord itself. The current runner constructs the Mattermost client directly.

## Expected

Stop full specification, because file targets written now would describe code that #163 and #1007 will change. Set native blocked-by relationships to #163 and #1007, optionally replace the body with an outline that names the interface contract it consumes, label the issue `triage:blocked`, and return it to the parent.

## Not acceptable

- Labeling the issue `triage:needs-input` when no user decision is open.
- Writing file and line targets against the current runner and labeling it `triage:ready`.
- Leaving it on `triage:needs-definition` with the blockers recorded only in text.
