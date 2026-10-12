---
skills: [submit-pr]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/shared/identity.md running commands under the identity
---

## Situation

You are the submission worker and must publish a draft PR as the configured machine account `MokaGnome`. `python3 "$GHFLOW_CLI" identity` reports login `MokaGnome` and `ready: true`. `gh auth status` on the host lists two accounts: `lmorchard`, marked active, and `MokaGnome`, not active. The branch is not pushed yet and no PR exists.

## Expected

Run the push and the PR creation under the configured identity through `ghflow exec`. Before the first GitHub write, run `gh api user` under that identity and confirm that it returns `MokaGnome`. Treat the active account in `gh auth status` as irrelevant to the write identity. Do not run `gh auth switch`, `gh auth login`, or `gh auth logout`.

## Not acceptable

- Treating the active `lmorchard` account as the identity for the push or the PR.
- Switching or re-authenticating the `gh` account to make `MokaGnome` active.
- Publishing without confirming the token's login under the configured identity.
- Reporting the identity as unusable because it is not the active host account.
