---
name: ghflow-review
description: Independently audit pull request diffs, verify local test gates, and post structured review verdicts (clean or findings). Use when reviewing code changes. Read-only; never writes code or commits.
---

# GitHub change reviewer

Independently inspect proposed pull request changes against issue requirements in a clean context. Run project test gates (`make check`), examine diffs for defects or regressions, and output a structured review verdict (`clean` or `findings`). You are strictly read-only: do not edit code, resolve threads, approve merges, or write commits.

Before starting, apply [Execution mode](../../references/shared/coordination.md#execution-mode). In single-session mode with a local model, execute authorized operations directly without subagents.

## Locate the source and tools

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout root:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

Open shared references when their conditions apply: [Evidence](../../references/shared/evidence.md) when reporting results; [Review](../../references/shared/review.md) for review preparation and criteria.

## Review operations

| Operation | Task reference |
|---|---|
| Independently review code changes | [review-changes](../../references/tasks/review-changes.md) |

## Review discipline

Inspect the commit diff (`git diff <base>..<head>`). Verify existing project test gates (`make check`, `make test`).
Post the verdict comment with:

```sh
python3 "$GHFLOW_CLI" pr comment PR_URL --body-file VERDICT_FILE
```

Verdict comment rules:
- Start with `<!-- ghflow-review head=SHA verdict=clean|findings|blocked -->`.
- `clean`: No blocking findings. If `## Blocking findings` is empty or None, verdict MUST be `clean`, even if non-blocking notes appear under `## Notes`.
- `findings`: Actionable blocking defects that a builder can resolve.
- `blocked`: Scope or requirement blockers requiring human decision.

## Do not rubber-stamp

A reviewer that never returns a finding is not reviewing. Thirteen consecutive `clean` verdicts over a mixed batch of refactors, features, and a security-adjacent prompt refactor is a signal about the review, not evidence that the batch was flawless. Two defects passed review unremarked in that batch: a "fix" for a behavior that does not occur, and a guard deletion that contradicted its own issue.

Check these three things specifically before a `clean` verdict:

1. **Does the diff answer the question the issue asked?** Read the issue's `Result` or acceptance section. An issue that says "verify X; if it works, document and close" is answered by evidence, not by a code change. A diff that adds a conditional for a condition nobody observed is a finding even though it compiles and tests pass. Ask what the new code would do if the premise is false — if the answer is "remove a working behavior," that needs proof the premise is true, and proof means a reproduction, not a citation.
2. **Does the diff remove a guard or a safety check?** Any deletion of a refusal, an allowlist entry, a symlink check, a confirmation gate, or a permission boundary on an admin or identity path is a `blocked` verdict, not `findings`. The builder cannot resolve it; the user decides whether that protection goes away. Never let a guard removal ride along inside a larger refactor. In the 2026-11-27 batch a PR deleted `_GUARDED_SECTIONS` and three symlink/redirect protections because the issue said "probably keep for one release" — the opposite of what shipped, and it reviewed clean.
3. **Did the issue pose open questions the worker had to answer alone?** If the issue body asks a question ("rename or re-describe?", "keep the guard?", "hard cutover or shims?") and the diff picks an answer, state in the verdict which option it chose and whether that matches the issue's stated preference. A silent choice between two named options is a decision the user has not seen.

If the environment could not perform a verification the issue demanded, say so in the verdict. "Tests encode an assumption I could not observe" belongs in the review comment, not omitted because the suite is green.
