# Coordinator preparation review, 2026-10-11

The issue #997 transcript shows repeated procedural decisions before the first implementation dispatch.
Les requested a review, then authorized the proposed skill changes and a pull request (PR).
A PR proposes changes for review.
This record supplies the source for the changes and their decision scenarios.

## Source and observed behavior

Source: local decafclaw transcript `session-ses_ed3e.md`, session `ses_ed3ed5843ffeFInXeXPKb3t28W`.
The reviewed snapshot reported creation at 10:46:22 and update at 11:05:38 on 2026-10-11.
It contained 2,266 lines and ended while the agent prepared an implementation handoff.
The SHA256 digest of this snapshot is `df193660bcd085b27310a0769c9657875ec9b2985437c95eae8f3ff458bc56a8`.
The exact skill source commit was not recorded in the transcript.
The workflow files that it read contain the relevant existing rules.

The user requested delivery of issue #997 and the same model for implementation and review.
At line 869, the agent loaded future task procedures before implementation dispatch.
At lines 1,486 and 1,883, it repeatedly reconsidered delegation without new evidence that changed the rule.
It also struggled with the distinction between parent ownership and worker execution of PR follow-up.
At line 2,118, it claimed that two `general` agents establish the same model.
The recorded configuration and session model names differed; neither established worker runtime identity.
At line 2,235, it prepared to omit the source revision, although an earlier directory listing showed `.git`.

## Changes and assessment

[Coordination](../../../references/shared/coordination.md) separates dispatch ownership from subject-repository execution and gives a compact implementation handoff example.
[Working context](../../../references/shared/context.md) states when preparation permits dispatch and when to read future task procedures.
[Review](../../../references/shared/review.md) separates selected model configuration from actual runtime identity for explicit same-model requests.
The exception preserves honest reporting of missing evidence.

Three new scenarios assess dispatch readiness, operation scope in handoffs, and missing same-model identity evidence.
The existing parent-follow-up scenario also rejects execution by the conversation parent.
The scenario runner built all three baseline prompts at commit `8c36c4467e1ea816f0f0f416ddb5ae73f2f9f3c1` in dry-run mode.
The prompts excluded Expected and Not acceptable criteria.
No model session or behavioral assessment occurred in those checks.

An independent built-in reviewer examined the full diff from `ddd342e` to the working text and found no actionable issues.
Dispatch selected `gpt-6-astra`; this records the selection, not provider runtime attestation.
The reviewer used a fresh context and did read-only source inspection.
The author used the Codex parent session; its exact runtime model identity was not exposed.
This content review does not establish a verified different-model comparison.

Automatic approval review rejected the proposed Claude Sonnet evaluations because they would send repository guidance and scenario prompts to an external provider.
The author requested specific user approval for that disclosure.
Behavioral scenario runs remain unperformed pending that approval.
Les later approved the runs. [Coordinator preparation](../../../evals/results/2026-10-11-coordinator-preparation.md), [regression](../../../evals/results/2026-10-11-coordinator-preparation-regression.md), and [round 2](../../../evals/results/2026-10-11-coordinator-preparation-round2.md) record the results.
Repository checks passed: 144 CLI tests, 51 script tests, Markdown links, scenario index, and whitespace checks.
The general skill validator lacked PyYAML; the repository checker separately examined the skill frontmatter.

## Evidence limits

This snapshot establishes preparation behavior, not completed delivery or failed implementation.
It shows no subagent call, code change, test result, PR, or completed review.
The transcript is a local source and can change as the session continues.
The quoted locations identify the reviewed portion; no full transcript is copied into this repository.
Decision scenarios cannot establish faster execution or reliable worker behavior on a real issue.
