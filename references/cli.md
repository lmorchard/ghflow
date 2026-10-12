# CLI results for PRs and commits

Read this reference when using `pr-state`, local Git verification, or `verify-commit`.
The entry skill resolves `GHFLOW_CLI` to the source checkout CLI. Run commands from the target project directory.
These commands apply the configured [agent identity](shared/identity.md) to their GitHub reads.

## Reading PR state

Read a PR's state with `python3 "$GHFLOW_CLI" pr-state PR_URL`, run from the target project directory. It reports the current head, each check's state with required checks from rulesets, review requests from the timeline, and reviews with their commits. It matches a Copilot request to reviews authored by `copilot-pull-request-reviewer[bot]`.

`base_behind_by` is the number of base-branch commits that the head does not contain. A value of 0 means the head contains the current base tip.

`comments` lists the PR's top-level comments from every result page, each with its author, time, URL, and full body. These are the conversation comments on the PR, not inline review threads; `inline_comments` on each review counts those. An empty list means that the read succeeded and found none. Read the bodies yourself before you describe or dismiss them.

Use `latest_review_requests` to decide whether a review request exists and whether a later review answered it. `pending_review_requests` lists only reviewers that GitHub still shows as requested, and it can be empty while a request is live. Request events do not record a commit; after later pushes, compare the request time with the push times to decide which head it covers.

A part that the tool could not read is `null` and has an entry in `errors`. Exit status 2 means some parts failed. Treat a `null` part as unread, not as empty. The tool does not judge whether a review is favorable; read the review bodies yourself.

Invalid required values or collection entries produce an error for the affected part. If the primary PR response is invalid, the tool exits 1 without reporting a head. Optional read failures preserve the facts already read.

The `ci` summary reports automated project checks, or continuous integration (CI). `failing` takes precedence when a check failed, was canceled, or has an unknown state. Otherwise, `missing` reports a known required check without a result, and `pending` reports work that has not finished. `incomplete` means required-check discovery failed, and the observed checks show neither failure nor pending work. `green` requires successful required-check discovery and only passed or skipped reported checks. `none` means no checks were reported and no required checks were found.

When required-check discovery fails, `required_checks` remains `null`, affected checks have `required: null`, and `errors` records the read error. The command exits 2. A failed optional review or timeline read does not change the CI summary.

Individual nullable fields can be `null` without an error. A review can have no author, commit, or submission time. A review with no author does not match a review request. These nullable fields follow the [GitHub REST response schema](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json).

## Verifying a local commit

Use local Git verification for an unpublished commit that another agent must review in the supplied checkout.
Resolve the supplied identifier with `git -C "CHECKOUT" rev-parse --verify 'REV^{commit}'` and retain the full identifier it returns.
Resolve the supplied base with the same command before comparing changes.
Compare the resolved commit with the reported head and tested commit when they should match.
If an expected subject is supplied, compare it with `git -C "CHECKOUT" show -s --format=%s FULL_SHA`.
Resolve the reported branch with `git -C "CHECKOUT" rev-parse --verify 'BRANCH^{commit}'` and compare it with the expected head when the handoff makes that claim.
Reject a missing commit, wrong checkout, or mismatched expected head, and return the mismatch to the sender.
A valid local result establishes local existence only; it does not establish publication on GitHub.

## Verifying a published commit

For a published commit, current PR head, or merge claim, run `python3 "$GHFLOW_CLI" verify-commit SHA --repo OWNER/NAME` from the target project directory.
Add the facts that you expect: `--subject` with the first line of the commit message, `--on BRANCH` for the branch that should contain it, and `--pr-head PR_URL` when it should be the PR's current head.
Use the full SHA that the tool reports.

Exit status 0 means the commit exists and each expectation holds. Exit status 3 means an expectation is false. Exit status 1 means GitHub did not find the commit, which can mean it is not pushed. Do not pass on an identifier that failed. Read the branch again or return the mismatch to the agent that reported it.

An invalid primary commit response also exits 1. An invalid expectation response leaves that expectation `null` with an error. It exits 2 unless another expectation is false, which retains exit status 3. If GitHub provides no commit author or author date, `author_date` is `null` without an error, as the [GitHub REST response schema](https://github.com/github/rest-api-description/blob/main/descriptions/api.github.com/api.github.com.json) permits.
