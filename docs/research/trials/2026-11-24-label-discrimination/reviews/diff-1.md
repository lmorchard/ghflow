### Blocking findings

None.

### Non-blocking findings

1. **The `default` mode now sends a flag that was never sent before.** See `scavenger.py`, `container_limit_flags`: `flags = [f"--network={network}"]`. On the base commit, the run and create scripts had no `--network` flag. With this diff they always get `--network=default`. Docker reads `default` as its normal bridge network. Rootless Podman uses different network names, such as `podman`, `pasta` and `slirp4netns`, so the effect there is less clear. The issue says "the default stays `default` … so existing recipes … keep working." The safest way to keep that promise is to send no flag when the mode is `default`, and only add `--network=none` when asked. The tests only check that the string is present, so nothing confirms that the engines accept `--network=default`.

2. **The log options are chosen by engine name, not by log driver.** See `scavenger.py`, `LOG_OPT_ENGINES` and the `--log-opt` block. The code, `FLEET.md` (principle 3 and the checklist) and `SKILL.md` all describe a "json-file log driver". But:
   - Rootless Podman usually defaults to `journald` or `k8s-file`, not json-file. Podman's documented `--log-opt` keys are `path`, `max-size` and `tag`; `max-file` is not one of them.
   - A Docker daemon set to use `journald` rejects `max-size` and `max-file`. When that happens, every container fails to start.

   The issue's wording is "where the engine supports it". The code assumes support for any `docker` or `podman` engine. Two fixes would help: make the log options opt-in per host (for example, only send them when `log_max_size` is set), or document which log driver they need. The Podman test also checks only `max-size`.

3. **The list of network modes is defined four times:**
   - the tuple inside `container_limit_flags`
   - `NETWORK_MODES` in `tools.py`
   - `choices=["none", "default"]` twice in `argparse`
   - the `enum` lists in both `TOOL_DEFINITIONS` entries

   It would be better to define one constant in `scavenger.py` and import it everywhere. The two copies of the error message in `tools.py` could also share one helper.

4. **The type and the comment for `pids_limit` do not match the code.** The field is declared as `int` with the comment "-1 disables the cap". But `container_limit_flags` checks `is not None`, a check that only does something if `fleet.json` contains `null`. A value of -1 is passed straight to the engine. If `None` is meant to be a valid value, declare the field as `Optional[int]` and document what each value does.

5. **`network` is quietly ignored when `kind="native"`.** `env_create` only uses `network` on the container path. A caller that sets `kind="native", network="none"` gets no warning. The `SKILL.md` text says "Container network mode", but a short note or a warning would avoid confusion.

6. **Invalid network values can reach `env_create` in some paths.** The `ValueError` is raised inside the container branch of `env_create`, after a host has been chosen. The diff does not show whether a lease could already be saved by then. The tool layer and the CLI check the value first, but a direct Python call to the engine would not. Checking `network` at the start of `env_create` and `execute_job` would make this safe.

7. **Some test gaps:**
   - No test covers how the CLI passes `--network` through (`cmd_run` and `cmd_env_create` forwarding `args.network`).
   - No test shows that a valid `network` reaches `env_create` through the `scavenger_env_create` tool. Only the invalid case is tested.
   - The log-option tests check that the tokens exist in the list, but not that each value follows its `--log-opt`.

8. **The manual check was not reported.** The gate results do not include the `wget` check from the issue's Verify section. Because of item 1, the "same command without `--network none` succeeds" half matters most for Podman hosts.

9. **I cannot tell whether every container launch is covered.** The diff updates the `execute_job` scripts (both branches), the `env_create` container script, and the scripts in the `scavenger_run` tool (both branches). Any other `run` or `create` call not shown in the diff would still lack the limits. The issue also depends on #1724 (argument builders). This diff adds a separate `container_limit_flags` helper and joins its output into inline f-string scripts. If #1724's builders exist at the base commit, this may be a second way of doing the same thing, which `AGENTS.md` forbids. That is worth checking.

### Requirements coverage

- **`network` parameter (`none`/`default`, default `default`, skill text recommends `none`):** Met.
  - Added to `scavenger_run` and `scavenger_env_create` in `tools.py`, with the JSON schema `enum`.
  - Added to `execute_job` and `env_create` in the engine, and to the CLI `run` and `env create` commands.
  - The default is `"default"`.
  - `SKILL.md` says "Prefer `"none"` for test runs that need no downloads".
  - Caveat: item 1, the `default` mode now sends an explicit flag.
- **`--pids-limit` on every container, configurable in `fleet.json` `limits`:** Met for the launch paths shown in the diff.
  - `pids_limit` defaults to 4096 and is loaded from `limits.pids_limit`.
  - It is passed to all three script sites in the engine and both sites in `tools.py`.
  - Tests cover the default value, a custom value, and loading from config.
- **Log size limit where the engine supports it:** Partially met.
  - `--log-opt max-size` and `max-file` are added for docker and podman, are configurable, and are tested.
  - Support is decided by engine name rather than by the log driver actually in use, and the `max-file` claim for Podman is shaky (item 2).

### Quality assessment

The change is small and coherent. It gathers all the new flags into one pure builder function and passes them through the engine, the tool layer and the CLI. Invalid values are checked up front in the tool layer. The tests test real behavior: they cover the builder for each option, as the issue asks, and also check the generated remote scripts for `execute_job`, `env_create` and the `scavenger_run` tool. If someone removes `limit_args` from one of the scripts that has a test, the tests would catch it. However, they only check that strings are present, so they could not catch an engine rejecting `--network=default` or an unsupported log option. Those are the two real risks in this diff. The change stays within scope and the docs are updated consistently. The main maintenance cost is the network-mode list repeated in four places, on top of the copied script templates in `tools.py`, which existed before this change.

Verdict: `minor`