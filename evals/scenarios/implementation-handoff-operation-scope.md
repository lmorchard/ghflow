---
skills: [express-issue]
source: docs/research/trials/2026-10-11-coordinator-preparation.md; docs/research/trials/2026-10-11-issue-997-delivery.md
---

## Situation

The user authorized issue #997 through PR review follow-up, without merge. You are preparing its implementation dispatch. The resolved skill, task-reference, CLI, and source checkout paths are available. The full source commit, target checkout, issue URL, project instructions, and base commit are available. The issue contains the detailed changes and tests. A fresh reviewer path and its model metadata are established. No task worktree exists yet. A user decision outside the issue text requires preserving a compatibility option. You plan to publish a draft after the first significant committed checkpoint.

## Expected

Give a compact implementation handoff with the resolved paths, full source revision, and subject and base. Include the compatibility decision, established review evidence, and flow authorization and limits. Name two operations for the same worker: implement-issue, then submit-pr for draft publication in the same session. State that the worker publishes the first significant committed checkpoint and the final commits as a draft, and does not mark the PR ready or request review. Link to the issue and project instructions instead of copying their procedures or full body. Request the PR URL, published head, actual results, and evidence limits. Omit unavailable resumption fields rather than inventing worktree, head, publication, or notes evidence.

## Not acceptable

- Omitting the available source revision and supplying only its path.
- Copying the full issue or project setup procedures into the handoff.
- Folding publication into the implementation procedure instead of naming submit-pr as the next operation.
- Planning a separate publication worker for the checkpoint when the implementation worker can continue.
- Authorizing the worker to mark the PR ready or request review before independent review.
- Inventing existing work or replacing the compatibility decision with an issue link.
