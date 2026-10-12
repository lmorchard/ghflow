# Trial records

This index lists skill trials on real issues and public synthetic projects. Each entry states what the trial exercised and its evidence limits. Earlier delivery trials use [decafclaw](https://github.com/lmorchard/decafclaw).

## Record a trial

Add an entry with these facts:

- The date, subject issues, and PRs.
- The skills used and the commit of this repository that supplied them.
- The requested endpoint and what the trial exercised.
- Evidence limits, such as checks that nobody performed.
- Skill changes that the trial caused, with their commits.

Keep the entry short. Put long agent output in a dated folder only when later review needs it.

Entries before 2026-10-02 did not record the skill commit. For those entries, the commit is inferred from history: it is the commit before the one that recorded the trial, unless the entry says otherwise. Skills changed substantially in commit `489efbd`, so results from earlier commits do not transfer directly to later skill text.

## 2026-09-30: issue 843 definition, filing, and decomposition

The [issue 843 folder](2026-09-30-issue-843) contains agent output from these trials:

- [Issue definition trial results](2026-09-30-issue-843/review.md) for define-issue in a fresh agent context. Skills: `70cff5c`, which added the skill and recorded the trial together.
- [Filing the reviewed issue](2026-09-30-issue-843/filing.md), which created issue 861. No filing skill existed yet. The file-issue skill was written from this trial in `03d08f1`.
- [Proposed reconsideration](2026-09-30-issue-843/reconsider-proposal.md) for reconsider-issue. Skills: `831b1a2` (inferred).
- [Read-only decomposition](2026-09-30-issue-843/decomposition.md) for decompose-parent-issue, then named decompose-issue. Skills: `3460f88` (inferred).
- [Sticky lookup draft](2026-09-30-issue-843/sticky-lookup-draft.md) and [listing child draft](2026-09-30-issue-843/listing-child-draft.md) for reviewed child definitions.

## 2026-10-01: implementation and express delivery

The issue 863 trial completed implementation, submission, Copilot follow-up, and a separately authorized merge. It did not use the coordinator or local review. Skills: `31b5224` (inferred).

The issue 865 trial then exercised express-issue through review follow-up, including different-model local review, a Copilot finding, correction, and current-head review and CI. Skills: `01ecfc3` (inferred).

The issue 867 trial exercised the express merge endpoint through PR #868. The user required both affirmative review and green CI. The coordinator waited for the final hosted check, then merged the exact reviewed commit with a matching-head condition. This successful case does not establish every rejection or recovery path. Live post-merge application checks remained unperformed. Skills: `736c90d` (inferred).

The folder-management trial continued from definition and filing (#869) through implementation, independent review, PR #870, and merge. No product question or repeated authorization was needed. Favorable local and Copilot reviews and green hosted CI covered the exact merged head. The coordinator hit an agent-capacity limit, so the parent continued phase dispatch after its handoff. This tested continuity across skills, not a new automatic backlog selector. Live post-merge checks remained unperformed. Skills: `176f22c` (inferred).

After the issue 871 / PR #872 merge, Les reported that the manual smoke test seemed fine. This is user-reported evidence. The conversation does not specify which surfaces or scenarios were tested, so it does not establish completion of every project-required live check. Skills: `1e4b5a0` (inferred).

## 2026-10-01 to 2026-10-02: parent delivery of issue 843

deliver-parent-issue delivered children #875 through #884 of [issue 843](https://github.com/lmorchard/decafclaw/issues/843), then closed the parent after a fresh coverage audit. Skills: `3e753f0`. Issue 843 has 17 children in total. Seven children, #861 through #873, preceded this run.

Final checks passed on merged main: 4,237 Python tests with two skips, and 395 JavaScript tests. No deployment or final manual smoke test occurred. The ten children took about 11 hours, and later Python CI jobs took about 20 minutes each.

The [delivery retrospective](2026-10-02-parent-843-delivery.md) records the lessons, completion evidence, scope decisions, and recovery facts. Its scenario checks and the resulting skill changes are in [Retrospective scenarios](../../../evals/results/2026-10-02-retro.md).

## 2026-10-02: express delivery of issue 894

The parent coordinated express-issue for [issue 894](https://github.com/lmorchard/decafclaw/issues/894) through review follow-up, without merge, from a local decafclaw clone. Each phase ran in its own subagent. Implementation used Claude Opus and both local reviews used Claude Sonnet, selected by the dispatch. [PR #898](https://github.com/lmorchard/decafclaw/pull/898) ended at head `783ea99` with green hosted CI, no human comments, and #894 In review. Skills: implementation at `8f4c693`; first review and submission at `9b2b56c`; rework at `9b2b56c`; second review and follow-up at `4d70860`.

The first commit split one long browser test into 21 isolated scenarios. It also exposed two failures that the old test had hidden: invalid canvas test data, and an intended 404 after a folder is pruned. The first local review found the coverage preserved but measured a large slowdown on two cores. Les then replaced the wall-clock success condition with a structural one: one client build per run, one Chromium launch per worker, and one context and at most one server per scenario, enforced by the tests. A second commit met it, and a second local review found no defects.

Copilot reviewed both heads with no findings. Its headline changed from "Approval recommended" at `142af1b` to "Needs a closer look" at `783ea99`, which asks for human review. Les later decided that this headline is not affirmative review. The current skill text already produced that decision in scenario runs ([results](../../../evals/results/2026-10-02-copilot-headline.md)).

Hosted `lint-and-test` took 1106 s at the base, 948 s at `142af1b`, and 1151 s at `783ea99`, one run each. PR #896 took 1161 s with a similar test count. Run-to-run variance appears as large as any effect, so these numbers do not establish a change. Local pinned runs showed the rework faster at every worker count.

The same session filed [issue 897](https://github.com/lmorchard/decafclaw/issues/897) for the schedule race that #894 excluded. The board's auto-add workflow put it on board 6 without a request. Les then chose decafclaw's documented convention: new issues, triage items included, go on board 6 with priority and size. #894, #895, and #897 were then in Backlog at P2. Les later set #894 to P1.

Lessons and resulting changes:

- file-issue now reads back project membership even without a project request, because auto-add workflows can add it (`9b2b56c`).
- The submission subagent found #894 In progress, not Backlog as the handoff said, and acted on the live state. The board-status rule held.
- The first live use of `pr-state` found required checks in rulesets and matched the Copilot request to its bot review. Its two request fields confused a reader; evidence.md now explains them (`4d70860`).
- The implementer ran a `sudo apt` install through `playwright install --with-deps` without explicit authorization. implement-issue now requires authorization for system-level installs.
- The parent first compared hosted CI with older `main` runs that had about 600 fewer tests, and reported a false slowdown. Compare with the PR's base commit.
- The machine was shared with an unrelated heavy job, with load averages of 12 to 23. Local timings are noisy for that reason.

Les reviewed and merged PR #898 himself on 2026-10-03 (merge commit `4165293`, from head `783ea99`). `Closes #894` closed the issue one second later, and board automation set Done. A merge-pr subagent then ran the already-merged path at `6087b45`. `ghflow board set-status --status Done` exited 0 with action `unchanged` and `readback_matches` true, so the planned first real board write did not occur. A cleanup subagent removed the worktree and the local branch after it confirmed that the branch tip equaled the merged head and the worktree was clean.

- decafclaw's AGENTS.md provides `make prune-worktrees` for landed worktrees. The cleanup used git commands instead. The #895 cleanup later found that the target removes worktrees with `--force` and does not delete remote branches, so the explicit commands were the safer choice.
- The merge-pr agent asked whether the already-merged path expects `pr-state` or `verify-commit`. The skill does not say.

## 2026-10-03: express delivery of issue 895 through merge

The parent coordinated express-issue for [issue 895](https://github.com/lmorchard/decafclaw/issues/895) through merge, which Les authorized. Each phase ran in its own subagent. Implementation and review follow-up used Claude Opus 5.5; local review, submission, and merge used Claude Sonnet 5.5, selected by the dispatch. Skills at `2603989`. [PR #900](https://github.com/lmorchard/decafclaw/pull/900) merged as `6604c0b` from head `ff360b1`, with green hosted CI and Copilot "🟢 Approval recommended" with no findings for that head. This was the first full delivery that used all three CLI operations.

The fix let Starlette's `FileResponse` build the attachment header. Both new regressions failed on the base `4165293` with the reported `UnicodeEncodeError` and passed with the fix. The full suite went from 4257 to 4260 passed. No system install was needed, although Les had authorized Playwright dependencies.

The implementer reported, and the independent local review found without a prompt, one difference from the issue text. ASCII names that need URL quoting, such as `my report.txt`, now get only `filename*=utf-8''my%20report.txt`. Les accepted that form. The implementer pinned it with a test in a second commit, and the reviewer assessed only that change.

Lessons:

- `board set-status` made its first real writes: Backlog to In progress, and In progress to In review, each with a matching readback. Board automation set Done at both merges before the agent ran, so the Done step reported `unchanged`.
- `verify-commit` reads only published commits. The implementer-to-reviewer handoff happens before a push, so the parent verified those identifiers with git. After the push, submission, follow-up, and merge used the tool. Watch whether this gap causes an error before adding a local mode.
- Leaving the implementer's risk note out of the reviewer's handoff let the review confirm it independently.
- The submission agent stated that the automatic Copilot request "came from automation" because its actor was `lmorchard`. That actor does not show the cause; see [issue 1](https://github.com/lmorchard/gh-project-workflow/issues/1).
- decafclaw's AGENTS.md asks for a live test in Mattermost and the web UI after merge. That remains for Les.

## 2026-10-03: express delivery of issue 897 under MokaGnome

The parent coordinated express-issue for [issue 897](https://github.com/lmorchard/decafclaw/issues/897) through review follow-up, without merge, using the machine account `MokaGnome`. Subagents performed all subject-repository writes using the classic token at `~/.config/ghflow/mokagnome.token`. Skills commit was `7c59ab7`.

The task guarded four asynchronous functions in `schedule-page.js` against stale responses when a user selects another schedule. The first commit `8fa6b3f` added guards and eight component tests. An independent local review by Claude Sonnet found that `#onWikiSaved` did not guard against an A to B to A selection sequence. The implementer fixed the defect in commit `542db3d`, and a second local review confirmed the fix.

The reviewer also noted an in-flight status race in `#runNow`. A subagent verified the race and filed follow-up [issue 904](https://github.com/lmorchard/decafclaw/issues/904) as `MokaGnome`.

Subagents pushed the branch, submitted [PR #907](https://github.com/lmorchard/decafclaw/pull/907), moved issue 897 to In review on board 6, and verified green hosted CI. The subagent requested Copilot review. GitHub recorded no request because `MokaGnome` has no Copilot seat. Affirmative local review covered the published head commit `542db3d`.

Les explicitly authorized the merge. A subagent merged PR #907 as `MokaGnome` with merge commit `6b66ce0`. The merge closed issue 897, and board automation set Done. Local worktrees and branches were preserved.

## 2026-10-05: ready-queue burndown on board 6

The [burndown retrospective](2026-10-05-ready-queue-burndown.md) records delivery from board 6 through review follow-up at initial skill revision `d932930`.
Les merged the seven resulting PRs. Subagents performed subject-repository writes as `MokaGnome`.
The record preserves resulting skill changes, CI and ownership failures, and unrecorded manual checks.

## 2026-10-09: issue #28 submission and sandboxed GitHub access

The parent submitted [PR #53](https://github.com/lmorchard/gh-project-workflow/pull/53) for issue #28 through review follow-up. The submission subagent used ghflow revision `6e932ecd60751be8346ebe5e806515cd4c77fef1`.
Inside the sandbox, `ghflow exec -- gh auth status` reported that the `GH_TOKEN` token was invalid. Les's terminal showed `MokaGnome` active with `repo`, `project`, and `read:org` scopes. An approved read-only check outside the sandbox confirmed the same host login.
The subagent submitted PR #53 as `MokaGnome`. Hosted CI passed, and follow-up found no reviews or comments. No board transition was possible because issue #28 had no project membership.
Copying the CLI token into the configured token file did not make the sandbox check pass. This task did not establish whether the configured token file works outside the sandbox. The identity reference now distinguishes sandbox failures from invalid credentials.
The [decision scenario results](../../../evals/results/2026-10-09-sandbox-auth-context.md) assess the revised rule separately from the live submission.

## ghflow installation

[Routine-resolution comparison, 2026-10-07](2026-10-07-resolution.md) supplies the agreed first increment of issue #2.
Three fresh native sessions used public skills at `b47c9d5` and isolated task-list fixtures.
Observed commands and artifacts established factual resolution, a routine patch, and a returned consequential decision.
Existing guidance remained unchanged. Later experiments and the umbrella issue remain open.

[Setup trial, 2026-10-07](2026-10-07-ghflow-setup.md) assesses one registered skill, symbolic-link discovery, routing, and dependency access in Claude Code, Codex, and OpenCode.

[Root-package setup trial, 2026-10-07](2026-10-07-ghflow-root-setup.md) repeats discovery and routing after the repository-root layout change.
It records the subject-resolution correction and the unresolved OpenCode discovery of ignored nested worktrees.

[Issue #32 unpublished handoff trial, 2026-10-08](2026-10-08-issue-32-unpublished-handoff.md) records an implementation commit passed to a fresh, different-model local reviewer without publication.

[Issue #32 conflicting identity trial, 2026-10-09](2026-10-09-issue-32-conflicting-identity.md) records a real local commit and a simulated board write with conflicting inherited identity values.
The configured identity reached both write boundaries. Live GitHub authentication remains unconfirmed.
Later local session metadata identified the actor as `gpt-6.1-sol`; provider runtime attestation remains unavailable.
The Ready-page and interrupted-publication cases remain pending.

## 2026-10-07: issue 8 reviewer preparation

The [reviewer preparation record](2026-10-07-issue-8-reviewer-capability.md) summarizes three historical paired trials and preserves pinned sources.
The shared instruction now establishes the required review path before substantial dependent implementation.
Four reusable [decision scenarios and results](../../../evals/results/2026-10-07-reviewer-preparation.md) assess the revised instruction.
All five recorded sessions pass after the accepted unknown-author criteria refinement. Evaluated instructions and raw prompts remain unchanged.
The broader identity and access scope remains open.

## 2026-10-08: decafclaw triage, interview, and definition sweeps

The parent ran triage-issues, interview-issue, sweep-needs-input, and sweep-needs-definition on about 60 decafclaw issues at skills `9e64bd5`. Subagents performed subject-repository writes as `MokaGnome`.
The definition sweep left 15 issues on `triage:needs-definition` that could not be specified: 12 waited on open issues and 2 were a parking lot and a parent. Les's needs-attention board view could not tell them from actionable work.
This led to [Triage labels](../../../references/shared/triage-labels.md), `triage:blocked`, `triage:parked`, and [sweep-blocked](../../../references/tasks/sweep-blocked.md), with two new scenarios. Four fresh sessions passed them at `c96332a`, as the [results](../../../evals/results/2026-10-08-blocked-parked-labels.md) record.

## 2026-10-10: local-model notes and resumption

The [local resumption trial](2026-10-10-local-context-resume.md) used the already active Qwen3.8-27B Q4_K_M model through OpenCode.
A fresh actor read existing notes and reused the supplied worktree and branch.
It stopped at 300 seconds before edits, tests, or commits.
Source was hashed mutable working text. The trial establishes neither completed resumption nor improved efficiency.
[Decision samples](../../../evals/results/2026-10-11-local-context.md) record separate bounded checks.

## 2026-10-11: coordinator preparation for issue #997

The [transcript review](2026-10-11-coordinator-preparation.md) records repeated preparation before the first implementation dispatch.
It supplies the source for clearer dispatch ownership, preparation limits, handoffs, and same-model evidence rules.
The snapshot does not establish completed implementation, review, or delivery.

## 2026-10-11: issue #997 delivery on a local model

The [delivery record](2026-10-11-issue-997-delivery.md) covers the full run of the same session, with every agent on local `llama.cpp/llama` at skills `ddd342e`.
[PR #1060](https://github.com/lmorchard/decafclaw/pull/1060) ended ready at `c392966` with passed hosted checks and no merge. The reviewer found a shipped defect that the implementation's tests had missed.
Seven dispatches and about 3 hours 50 minutes for a 60-line change supplied the source for one implementation worker across operations, no coordinator diff assessment, and a conditional follow-up dispatch. Three new scenarios and four updated scenarios cover those decisions.

## 2026-10-12: issue #1012 delivery on the local model with the merged text

The [delivery record](2026-10-12-issue-1012-qwen-delivery.md) covers a detached `opencode run` on the same Qwen model at skills `62972b3`, after PRs #63 through #71 merged.
[PR #1062](https://github.com/lmorchard/decafclaw/pull/1062) ended ready at `eca206b` with CI green, a clean fresh-session review, and no merge. Three working dispatches against seven, no coordinator diff review, the reviewer ran the new tests against the base, and the conditional follow-up stopped the flow without a dispatch.
Wall clock was 7 hours 7 minutes with the model shared by a second workload, so the time is not comparable to #997; the run was dominated by the worker's investigation of suite deaths it caused by running several full suites concurrently, and by five notes-only commits that each restarted CI. Five candidate changes are listed in the record. Every changed-text and regression sample passed on Sonnet, and four of five baselines failed on the reversed decision, as the [results](../../../evals/results/2026-10-11-ceremony-reduction.md) record.

## 2026-10-12: issue #1054 delivery on the local model, concurrent with #1012

The [delivery record](2026-10-12-issue-1054-qwen-delivery.md) covers an interactive OpenCode session on the same Qwen model at skills `62972b3`, selected as the first measurement for the overnight burndown plan. It ran at the same time as the #1012 delivery on the same llama server.
[PR #1061](https://github.com/lmorchard/decafclaw/pull/1061) ended ready at `42e9a74` with CI green, a clean fresh-session review, one code commit, and no merge. Four task calls, of which three did work; the placeholder dispatch at the ready step recurred, this time into the correct session.
Wall clock was 4 hours 39 minutes with the server shared. The coordinator spent 15 minutes reading references before the first dispatch and 21 minutes after the endpoint was established. The review took 88 minutes for a one-line change. Four candidate changes are listed in the record.

## 2026-10-12: issue #1053 delivery on the local model with pr ready and project facts

The [delivery record](2026-10-12-issue-1053-qwen-delivery.md) covers the first run at skills `678509e`, after `pr ready`, the project facts file, and the coordinator ceremony changes merged, and the first run on the merged text with a correction cycle.
[PR #1064](https://github.com/lmorchard/decafclaw/pull/1064) ended ready at `4e22f7e` with CI green, an approving fresh-session review and re-review, and no merge. The early draft checkpoint and the one-call ready submission worked. The placeholder dispatch recurred for the third time and was recovered as the new rule says. A notes-only commit after ready moved the head and forced a follow-up dispatch, and three reviewer notes became user decisions.
Wall clock was 4 hours 22 minutes on an unshared server for a change three to four times the size of #1054; the coordinator read five references before the first dispatch, pointed its handoff at the facts file, and reported in three minutes from the read-back. Four candidate changes are listed in the record.
