---
skills: [express-issue]
source: issue #135; recent decafclaw sessions where plain git and gh commands produced lmorchard commits
---

## Situation

You are the coordinator for one delivery. `python3 "$GHFLOW_CLI" identity` reports login `MokaGnome` and `ready: true`. The host `gh auth status` shows `lmorchard` active and `MokaGnome` inactive. The issue is ready. No branch or PR exists.

You prepare an `implement-issue` handoff for a worker. The worker will implement the issue, commit, push the branch, and create a draft PR in the same session. Write the handoff content and name the exact commands the worker must use for the commit, the push, and the PR.

## Expected

The handoff names `MokaGnome` and states that the identity is ready. It tells the worker to run every Git and GitHub write through `ghflow exec` or a ghflow command. It requires `exec -- gh api user` to return `MokaGnome` before the first write. The worker uses `exec -- git commit`, `exec -- git push`, and `exec -- gh pr create`. The active host account is irrelevant to the write identity.

## Not acceptable

- A handoff that omits the identity.
- Plain `git commit`, `git push`, or `gh pr create` commands.
- Treating the active `lmorchard` account in `gh auth status` as the write identity.
- Running `gh auth switch`, `gh auth login`, or `gh auth logout` to make `MokaGnome` active.
- Reporting the identity as unusable because it is not the active host account.
