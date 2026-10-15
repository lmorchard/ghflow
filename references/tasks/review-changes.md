# Review changes

Assess proposed changes against their issue and the current code. Report defects and missing evidence without modifying the implementation. The next task assesses and addresses the findings.

Read this reference and your handoff first. Read [Review](../shared/review.md) before you set up the reviewer and record model identities, and [Evidence](../shared/evidence.md) before you report findings and checks. Open [GitHub writes](../shared/github-writes.md) only before you change a GitHub record, which a review rarely does.

Apply [Working context and tool output](../shared/context.md) to selective source reads and complete evidence with concise output.

## Set up the reviewer

The parent starts this review in a fresh context. It supplies the repository, issue, project instructions, and exact base and head commits. Give the reviewer the necessary facts, not the author's conversation or conclusions.

For an unpublished head, also require the supplied checkout path and publication state. Verify the supplied base and head with local Git in that checkout, following [Evidence](../shared/evidence.md#verifying-a-commit). Reject a missing commit, wrong checkout, or mismatched expected head and return it to the parent. For a published PR, read its current head with `pr-state` and verify that published commit remotely.

Select the reviewer model explicitly through the available tool configuration. It must differ from the implementation model unless a [user-approved exception](../shared/review.md#user-approved-exceptions) permits this review method. Record both identities, their sources, and any applicable exception. If the agreed plan waives this review, return that status instead of starting an unrequested substitute.

## Establish the scope

Read the issue, project instructions, and the diff between the supplied commits. Inspect related code where it affects the changed behavior. Earlier work does not need to have used these skills.

Treat the implementation report as claims, not as your conclusion. Examine tests before you accept their stated coverage.

Keep the implementation checkout unchanged. If tests generate files or modify data, use an isolated temporary copy. Do not change expected results to make the reviewed code pass.

For a published PR, read its current head, reviews, and top-level comments with `pr-state`, described in [CLI results](../cli.md#reading-pr-state). Read the comment and review bodies. A `null` part is unread, not empty; read it again or report incomplete retrieval. Do not report that a PR has no comments or reviews unless a read returned an empty list.

## Examine the change

Focus on these questions:

- Does the change satisfy the issue without changing the agreed scope?
- Do callers, error paths, permissions, and data handling remain correct?
- Does the change depend on library or runtime behavior that a comment, the notes, or your recollection asserts? Confirm that behavior with a short command in the project's interpreter before you reason from it, as [Evidence](../shared/evidence.md#sources-and-revisions) requires.
- Do tests establish the intended behavior rather than a nearby substitute? For each new assertion, check whether the pre-change output or a neighboring code path also satisfies it. Where the environment permits, run the test with the covered behavior disabled in an isolated copy; a test that still passes does not cover it.
- Do builds and generated files match the code that users receive?
- Do documentation and setup instructions match the change?

When the change touches a shared function, interface, or branch, find every caller, not only the callers in the diff. For each caller, compare behavior before and after the change for success, empty, and malformed inputs or responses.

Run useful targeted checks where the environment permits. Record setup failures separately from product defects. Passing tests do not prove that no defects exist.

Evaluate existing review findings instead of accepting them. Distinguish a demonstrated defect from a question, a preference, or an unrelated existing problem. Avoid speculative redesign outside the issue.

## Return findings

Separate findings from notes. A finding is a demonstrated or reasoned defect, a deviation from the agreed scope, or missing evidence; it has a file and lines, a triggering condition, an observed or reasoned result, and a practical impact. Explain how it conflicts with the intended behavior and suggest a correction without implementing it. A style preference, a naming or wording choice, a documentation or session-file convention, or the phrasing of the PR description is a note: list notes separately under that label, with the suggestion, and do not call a note disputed. The coordinator settles notes as routine choices; a note does not go to the user.

If you found no actionable defects, say so. Do not invent a finding to justify the review. Either way, state which callers and paths you traced and which behavior you did not test. A favorable review covers only what it traced.

Return the reviewed base and head, the model identities and their sources, the findings, and the checks you ran. Give your own model as the ID your runtime states to you, not a configured or default model. If the head changed during review, say that the result covers the earlier commit. Keep the report short, in the conversation or a requested location. Return user decisions to the parent.

Do not post a GitHub review without authorization to publish it. Do not edit code, resolve threads, approve a merge, or start a repair loop.
