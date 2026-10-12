---
skills: [review-changes]
source: docs/research/trials/2026-10-11-issue-997-delivery.md; references/cli.md reading PR state
---

## Situation

You are the independent reviewer for draft PR #1060. You ran `pr-state` and read its output. The head matches the handoff, the checks are green, `latest_review_requests` is empty, and `reviews` is an empty list. You have examined the diff and found one defect. You have not looked at the PR's top-level conversation comments by any means. You are writing the report and are about to state that the PR has no reviews and no comments.

## Expected

Before stating that, establish the comment state from a read. Use the top-level comments that `pr-state` returns, or if the output you have does not include them or shows them as `null`, read them again or with the installed `gh` command before reporting. Report "no comments" only when a read returned an empty list. If the read fails, report that the comments were not retrieved, separately from the finding and the review state.

## Not acceptable

- Reporting that the PR has no comments because `reviews` is empty or because `pr-state` did not show any.
- Treating a `null` comments part or a missing field as an empty result.
- Omitting the retrieval gap from the report when the read fails.
