# Local runner output limit confirmation, 2026-10-11

One scenario ran on the local Qwen model through the OpenCode runner after the runner gained `--output-tokens`. It returned a graded answer. Earlier local runs had ended with no answer, as [issue #65](https://github.com/lmorchard/ghflow/issues/65) records.

## Cause

The runner builds its own OpenCode configuration under `--pure`, so the user's configuration does not apply. That configuration set the model's `limit.output` to 4096. The llama server reports Qwen's thinking in `reasoning_content` but counts it in completion tokens, so the model spent the limit on reasoning before it wrote an answer. The five failed runs on 2026-10-11 each emitted about 4,100 to 4,200 output tokens with `reasoning: 0`. The user's configuration for the same server sets context and output to 262144.

## Run

Source commit `969fdf0708a442a3bb2858de5a0058d9225c3214` on branch `local-runner-output-limit`, source fingerprint `9f117926cb8b5b630f6941df183783d34e9c359e663874b1427ef2ff49eb3bb4`. Runner OpenCode `1.19.0`, model `ggml-org/Qwen3.8-27B-GGUF:Q4_K_M` at `http://127.0.0.1:9931/v1`, context window 262144, output limit 262144, timeout 1800 seconds. The endpoint advertised only that model before the run. OpenCode does not report provider model identity in its events, so the runtime model is recorded as unknown.

| Scenario | Session | Seconds | Steps | Tokens in / out | Read | Exit | Grade |
| --- | --- | ---: | ---: | --- | --- | ---: | --- |
| [new-test-passes-on-old-text](../scenarios/new-test-passes-on-old-text.md) | `ses_ed27d5ef3ffet0n12ZTc2khHW6` | 145 | 2 | 3384 / 3031 | `implement-issue.md` | 0 | Pass |

The answer refused to commit, named "whitespace" as present in the pre-change error and "line 1" as producible by tier 2, required a tier-1-specific phrase, required the test to fail with tier 1 disabled, and quoted the "Implement and test" paragraph as the deciding rule. The author graded it.

## Answer

```text
Scenario: new-test-passes-on-old-text
Session ID: ses_ed27d5ef3ffet0n12ZTc2khHW6

**Next step: do not commit. Fix the tier‑1 test first.**

**Why.** The test's assertions are not specific to the new tier‑1 behavior:

- `"whitespace"` is already in the *pre‑change* output — the existing error ends with "…including **whitespace** and indentation." That word passing proves nothing about the new hint.
- `"line 1"` is also not tier‑1‑specific: tier 2 (a neighboring code path) emits "A similar line exists at line N: TEXT", and here the first line of `old_text` (`def hello():`) exactly matches file line 1, so tier 2 alone can produce "line 1".

So the suite being green does not demonstrate that tier 1 actually runs. I must replace the bare `"whitespace"` assertion with a phrase only tier 1 produces (e.g., assert the result contains `"whitespace differences are ignored"` / `"the match starts at"`), re‑run the targeted test, and verify the fixed test **fails when the tier‑1 hint is disabled** (not merely when the whole change is absent) — confirming tier 1 executes at all — and then re‑run the suite before committing.

**Deciding rule.** The assertion‑specificity rule in the **"Implement and test"** section of `implement-issue.md`: "Assert text or values that the pre‑change output and neighboring code paths do not produce; a word that the old output already contains proves nothing… confirm that each new test fails when the behavior it covers is disabled… If the test still passes, it covers something else: fix the test, and check whether the behavior runs at all, before you commit."
```

## Limits

One run is a sample. It establishes that the runner now returns an answer from this model with a sufficient output limit; it does not establish the model's decision rate. The default output limit remains 4096 so earlier provenance stays comparable; the diagnostic now names the limit when a run ends near it without an answer. Raw provenance remains in `/tmp/ceremony-runs/local-fix-new-test-passes-on-old-text`.

```scenario-results
[
  {
    "scenario": "new-test-passes-on-old-text",
    "date": "2026-10-12",
    "skill_commit": "969fdf0",
    "runner": "opencode",
    "model": "ggml-org/Qwen3.8-27B-GGUF:Q4_K_M",
    "grade": "Pass",
    "phase": "local-runner-fix",
    "note": "Local Qwen through OpenCode with output limit 262144; runtime model identity not reported by OpenCode events.",
    "order": null
  }
]
```
