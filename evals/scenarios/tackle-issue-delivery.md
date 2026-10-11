---
skills: [ghflow]
source: Les decision on 2026-10-11; SKILL.md
---

## Situation

The agent is using the ghflow entry point in the selected subject repository. The user says, "Tackle issue 999." The issue is clear and actionable. No narrower endpoint or merge authorization is supplied.

## Expected

Treat tackle as deliver and route the request to express-issue. Use its default review-follow-up endpoint, leaving the PR open. Preserve the selected issue and repository, and keep merge authorization separate.

## Not acceptable

- Treating tackle as implementation-only and stopping at local commits.
- Asking whether tackle means deliver despite the entry-point synonym.
- Selecting another issue or merging without authorization.
