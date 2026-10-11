# Issue #997 delivery on a local model, 2026-10-11

This record covers the full delivery run that followed the [coordinator preparation review](2026-10-11-coordinator-preparation.md). That review used an early snapshot of the same session. This record supplies the source for the ceremony reduction in express-issue and coordination, and for the scenarios that cite it.

## Source and setup

Sources: local decafclaw transcripts `session-ses_ed3e.md` (parent, session `ses_ed3ed5843ffeFInXeXPKb3t28W`), `session-ses_ed3d-1.md` (implementation worker), `session-ses_ed3a-2.md` (submission worker), `session-ses_ed39-3.md` (reviewer), and `session-ses_ed31-4.md` (follow-up worker, truncated at its first turn). The transcripts are not copied into this repository.

Every agent ran in OpenCode on the local model `llama.cpp/llama`. The user requested delivery of [issue #997](https://github.com/lmorchard/decafclaw/issues/997) with the same model for implementation and review. The installed skill was at `ddd342e`, before PR #62 merged.

## Result

[PR #1060](https://github.com/lmorchard/decafclaw/pull/1060) ended ready for review at head `c392966`, with three hosted checks passed and the issue In review. Nobody merged it. The reviewer found a real defect that the implementation had shipped as passing: the whitespace-insensitive hint pattern never matched, and its two tests passed on text from the old error. A second commit fixed it and a delta re-review found no new defects.

The run took about 3 hours 50 minutes of wall clock for a change of about 60 lines. The coordinator made seven dispatches: implementation, draft publication, review, correction, re-review, ready submission, and follow-up.

## Observed behavior

- The coordinator read every reference, including the task references of operations it would dispatch, before the first dispatch. It then read the full diff and assessed it itself before publishing the draft. It verified one reviewer claim empirically before dispatching the correction. That verification settled the next dispatch; the earlier diff assessment did not.
- Each worker opened its task reference once and read no shared reference. The workers followed the coordinator's handoff text, which restated the procedure, commands, and return list.
- The draft publication, ready submission, and final follow-up ran as separate dispatches. The implementation was complete when it first returned. The final follow-up started after the submission worker had already read back passed checks for the current head and no review requests.
- The correction handoff told the implementation worker to push. The worker committed, pushed, and verified the published head itself.
- The coordinator resumed the same worker sessions for the correction, the re-review, and the ready submission.
- The implementation worker and the reviewer each reasoned about `re.escape` from memory before testing it. The implementation self-review stated that the pattern was verified in tests. No command had verified it.
- The implementation worker wrote the result of gates and a push into its notes before running them. The results later matched.
- The submission worker spent four turns writing GraphQL queries to read the board status before `board set-status`, which returns the earlier status itself.
- The reviewer reported no PR comments without reading them. `pr-state` does not return top-level comments.

## Changes from this record

express-issue now has one implementation worker carry implementation, draft publication, corrections, and ready submission through their task references, and a separate fresh reviewer. The coordinator reads reports and does not assess the diff itself. A ready submission report with passed current-head checks, no requested or pending review, and no unresolved findings completes the follow-up endpoint without a follow-up dispatch. Coordination states the same worker reuse and the handoff requirement to supply finding text. implement-issue and submit-pr carry the matching sentences.

This reverses the operation-scope decision in the preparation review, which kept publication out of the implementation handoff. The scenario `implementation-handoff-operation-scope` now expects both operations named for the same worker, each with its own scope.

Scenarios added: `express-complete-return`, `corrections-same-worker`, and `followup-already-green`. Scenarios updated: `delivery-early-draft`, `draft-pr-ready-transition`, `express-default-endpoint`, and `implementation-handoff-operation-scope`.

The remaining observations are not yet changes. They concern test assertions that must be unique to the new behavior, empirical checks of library behavior, notes written before results exist, the board status read, submission command details, and reviewer access to PR comments.

## Evidence limits

The analysis of the worker transcripts came from three subagents; the author read the parent transcript directly and verified the quoted skill text, CLI commands, and subject repository rules. Wall-clock figures come from the turn durations in the transcripts. The run used one model on one issue, so it does not measure the effect of the changes. No scenario run has assessed the revised text yet.
