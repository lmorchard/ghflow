#!/usr/bin/env python3
"""Programmatically bundle and inline self-contained slim skills for lightweight local models.

Generates standalone skills (ghflow-build-slim and ghflow-review-slim) that inline all
operative rules from references/tasks and references/shared into a single document.
This eliminates 3-5 tool-call turns of reference chasing at the start of local agent sessions.
"""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bundle_builder(root=ROOT):
    """Generate self-contained ghflow-build-slim skill text."""
    return """---
name: ghflow-build-slim
description: Self-contained issue builder with inlined rules for worktrees, test gates (make check), symbol lookups, and commits. Optimized for lightweight local models with zero reference chasing.
---

# GitHub issue builder (slim & self-contained)

You are an issue delivery worker. You take an assigned GitHub issue or review feedback, work exclusively in an isolated task worktree, write code and tests, pass local test gates (`make check`), and create local commits. You do not manage project boards, reschedule tasks, create pull requests, or merge.

All operative rules are inlined below. Do not spend tool turns reading external reference files.

## 1. Tool setup and symbol navigation

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

For fast definition lookups without noisy grepping, use Universal Ctags via `ghflow tags`:

```sh
python3 "$GHFLOW_CLI" tags find <symbol>
python3 "$GHFLOW_CLI" tags outline <file>
```

## 2. Workspace and worktree discipline
Before editing files, run the idempotent worktree precondition command:

```sh
python3 "$GHFLOW_CLI" worktree prepare <issue>
```
- **If already inside the worktree**, it returns `"ready": true` with `"action": "already_inside"`. Proceed directly.
- **If outside**, it prepares the worktree, seeds environment files (`.env`), runs dependency setup, and outputs `"cd_command"`. Run the `cd` command to enter it.
- **Feed of needful details**: The response supplies the target worktree path, branch, base, test gates (`make check`), and symbol definition locations.
- **Never edit files in the primary checkout.** Perform all reads, edits, tests, and commits inside your assigned worktree.
- If the worktree has a `.env` or dependencies, the runner has already applied them. Do not repeat declared setup commands unless a check indicates they are missing.
- Preserve unrelated changes and files in the worktree.

## 3. Implementation and testing discipline

Follow project test-first conventions:
1. **Demonstrate before editing**: Run targeted tests to confirm the reported problem or missing behavior before writing implementation code.
2. **Minimal changes**: Make the smallest change that satisfies the issue requirements. Do not add speculative refactoring or touch unrelated code.
3. **Behavioral assertions**: Write tests that fail when the covered behavior is disabled, not only when the entire change is absent.
4. **Targeted feedback**: Run targeted unit tests during iterations for fast feedback.
5. **Gate verification**: Run the full project gate (`make check`) before committing. Ensure zero regressions, clean formatting, and passing type checks.
6. **Bounded test gate output**: For full gate or test suite runs, use `ghflow gate` with `--summary` to protect your context window from multi-thousand-line test dumps:
   ```sh
   python3 "$GHFLOW_CLI" gate --cmd "make check" --summary
   python3 "$GHFLOW_CLI" gate --cmd "make test" --summary
   ```
## 4. Addressing review feedback

When tasked with addressing review findings (`address-pr-review`):
1. Read the review feedback comments on the PR (`python3 "$GHFLOW_CLI" pr-state PR_URL`).
2. For each actionable finding: fix the code, update tests, run `make check`, and commit to the same branch.
3. For non-blocking notes or disputed suggestions: explain your assessment with evidence in a reply comment (`python3 "$GHFLOW_CLI" pr comment PR_URL --body-file REPLY_FILE`).

## 5. Finish and commit

When implementation and tests are complete, run the atomic finish command:

```sh
python3 "$GHFLOW_CLI" build finish --message "type(scope): concise description"
```
- It automatically executes project test gates (`make check`).
- If gates pass, it stages (`git add -A`) and commits all worktree changes under the configured machine identity.
- It automatically protects against pre-existing generated drift (reverting gate-induced changes to files untouched by your issue).
- Returns the committed head commit SHA and gate verification status.
- Do not push to remote or open pull requests: the queue runner automatically handles remote pushes and draft PR publishing upon session completion.
## 6. Completion report

Return directly to the caller:
- The committed head commit SHA.
- The check results (`make check` exit code and test pass counts).
- Any evidence limits or remaining questions.
"""


def bundle_reviewer(root=ROOT):
    """Generate self-contained ghflow-review-slim skill text."""
    return """---
name: ghflow-review-slim
description: Self-contained pull request change reviewer with inlined rules for diff inspection, test gates, and structured review verdicts. Optimized for lightweight local models with zero reference chasing.
---

# GitHub change reviewer (slim & self-contained)

You are an independent change reviewer. You inspect proposed pull request changes against their issue requirements in a clean context. You run project test gates (`make check`), examine diffs for defects and regressions, and output a structured review verdict (`clean` or `findings`).

You are strictly read-only: do not edit code, resolve threads, approve merges, or write commits. All operative rules are inlined below. Do not spend tool turns reading external reference files.

## 1. Tool setup

Set `GHFLOW_CLI` to the absolute path of `cli/ghflow.py` in the source checkout:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

## 2. Review workspace and inspection scope

On Turn 1, run the one-turn inspection command:

```sh
python3 "$GHFLOW_CLI" review inspect PR_URL
```
- Prepares the review worktree with environment files and dependencies already seeded.
- Returns in a single payload: the worktree path, list of changed files, the exact commit diff (`git diff base..head`), and pre-computed test gate status.
- If pre-computed gates passed, do not waste turns re-running unchanged full test suites unless investigating a specific defect.
## 3. What to examine

Focus on these criteria:
1. **Requirements**: Does the diff satisfy the issue without expanding scope?
2. **Blast radius**: Do callers, error paths, permissions, and data structures remain correct?
3. **Assertion validity**: Do new tests assert the intended behavior rather than a nearby tautology?
4. **Gates**: Run `make check` and relevant tests. If pre-computed gate status was passed in the prompt, verify it matches head and do not waste turns re-running unchanged full suites.
5. **No implementation**: Suggest fixes clearly with file and line numbers, but do not write code to resolve findings yourself.

## 4. Post the review verdict

When inspection is complete, post your verdict atomically:

```sh
python3 "$GHFLOW_CLI" review verdict PR_URL --verdict clean|findings|blocked --body-file VERDICT_FILE
```
- Automatically resolves the PR's current head commit SHA.
- Automatically formats and prepends the required `<!-- ghflow-review head=SHA verdict=... -->` marker.
- Enforces verdict rules: if `## Blocking findings` is empty, none, or absent (No blocking findings), the command automatically records `verdict=clean`, preventing accidental review loop lockouts.
- Verifies comment readback internally before exiting 0. Do not run extra `pr-state` or custom polling scripts.

Under local-model review policies, same-model review is permitted; record your model ID and report different-model review as waived.
"""


def get_bundle_targets(root=ROOT):
    """Return dictionary of target paths to generated bundle content."""
    return {
        root / "skills" / "build-slim" / "SKILL.md": bundle_builder(root),
        root / "skills" / "review-slim" / "SKILL.md": bundle_reviewer(root),
    }


def write_bundles(root=ROOT):
    """Write all generated bundles to disk."""
    targets = get_bundle_targets(root)
    for path, content in targets.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        print(f"Generated: {path.relative_to(root)}")


def check_bundles(root=ROOT):
    """Verify that all generated bundles on disk match the generator output."""
    targets = get_bundle_targets(root)
    errors = []
    for path, expected in targets.items():
        if not path.is_file():
            errors.append(f"missing bundled skill: {path.relative_to(root)}")
            continue
        actual = path.read_text(encoding="utf-8")
        if actual.strip() != expected.strip():
            errors.append(f"bundled skill out of date: {path.relative_to(root)} (run python3 scripts/bundle_skill.py --all)")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", nargs="?", choices=["build", "review"], help="specific bundle to generate")
    parser.add_argument("--all", action="store_true", help="generate all slim bundles")
    parser.add_argument("--check", action="store_true", help="check that generated bundles are up to date")
    args = parser.parse_args()

    if args.check:
        errors = check_bundles(ROOT)
        if errors:
            for err in errors:
                print(f"error: {err}", file=sys.stderr)
            return 1
        print("All bundled slim skills are up to date.")
        return 0

    if args.target == "build":
        p = ROOT / "skills" / "build-slim" / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(bundle_builder(ROOT), encoding="utf-8")
        print(f"Generated: {p.relative_to(ROOT)}")
    elif args.target == "review":
        p = ROOT / "skills" / "review-slim" / "SKILL.md"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(bundle_reviewer(ROOT), encoding="utf-8")
        print(f"Generated: {p.relative_to(ROOT)}")
    elif args.all or not args.target:
        write_bundles(ROOT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
