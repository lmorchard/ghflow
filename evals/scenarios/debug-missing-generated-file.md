---
skills: [implement-issue]
source: references/shared/debugging.md
---

## Situation

A build did not produce `src/message_types.py`. Two explanations are plausible: the generation step did not run, or it wrote to a different path. `make check` failed once at the import. You have not inspected the build target or the generator output.

## Expected

State one hypothesis with its observations and uncertainty. Choose one small experiment that distinguishes the two explanations, such as checking whether the generation target ran and where it wrote. Record the actual result before editing. Then correct the cause or report a blocker.

## Not acceptable

- Rerunning the full build or check without a new reason.
- Editing paths or adding the file by hand on a guess.
- Claiming the problem is fixed without a result that distinguishes the causes.
