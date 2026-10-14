# Review

These rules apply to every skill that requests, performs, waits for, or relies on a code review.

## Review sources

For an agent pull request, the primary review source is **independent local review**, done with [review-changes](../tasks/review-changes.md) in a fresh context.

The user may request **Copilot** review manually, in the GitHub web interface or with `gh pr edit PR_URL --add-reviewer "@copilot"`. Copilot is not the default for agent pull requests. Its underlying model is unknown unless something identifies it.

**Human review** comes from the user or another person.

By default, the local review must use a different model from the implementer. Apply an existing [user-approved exception](#user-approved-exceptions) before selecting a reviewer. Record each model identity from runtime or dispatch metadata. Do not infer it from an agent's name, writing style, or claims. A different agent name, a fresh context, or a changed reasoning setting does not make a different model.

When the user requested Copilot and it is unavailable, a different-model local review is the review source. Do not return that choice to the user. If a model identity is unknown or a different model is unavailable, report that and return the review choice to the parent. A same-model second opinion can still help. Label it as same-model, and leave the different-model requirement unmet. A user-approved alternative stays explicit in later handoffs.

No review source guarantees correct findings. Review does not replace tests or human judgment.

## User-approved exceptions

The user may approve another review method or waive the different-model review requirement. Record the user's instruction, its scope, and the review that remains required or optional. Scope can identify a project, task, agent application, or model setup. For example, approval for one local-model setup does not apply to an unrelated cloud-model workflow.

Apply an exception only within its approved scope. Carry it through implementation, reviewer selection, submission, and follow-up without asking for the same approval again. Before checking reviewer availability or arranging a fallback, check the existing exception. If its scope does not cover the task, apply the default requirement or return the specific unresolved choice to the parent.

Limited memory, cost, unavailable models, or dispatch limits can justify proposing an exception; they do not grant one. Do not silently replace different-model review with same-model review or self-review. If the user waived different-model review and made a same-model second opinion optional, do not make that second opinion a new gate.

Report an approved waiver as waived, not completed or silently unmet. For an alternative review, report the method, actual model evidence, covered commit, and findings. Keep self-review and same-model review labeled accurately. An exception does not waive tests, CI, unresolved findings, repository protections, or separate merge authorization. Apply a stricter review condition for a particular delivery unless the user's exception explicitly covers it.

## Prepare required review

First apply any [user-approved exception](#user-approved-exceptions) to establish what review this delivery requires. Establish an available path for that review before substantial implementation depends on it. Inspect current tool, session, or dispatch metadata for available dispatch, usable model selection, and recorded implementer and reviewer model identities. `facts` reports the detected runtime, its configured models, and per-agent model overrides under `runtime`; use it instead of reading the runtime's configuration files. Unless the approved exception permits otherwise, make sure that the selected reviewer model differs from the implementer model. Use that evidence, not assumptions about runtime names or model availability.

For an explicit same-model request, preserve the requested review method and fresh review context. Select the same model configuration for both workers when the dispatch controls permit it. Record the selected configuration separately from actual runtime identity. A shared agent type or configuration default alone does not establish that both workers ran the same model. When the exception waives model difference, preparation needs only an available dispatch path: do not read runtime or agent configuration to predict which model a worker will run. Ask each worker in its handoff for the model ID its own runtime states to it, and record that as a self-reported identity. Treat dispatch metadata as confirmation only when you can read it yourself; some runtimes store it where the coordinator cannot see it. Never record a configured or default model as a worker's identity, because a session flag can override every configuration file. The exception waives model difference, not accurate evidence reporting.

If dispatch, model selection, or model identity evidence is missing, report the precise unmet requirement and the next action to the parent. Under an approved waiver of model difference, missing identity evidence is a reporting limit, not an unmet requirement: dispatch, and carry the limit into the review report. Continue useful preparation that does not depend on it. Do not substitute self-review or a same-model review for the required independent different-model review. Preserve an explicit user-approved exception and its scope in the handoff.

Preparation establishes the available path and model evidence; it does not require executing the review before implementation. At review dispatch, record the actual selection and returned model evidence, including any remaining identity limit. If an established path later hits a capacity limit, preserve the work and model evidence and let the parent dispatch the reviewer under [Coordination](coordination.md#handoffs). This dispatch failure does not create a new review choice or require renewed approval.

Apply this preparation only when the selected flow requires independent review. A standalone implement-only operation, an ordinary draft, or a read-only task does not gain this requirement merely by using ghflow.

## Copilot request state

Request a Copilot review with `gh pr edit PR_URL --add-reviewer "@copilot"` only when the user asked for it. For an agent pull request, the default source is independent local review, not Copilot. Request a reviewer, not a coding-agent assignment or a comment that asks Copilot to change code.

Before you request, inspect current review requests, completed reviews, and review-request timeline events. Repository automation can request Copilot as soon as the PR opens. An empty requested-reviewer list does not prove that no request exists. If a request for the current head exists, keep its timestamp and do not request again.

Repository automation varies: a push may or may not trigger a new review. After a push, check for an automatic request first. Request a review only when the changes need one and no request exists.

Keep these states separate: requested, pending, completed, unavailable, and failed. A pending request or a temporary network error does not show that Copilot is unavailable. A request command can exit 0 without recording a request, for example when the PR author has no Copilot access. If GitHub records no request after you read it back, treat Copilot as unavailable.

A review is complete when the requested reviewer has submitted a review for the requested commit. Identify it by its author, commit, and submission time. It can have zero inline comments. CI completion, unrelated comments, and disappearance from the reviewer list do not show that Copilot finished.

## Affirmative review

**Affirmative review** is a favorable review that covers the changes being merged. It can come from a person, Copilot, or an independent local review.

A COMMENTED review qualifies when its text recommends approval or clearly reports a completed review with no findings. These do not qualify: silence, an empty comment list, a timeout, or the COMMENTED state alone. A review whose text asks for human review, such as Copilot's "Needs a closer look", does not qualify even with no findings. It returns the merge decision to the user. Another review source, including a different-model local review, does not answer that request. This workflow does not require the GitHub APPROVED state. Authors cannot approve their own PRs, and the agent often submits PRs as the user.

A favorable review does not by itself authorize merge. [merge-pr](../tasks/merge-pr.md) states when it counts.

If a review covers an earlier commit, assess what changed since then and state the coverage limit. Do not describe it as a review of the current head.

## Human feedback

A human COMMENTED review that requests changes is actionable, including a review from the PR author. The review state does not decide whether a finding needs a response. A comment that requests no change does not need a code edit.

Do not resolve a disputed discussion to make a PR look ready. Return disputes and human objections to the parent or user.
