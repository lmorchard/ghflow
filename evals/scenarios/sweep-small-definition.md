---
skills: [sweep-triage]
source: https://github.com/lmorchard/gh-project-workflow/issues/31
---

## Situation

The open issue is labeled `triage:needs-definition`. It asks for an error from `board set-status` when the supplied status is invalid. The issue says the command must print the valid status choices and leave the board unchanged. The maintainer confirmed that it must also exit with a nonzero status. Current code already rejects an invalid value and exits with a nonzero status, but its error does not print the valid choices. The maintainer authorized updating this issue, its triage labels, its ready comment, and a parent rollup if one exists.

## Expected

Define the missing error detail as a small issue. Preserve the stated behavior and confirmed decision. Use the definition process to choose suitable evidence and verification criteria. Do not require a fixed section structure, speculative file or method targets, or a prescribed test technique when the observable result is enough. Publish the reviewed definition and apply the ready outcome within the stated authorization.

## Not acceptable

- Expanding the issue into unrelated error handling or a broad board redesign.
- Requiring exact files, methods, or test names without evidence that they are needed to define the behavior.
- Treating a scenario answer as proof that the implementation is correct.
