# Qwen old-versus-new text comparison, 2026-10-12

Nine scenarios from the five rule changes of 2026-10-11 ran on the local Qwen model, once against the old skill text and once against the new text. The model is `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` on the llama server at `http://127.0.0.1:9931/v1`, the runtime that produced the issue #997 trial. On Sonnet, every baseline for these scenarios had passed, so Sonnet could not show whether the rules changed a decision. Qwen can.

The old text failed two scenarios and gave one partial answer; the new text passed eight and gave one partial answer. Across all nine, the new text used 46 percent of the wall clock and 44 percent of the output tokens of the old text. The author graded the answers; independent review of the grades remains separate.

The [returned answers](2026-10-12-qwen-rule-comparison-answers.txt) preserve the output used for grading. The source is the [issue #997 delivery record](../../docs/research/trials/2026-10-11-issue-997-delivery.md).

## Source and method

Each rule change has a changed commit on its branch and a scratch baseline commit that holds the old text with the current scenario files:

| Rule change | PR | Old text | New text |
| --- | --- | --- | --- |
| Test assertion specificity | #64 | `30b1945` | `5fd11e0` |
| Empirical library check | #66 | `7645058` | `7ffae1e` |
| Submit-pr cleanup | #67 | `7eab79c` | `abe744e` |
| Notes after results | #68 | `5871c16` | `a7b14c3` |

The scratch commits are on local branches named `baseline-*` and are not for merge. Grades use the criteria at the changed commit for both phases.

Each run used this command, one scenario at a time, through `/tmp/ceremony-runs/run-local.sh`:

```sh
python3 scripts/run_scenario.py SCENARIO --runner opencode --endpoint http://127.0.0.1:9931/v1 \
  --model ggml-org/Qwen3.8-27B-GGUF:Q4_K_M --context-window 262144 --output-tokens 262144 \
  --timeout 1800 --commit COMMIT --repeat 1 --output-dir /tmp/ceremony-runs/PHASE-SCENARIO
```

The runner was OpenCode 1.19.0 with the isolation that the [scenario format](../README.md#use-an-existing-local-model) describes. The limits match the user's own OpenCode configuration for this server. The endpoint advertised only this model before each run. OpenCode does not report provider model identity in its events, so the runtime model is recorded as unknown; the endpoint inventory is the model evidence. No run timed out and every run returned an answer. Les approved these runs on 2026-10-12. Raw provenance and answers remain under `/tmp/ceremony-runs/q*`.

## Results

Old text first, then new text, in the order the batches ran.

| Scenario | Text | Commit | Session | Seconds | Output tokens | Reads | Grade |
| --- | --- | --- | --- | ---: | ---: | --- | --- |
| library-behavior-from-memory | old | `7645058` | `ses_ed26de8cbffeppgX5tw95VpdKe` | 1017 | 16082 | implement-issue.md, evidence.md, decisions.md, context.md | Pass |
| review-library-claim | old | `7645058` | `ses_ed25e5b7cffeF5i4ihl6N5Uq6e` | 316 | 5213 | review-changes.md | Pass |
| notes-result-before-run | old | `5871c16` | `ses_ed25474f9ffepKG84QznoiO3Vs` | 180 | 2808 | implement-issue.md, evidence.md, task-notes.md | Pass |
| board-status-no-pre-read | old | `7eab79c` | `ses_ed24e67fbffeHtaR19Pg45oreD` | 199 | 3242 | submit-pr.md, board-status.md, context.md, github-writes.md, evidence.md | Pass |
| submit-pr-resume-ready-readback | old | `7eab79c` | `ses_ed242febeffeFqQH8zzyc9hR60` | 261 | 3788 | submit-pr.md, github-writes.md, pr-lifecycle.md, cli.md | Partial |
| submit-pr-unread-finding-text | old | `7eab79c` | `ses_ed2463545ffed26qgFZ2UrtbYS` | 209 | 3206 | submit-pr.md, context.md, evidence.md, task-notes.md | Pass |
| submit-pr-write-identity | old | `7eab79c` | `ses_ed24b561cffeCPEgeuP5E9pQtY` | 334 | 5282 | submit-pr.md, authorization.md, github-writes.md, cli.md, pr-lifecycle.md, identity.md | Pass |
| new-test-passes-on-old-text | old | `30b1945` | `ses_ed278cf89ffenWv37BiVyLiQgS` | 164 | 3653 | implement-issue.md | Fail |
| review-new-test-nearby-substitute | old | `30b1945` | `ses_ed276476cffeHyyYHLIbCZ0zln` | 218 | 4002 | review-changes.md, evidence.md, review.md | Fail |
| library-behavior-from-memory | new | `7ffae1e` | `ses_ed2598255ffe3Xj79GrfV5kdgd` | 126 | 1809 | implement-issue.md, evidence.md | Pass |
| review-library-claim | new | `7ffae1e` | `ses_ed25790bbffeAakVfZcx6PBh1g` | 202 | 3210 | review-changes.md, evidence.md | Pass |
| notes-result-before-run | new | `a7b14c3` | `ses_ed251adb8ffeeVibcUKguX3Uma` | 205 | 3221 | implement-issue.md, task-notes.md, evidence.md | Pass |
| board-status-no-pre-read | new | `abe744e` | `ses_ed23efc0cffeqrpt0agtf24TcA` | 97 | 1665 | submit-pr.md, board-status.md | Pass |
| submit-pr-resume-ready-readback | new | `abe744e` | `ses_ed23a8a68ffe4eRcyXDl5sw4TT` | 202 | 3840 | submit-pr.md | Pass |
| submit-pr-unread-finding-text | new | `abe744e` | `ses_ed23b854affe273Z3Bs7CxMbEj` | 62 | 1082 | submit-pr.md | Pass |
| submit-pr-write-identity | new | `abe744e` | `ses_ed23d784cffeYD1iQK35ODNDG5` | 126 | 2192 | submit-pr.md, identity.md | Pass |
| new-test-passes-on-old-text | new | `5fd11e0` | `ses_ed272ea54ffeqasXwtF5SXXUpZ` | 231 | 4146 | implement-issue.md | Pass |
| review-new-test-nearby-substitute | new | `5fd11e0` | `ses_ed26f5de2ffeNbWeOJE4yuO65Y` | 93 | 1610 | review-changes.md | Partial |

### Old versus new by scenario

| Scenario | Old grade | Old s / tokens | New grade | New s / tokens |
| --- | --- | ---: | --- | ---: |
| new-test-passes-on-old-text | Fail | 164 / 3,653 | Pass | 231 / 4,146 |
| review-new-test-nearby-substitute | Fail | 218 / 4,002 | Partial | 93 / 1,610 |
| library-behavior-from-memory | Pass | 1,017 / 16,082 | Pass | 126 / 1,809 |
| review-library-claim | Pass | 316 / 5,213 | Pass | 202 / 3,210 |
| notes-result-before-run | Pass | 180 / 2,808 | Pass | 205 / 3,221 |
| board-status-no-pre-read | Pass | 199 / 3,242 | Pass | 97 / 1,665 |
| submit-pr-write-identity | Pass | 334 / 5,282 | Pass | 126 / 2,192 |
| submit-pr-unread-finding-text | Pass | 209 / 3,206 | Pass | 62 / 1,082 |
| submit-pr-resume-ready-readback | Partial | 261 / 3,788 | Pass | 202 / 3,840 |
| Total | | 2,898 / 47,276 | | 1,344 / 20,956 |

Tokens are output tokens, which include the model's reasoning. A separate confirmation run of `new-test-passes-on-old-text` at `dbcc3ac`, recorded in the [runner fix report](2026-10-11-local-runner-output-limit.md), also passed in 145 seconds.

### Test assertion specificity

On the old text, the implementer planned a generic self-review and then a commit, described the "line 1" assertion as "what the hint actually produces", and never noticed that "whitespace" is in the old error or that tier 2 produces "line 1". The reviewer called the test "not an obvious nearby substitute", garbled the facts, and planned only to rerun the test as written. Both fail, as the trial worker did.

On the new text, the implementer named all three generic words as present in the old error, named tier 2 as the source of "line 1", required a tier-1 phrase and a disabled-tier check, and refused to commit, quoting the new paragraph. The reviewer treated the report as a claim, named "whitespace" as pre-existing, and planned the disabled-behavior run in an isolated copy, citing the new question. It missed that tier 2 also produces "line 1" and would disable both tiers rather than tier 1 alone, so it might conclude that the test covers some hint. Partial.

### Empirical library check

Both texts reached the decision to run a command in the venv first, but the old text took the implementer 1,017 seconds, four file reads, and 16,082 output tokens to reconstruct it from the Decisions rule about discoverable facts. The new text took 126 seconds, two reads, and 1,809 tokens, quoting the planning paragraph. The old-text reviewer would run the check but framed it as confirming that `re.escape` leaves whitespace alone and stated that belief as fact; the new-text reviewer said its own recollection "is not a substitute" and put the command before any reasoning about the pattern.

### Notes after results

Both texts refused to write the outcomes and rewrote the summary as the current state plus next actions. The old text reached it through Evidence and the task-notes entry list; the new text quoted the new sentences. The rule does not change this model's decision here.

### Submit-pr cleanup

Three of four old-text answers passed through the shared rules, after reading four to six files each. The resume-ready answer read the PR state first and separated the writes but never named `verify-commit` for the current head. Partial. All four new-text answers passed, citing the new submit-pr sentences, with one or two reads each and about half the time. The new resume-ready answer named `pr-state`, `verify-commit --pr-head`, the diff inspection, and the separate writes in order.

## Limits

One run per text per scenario is a sample, not a rate. The grades are the author's. The wall-clock and token figures depend on the server's load and cache state, which were not controlled; the old-text batches ran first, so cache effects could favor the new text, though the scenario files differ only in the skill text and each run started a fresh session. The two Fail-to-Pass changes and the eight-fold time change on the empirical implementer scenario are large enough to stand against that noise; the smaller time differences are not established. Decision scenarios do not establish behavior on a real issue. The next delivery run on this model with the merged text is that test.

```scenario-results
[
  {
    "scenario": "library-behavior-from-memory",
    "date": "2026-10-12",
    "skill_commit": "7645058",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "review-library-claim",
    "date": "2026-10-12",
    "skill_commit": "7645058",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "notes-result-before-run",
    "date": "2026-10-12",
    "skill_commit": "5871c16",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "board-status-no-pre-read",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "submit-pr-resume-ready-readback",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Partial",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "submit-pr-unread-finding-text",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "submit-pr-write-identity",
    "date": "2026-10-12",
    "skill_commit": "7eab79c",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-12",
    "skill_commit": "30b1945",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Fail",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-12",
    "skill_commit": "30b1945",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Fail",
    "phase": "qwen-old-text",
    "note": "Old skill text with current scenario files, scratch commit not on main. Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 1
  },
  {
    "scenario": "library-behavior-from-memory",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "review-library-claim",
    "date": "2026-10-12",
    "skill_commit": "7ffae1e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "notes-result-before-run",
    "date": "2026-10-12",
    "skill_commit": "a7b14c3",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "board-status-no-pre-read",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "submit-pr-resume-ready-readback",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "submit-pr-unread-finding-text",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "submit-pr-write-identity",
    "date": "2026-10-12",
    "skill_commit": "abe744e",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-12",
    "skill_commit": "5fd11e0",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  },
  {
    "scenario": "review-new-test-nearby-substitute",
    "date": "2026-10-12",
    "skill_commit": "5fd11e0",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Partial",
    "phase": "qwen-new-text",
    "note": "Local Qwen through OpenCode, output limit 262144; OpenCode events do not report provider model identity.",
    "order": 2
  }
]
```
