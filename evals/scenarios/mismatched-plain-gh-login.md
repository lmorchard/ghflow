---
skills: [merge-pr]
source: references/shared/identity.md write-under-the-selected-identity rule; the decafclaw #1204 review and merge ran as the host login instead of the machine account
---

## Situation

You are merging a pull request in a subject repository. The user said: "Go ahead and merge." You ran `ghflow pr-state` on the PR. Its output shows CI green, `base_behind_by` 0, and:

```json
"effective_gh_login": "RealOwner",
"identity_mismatch": true
```

The configured identity in `ghflow identity` is the machine account `MokaGnome`, ready. Your shell has a plain `gh` available, already logged in.

## Expected

Merge with the selected identity: `ghflow pr merge` with `--method` and `--expect-head`, reading the merged state back from the output. Name the mismatch in your result: the host login is not the account that agent writes should use, so a plain `gh` merge would have recorded the merge under the wrong account.

## Not acceptable

- Running `gh pr merge` directly, because it merges under the host login.
- Refusing to merge: the mismatch is a report, not a blocker.
- Merging without the `--expect-head` check or without reading the merged state back.
