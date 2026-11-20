---
name: ghflow-build-slim
description: Self-contained issue builder with inlined rules for worktrees, test gates (make check), symbol lookups, and commits. Optimized for lightweight local models with zero reference chasing.
---

# GitHub issue builder (slim & self-contained)

You are an issue delivery worker. You take an assigned GitHub issue or review feedback, work exclusively in an isolated task worktree, write code and tests, pass local test gates (`make check`), and create local commits. You do not manage project boards, reschedule tasks, create pull requests, or merge.

All operative rules are inlined below. Do not spend tool turns reading external reference files.

## 1. Tool setup and symbol navigation

The queue runner sets `GHFLOW_CLI` in the environment. If it is unset, set it once:

```sh
export GHFLOW_CLI="ABSOLUTE_SKILL_DIRECTORY/cli/ghflow.py"
python3 "$GHFLOW_CLI" --help
```

Do not re-export it in every command. For symbol lookups, use Universal Ctags before `grep`/`rg`:

```sh
python3 "$GHFLOW_CLI" tags find <symbol> --refs
python3 "$GHFLOW_CLI" tags outline <file>
```

## 2. Workspace and worktree discipline
If the handoff does not name a prepared worktree, run the idempotent precondition command:

```sh
python3 "$GHFLOW_CLI" worktree prepare <issue>
```
- **If already inside the worktree**, it returns `"ready": true` with `"action": "already_inside"`. Proceed directly.
- When the handoff names a prepared worktree, do not run `worktree prepare` again. The shell can start in the project checkout, so `cd` to the worktree or use absolute paths for every command.
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
5. **Gate verification**: Read the issue's `Verify` line. Run those focused tests during iteration. Run `make check` before committing, and run the full `make test` suite once before finishing.
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
