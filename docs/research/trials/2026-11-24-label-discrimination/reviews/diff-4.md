### Blocking findings

None.

### Non-blocking findings

1. **`parse_env_labels` has no production caller.** It is added in the `scavenger.py` hunk near line 64, and only `test_scavenger_cli.py` calls it. Reaping still goes through lease container names, so containers that exist now are still reaped. But "readers accept both names" exists only as a helper. The diff changes one label site, the `env_create` run script. If `scavenger.py` or `tools.py` contains any other `decafclaw.env_id` or `decafclaw.expires_at` filter or read outside these hunks, it now misses new containers. Someone should grep for that before merge. The test `test_env_create_writes_scavenger_labels` checks only the create script.
2. **SKILL-cli.md contradicts `wake` and `env-destroy`.** The doc says "On failure, `--json` prints `{"error": ...}`". But `wake` (exit 1 with `{host, awake: false, message}`) and `env-destroy` (exit 1 with `{env_id, destroyed: false}`) print their normal payload on failure (`cmd_wake`, `cmd_env_destroy`). Either the doc or the code should change so scripts can rely on one shape.
3. **Timeouts and unexpected exceptions bypass the JSON and exit-code contract.**
   - `cmd_run` turns `subprocess.TimeoutExpired` into exit 124 only in `--json` mode. In text mode the exception escapes as a traceback, which contradicts the doc's "124 means a timeout".
   - `cmd_env_create` catches only `ValueError` and `RuntimeError`.
   - A malformed `fleet.json` raises `JSONDecodeError` inside `load_fleet_config` / `_require_fleet`, which is outside any `CLIError` handling. The result is a traceback, not `{"error": ...}`.
   - A non-object `fleet.json` makes `configured_recipes_dir` raise `AttributeError` on `.get`.
4. **Exit codes can collide.** `run`, `exec-native`, and `env-exec` pass the remote exit code through. A remote exit of 1 or 124 looks the same as a CLI failure or a timeout, and ssh's own 255 is not documented. The doc partly covers this by pointing at `exit_code` in the JSON, but the ambiguity is worth one sentence in SKILL-cli.md.
5. **`run --json` decodes captured output with the locale encoding.** It reads `TemporaryFile("w+")` that way, so non-UTF-8 container output can raise `UnicodeDecodeError` after the job has finished. Opening the file in binary mode and decoding with `errors="replace"` would be safer.
6. **Behavior changes not called out in the issue:**
   - `env_create` now raises `Recipe not found` instead of silently falling back to `--image`. This also affects the DecafClaw tool path.
   - `scavenger_wake`'s "no wol_mac" message lost its `Error:` prefix (the `tools.py` hunk around line 109), and the `awake` variable is unused there.
   - In `scavenger_env_terminal`, `cfg = getattr(ctx, "config", None)` may now be dead.
   - When `recipes_dir` is set, `<workspace>/dockerfiles` is no longer searched inside DecafClaw. SKILL.md documents this.
7. **`exec-native` in the CLI calls `run_ssh` directly.** It does not share an engine function with the tool. Any eligibility or working-directory handling in the existing native-exec tool is not visible here and may differ. That risks a second convention for the same operation.
8. **Some tests are fragile.**
   - `test_wake_json_failure_exit_code` patches the global `time.time` with `side_effect=[0, 0, 5]`. One extra `time.time()` call in the code under test causes `StopIteration`.
   - `test_every_command_accepts_json_flag` checks only that the parser accepts the flag, which adds little beyond the per-command tests.
   - `test_resolve_recipe_has_no_hardcoded_home_path` scans `scavenger.py` but not `tools.py`.
9. **Script recipes are undocumented.** `resolve_recipe` also searches the primary recipes directory for setup scripts (`script_dirs = [primary]`), but SKILL-cli.md describes recipes as Dockerfiles only.

### Requirements coverage

- **No hardcoded path; order is `--recipes-dir`, then `recipes_dir` in fleet.json, then `./dockerfiles`:** Met. The `/home/lmorchard` fallbacks are removed from `scavenger.py` and `tools.py`. `configured_recipes_dir` and `resolve_recipe` follow the stated order, a relative `recipes_dir` is resolved against `fleet.json`, and the order has unit tests.
- **Labels renamed to `scavenger.*`, readers accept `decafclaw.*`:** Partially met. Writers use `LABEL_ENV_ID` and `LABEL_EXPIRES_AT`, and `parse_env_labels` accepts both prefixes and is tested. Nothing in production calls it, and the diff does not show whether any other label readers exist (finding 1).
- **Every command has `--json`, non-zero exit on failure, and new `wake`, `exec-native`, `env-info`:** Met, with gaps. All 11 subcommands share the `common --json` parent, errors go through `CLIError` and exit 1 or 124, the three new commands exist, and each command has a JSON test. The edge cases in finding 3 are not covered.
- **Generic CLI skill file that leaves out the canvas terminal and `wake_on`:** Met. SKILL-cli.md documents setup, output, commands, recipes, and rules, and lists the canvas terminal, `wake_on`, and `bg` only as "Not available in the CLI". The error-shape statement is inaccurate (finding 2).

### Quality assessment

The core changes are correct and well-factored. `find_fleet_config` and `wake_host` are extracted so the CLI and tools share them, the `CLIError` and `main(argv)` structure is clean, and the hardcoded workspace path is gone from both layers. The tests check real behavior: exact JSON payloads, propagated exit codes, which recipe file reaches `ensure_remote_image`, and the label strings in the create script. They would catch plausible regressions in recipe order, JSON shape, and exit-code handling. They do not exercise legacy label reading in any real code path, and one test patches the global clock in a brittle way. Scope stays mostly within the issue. A few small behavior changes slip in: an unknown recipe now fails hard, and a tool message changed wording. The remaining gaps are the unused label reader, the inconsistent error JSON for `wake` and `env-destroy`, and exception paths that skip the JSON and exit-code contract. None of these is a merge blocker, but all are worth fixing.

`minor`