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
Post the verdict as a native PR review:

```sh
python3 "$GHFLOW_CLI" review verdict PR_URL --verdict clean|findings|blocked --body-file VERDICT_FILE --model MODEL_ID
```

Verdict rules:
- Post the verdict as a native PR review with `review verdict PR_URL --verdict clean|findings|blocked --body-file FILE --model MODEL_ID`. The tool writes a visible `## Verdict: ...` heading and records the reviewed head on the review object. Do not write HTML comment markers.
- `clean`: No blocking findings. If `## Blocking findings` is empty or None, verdict MUST be `clean`, even if non-blocking notes appear under `## Notes`.
- `findings`: Actionable blocking defects that a builder can resolve.
- `blocked`: Scope or requirement blockers requiring human decision.
