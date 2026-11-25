### Blocking findings

None.

### Non-blocking findings

1. **`read_env_labels` is never called** (`scavenger.py`, hunk at about line 115). The diff adds the helper and its label constants, and only the container-create script uses `LABEL_ENV_ID` and `LABEL_EXPIRES_AT`. No production code calls `read_env_labels`. Reaping still works from `leases.json`, not from labels. The issue says #1723 will read the labels, so this is acceptable as groundwork. Still:
   - The three label tests only exercise an unused helper.
   - From the diff alone I can't rule out an existing reader elsewhere that still filters on `decafclaw.*`. Any such reader would now miss new containers. Before merge, search the code for `decafclaw.env_id` and `decafclaw.expires_at`.
2. **Recipes in `workspace/skills/scavenger/` may no longer be found** (`resolve_recipe` hunk, and the `tools.py` `scavenger_env_create` hunk).
   - The old search included `<ws>/skills/scavenger/dockerfiles` and `<ws>/skills/scavenger/setup-scripts`. The new search uses `<ws>/dockerfiles`, `<ws>/setup-scripts` and `SCRIPT_DIR`.
   - If the running code is not the copy inside the workspace skill folder, recipes kept there are no longer found. `SKILL.md` still lists `"rust-builder"`, but the tests say only `node-dev` and `android-builder` ship with the skill.
   - An unknown recipe now raises an error (the old code silently ignored it), so this change will be visible rather than silent.
3. **Bundled recipes are added as a fourth fallback** (`resolve_recipe`). The issue names three sources. The extra one is documented and makes the issue's own Verify step (`env-create --recipe node-dev`) work, so it is fine. But the setup-script directory is derived from the recipes directory (`dirname(base)/setup-scripts`). This rule is new and implicit; it is documented only in `SKILL-cli.md`.
4. **`cmd_probe` probes before it fails on an unknown host** (`cmd_probe` hunk). It still probes, and may wake, every known host before failing on the unknown one. The old code skipped the unknown host and printed results for the rest. Checking for unknown hosts before probing would avoid needless Wake-on-LAN packets.
5. **`cmd_run --json` loses output on timeout** (`cmd_run` hunk). If `execute_job` raises `TimeoutExpired`, `main` prints a JSON error and the captured stdout and stderr are thrown away. Also, there is no test for the auto-select path (no `--host`). If `select_best_host` exits or prints instead of raising, the `--json` contract breaks on that path.
6. **`env-create` errors are not JSON by default.** On success it "always prints JSON". On failure without `--json` it prints a text error to stderr. This matches the documented rules, but shell agents may be surprised.
7. **`test_missing_fleet_config_fails_nonzero` is fragile** (`test_cli.py`).
   - It replaces `os.path.expanduser` everywhere with `p.lstrip("~/")`, which strips characters, not a prefix.
   - It would fail if a `fleet.json` sits next to `scavenger.py` in a developer's checkout, because that fallback path is still searched.
8. **`test_every_subcommand_accepts_json` uses private argparse internals** (`_actions`, `_SubParsersAction`). This works, but it is brittle.
9. **`SKILL-cli.md` says "Python 3.9+".** The engine looks 3.9-compatible, but the new tests use parenthesized multi-item `with` blocks, which need Python 3.10. This is harmless for the repo's own runs but worth knowing.
10. **The CLI and tools layer each implement some commands separately.**
    - `scavenger_wake` in `tools.py` still checks `wol_mac` itself, although `wake_host` does the same check.
    - `cmd_env_info` and `cmd_exec_native` build their own output instead of sharing an engine function with the matching tools.
    - Not a second convention, but some duplication.

### Requirements coverage

- **No hardcoded path; order is flag, then `fleet.json` `recipes_dir`, then `./dockerfiles`:** met. All `/home/lmorchard` paths are gone from `scavenger.py` and `tools.py`, and a test checks this. `resolve_recipes_dir` follows the required order and resolves a relative path against `fleet.json`. The CLI flag `--recipes-dir` exists. Bundled recipes are an extra, documented final fallback.
- **`scavenger.*` labels, readers accept `decafclaw.*`:** partially met. New containers get `scavenger.env_id` and `scavenger.expires_at`, and a test confirms the create script has no `decafclaw.` labels. `read_env_labels` accepts both names and is tested, but nothing calls it yet; reaping still uses the lease file.
- **Every command takes `--json` and exits non-zero on failure; new `wake`, `exec-native` and `env-info` commands:** met. `--json` comes from a shared parent parser on every subcommand, with a test for this. `main` returns exit codes through `sys.exit(main())`. Errors go through `_fail`, and the three new commands exist. Every command has a JSON test.
- **Generic skill file for shell-only agents, without the canvas terminal or `wake_on`:** met. `SKILL-cli.md` documents setup, rules, all commands, recipe order and labels. It states that the canvas terminal and `wake_on` are tool-only. `FLEET.md` and `SKILL.md` link to it.

### Quality assessment

The engine changes are correct as far as the diff shows:
- Recipe directory selection, the label rename and the JSON/exit-code CLI are straightforward.
- Moving the wake logic into `wake_host` takes duplicate logic out of `tools.py`.
- `main(argv)` makes the CLI testable without starting a subprocess.

The tests mostly check real behavior: exact JSON payloads, exit codes passed through from the remote command, the order of recipe sources, the labels in the generated create script, and an end-to-end `env-create` run from outside the workspace with `recipes_dir` set. Any of these would catch a plausible regression.

There are two gaps. The label-fallback tests cover a helper that nothing calls yet, and the CLI `--recipes-dir` flag and auto-select `run` path are not tested. Scope is well kept: there is no daemon, no packaging and no `wake_on` replacement. The main risk for maintainers is the narrower recipe search for decafclaw users.

`minor`