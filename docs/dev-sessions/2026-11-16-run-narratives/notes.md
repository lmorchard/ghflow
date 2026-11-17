# Run narratives for unattended delivery (#156)

## Resume here

- Goal: publish a run narrative to GitHub so a remote operator sees progress, step findings, and the run result without the local notes directory.
- Issue: https://github.com/lmorchard/ghflow/issues/156
- Worktree: `.claude/worktrees/issue-156-run-narratives`, branch `issue-156-run-narratives`, base `origin/main` `ecb43cf`.
- Decisions (Les, 2026-11-16): use GitHub Discussions ("Lab Notebook" category) with native issue checkpoints as fallback; add the proposed one-turn model summarization per step. No merge authorization.
- Current state: implementation complete; `make check` passed (142 tests). Live discussion posting verified on 2026-11-16.
- Live result: `lmorchard/ghflow` now has Discussions enabled with the `Lab Notebook` (`lab-notebook`) category; discussion #165 "Run notebook 2026-11-16" was created and a comment appended, both read back. The existing token created the discussion, so `write:discussion` is not required for repository discussions with a `repo`-scoped token.
- Fix found in live use: a created discussion keeps its body on `Discussion.body`, not in `comments`. The read-back now checks `body` and `author`; the first live create reported exit 2 until this fix.
- Delivery: PR #166, head `35bf74e`, draft. Hosted `check` passed.
- Review (fresh context, same model `otari-mozilla/deepseek/deepseek-v4.1-flash-1017`): verdict `findings` on `35bf74e` with one blocking finding (a successful retry posted no note) and notes.
- Corrections: post the retry note; delete the summary session; drop NUL bytes and catch any spawn failure; print "posted" only after a post; document the notebook in `docs/setup.md`.
- Declined note: reading post-session state for the note costs an extra GitHub read per step; the next observation shows the PR.
- Final review of `5bd1bf8`: blocking finding that a bytes `TimeoutExpired.output` could raise out of the fallback. Fixed in `fe8e455` by decoding bytes; the regression test now puts the truncated UTF-8 before the session line so it fails on the pre-fix code.
- Base moved to `origin/main` `6ab8f8e` (PR #167). Merge `4b15310` resolved `cli/test_ghflow.py`, `scripts/run_queue.py`, and `scripts/test_run_queue.py`, keeping `publish_committed` and both notebook notes.
- Current head: `4b15310` plus the test-ordering fix; `make check` passes and hosted `check` was green at `4b15310`.
- Next action: ready submission with the reviewed head and board target project 12.

## Verified facts (2026-11-16)

- `repos/lmorchard/ghflow` reports `has_discussions: false` and no categories.
- MokaGnome token scopes: `gist, project, read:org, repo, workflow`; no `write:discussion`.
- MokaGnome repository permission: `push`, `triage`; no `admin`, so the machine account cannot enable Discussions.
- `decafclaw` `Lab Notebook` category (`lab-notebook`) reads fine, so category reads need no extra scope.
- Finding #846 (agent-sessions): `createDiscussionCategory` is not a GraphQL mutation; categories need manual creation.
- The runner keeps session logs and handoffs under `~/.local/state/ghflow/notes/runner-*`; the run summary is printed only.

## Blockers for live verification

1. Enable Discussions on `lmorchard/ghflow` (`PATCH repos/lmorchard/ghflow has_discussions=true`, needs admin).
2. Create the `Lab Notebook` (`lab-notebook`) category in the repository settings.
3. ~~Add `write:discussion` to the token~~ Not needed for repository discussions: a `repo`-scoped OAuth token created and appended live. The earlier scope finding applies to team discussions or a different token type.

## Design

- CLI: `discussion post --category SLUG --title TEXT --body-file FILE` finds an open discussion by exact title in the category, creates it when absent, appends a comment otherwise, and reads the write back. Exit 3 means Discussions are unavailable (disabled, missing category, missing scope) so the runner falls back without failing.
- CLI: `issue comment ISSUE --text FILE` posts and reads back a native checkpoint.
- `scripts/narrative.py`: builds the session excerpt (capped tail), runs one summarization turn through the session model, and posts start/step/finish notes. A failed model call falls back to deterministic facts; an unavailable notebook disables further discussion calls for the run and prints why once.
- Runner: prepares the day's thread, posts an issue checkpoint when implementation starts, appends a note after each session attempt, appends the run result.
