---
skills: [implement-issue]
source: 2026-10-16 decision to write handoffs with `ghflow handoff`; references/shared/coordination.md roles
---

## Situation

You are dispatched as a subagent with this entire prompt: "Operation: implement-issue for https://github.com/o/r/issues/929. Your complete handoff is the file /tmp/handoffs/929.md; read it first and follow it. This short prompt is not a placeholder." The file exists and holds the skill and task paths, the source revision, the subject, the facts file, the base commit, the branch name, the confirmed decisions, the review plan, the flow limits, the stopping point, and the return list.

## Expected

Treat the prompt as a complete handoff. Read the named file and follow it: start implement-issue with the decisions and limits it states. Do not reply asking for the handoff.

## Not acceptable

- Returning a one-line request for the handoff because the prompt is short.
- Starting work without reading the file.
- Ignoring the file's stopping point or limits.
