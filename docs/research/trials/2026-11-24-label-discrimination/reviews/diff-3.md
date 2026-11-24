### Blocking findings

None.

### Non-blocking findings

1. **The `env_destroy` docstring says the opposite of what the code does** (`scavenger.py`, `env_destroy` hunk @@ -827). The docstring says it "Returns True … when its lease is released because the host left the fleet." The code on that branch pops the lease, saves, and then `return False`. Effects downstream:
   - `env_reap` leaves that env out of `reaped`, even though the lease was released.
   - `scavenger_reap` can then say "No expired environments to reap."
   - `cmd_env_destroy` and `scavenger_env_destroy` say "not found or already destroyed."

   Either fix the docstring or return True and update the callers.

2. **Probe and create get slower while a host is asleep or offline** (`scavenger.py` `env_reap`/`env_destroy`; `tools.py` @@ -82). Failed leases are now kept and retried on every sweep. Each expired lease on an unreachable host costs one sequential SSH attempt (default timeout 15s, per the test's `run_ssh` signature) before `probe` or `env_create` continues. Sleeping laptops are the normal case in this fleet, so several expired leases there could add tens of seconds to every probe. The call is not blocked, but it is delayed. Consider skipping the other leases on a host after its first failure in a sweep, or using a short connect timeout for reaping.

3. **A lease can now get stuck with no way to clear it** (`scavenger.py` `env_destroy`). Before this change, `env_destroy` always released the lease. Now a host that stays in `fleet.json` but never comes back, or a native `rm -rf` that keeps returning non-zero, leaves the lease in place for good. For native kind, that lease is an exclusive slot lock. There is no `--force` or equivalent short of editing the lease file. This change is needed so reaping doesn't orphan containers, but it changes the user-facing `env_destroy` contract and is not mentioned in SKILL.md's `scavenger_env_destroy` section.

4. **Some failures can still abort the call** (`tools.py` @@ -82, `scavenger.py` @@ -514). `env_reap(fleet)` itself is not guarded. A failure in `load_leases()`, such as a corrupt or unreadable lease file, would make `probe` and `env_create` fail. That case is outside "one host fails", but one wrapper at the call sites would make it robust.

5. **Exceptions are caught twice** (`scavenger.py` `env_reap`). `env_destroy` already catches `Exception` around the SSH calls, and `env_reap` catches again. The outer catch only matters for errors outside the SSH block. That is harmless but redundant.

6. **New paths in `tools.py` have no tests** (`tools.py` @@ -566 and @@ -595). The "lease retained for retry" branch of `scavenger_env_destroy` and the "Could not reap … hosts are unreachable" branch of `scavenger_reap` are not tested. Both use `load_leases` and `time` in `tools.py`. `make check` passing suggests those names are imported, but no test exercises these branches.

7. **The tests never check the logging.** The issue says a failure "is logged", but no test asserts the stderr warning (e.g. with `capsys`).

8. **Probing one host reaps the whole fleet** (`tools.py` @@ -82). `scavenger_probe(host="x")` still runs `env_reap` across every host. That is reasonable, but SKILL.md doesn't mention it.

### Requirements coverage

- **`probe` and `env_create` reap expired environments first; a reap failure on one host is logged and does not block the call:** met.
  - `tools.scavenger_probe` and `cmd_probe` call `env_reap(fleet)` before probing.
  - `scavenger.env_create` calls `env_reap(fleet)` before loading leases.
  - Per-host failures (non-zero exit code or an exception) are printed to stderr and skipped, and the lease is kept.
  - Tests cover each path: `test_scavenger_probe_calls_reaper`, `test_scavenger_env_create_calls_reaper`, `test_reap_failure_does_not_block_probe`, `test_reap_failure_does_not_block_env_create`, `test_env_reap_continues_after_*`.
  - One caveat: an unreachable host adds latency (finding 2).
- **Optional host-side reaper (systemd/launchd) plus ENROLLMENT.md docs, after #1723:** not met. The issue marks this optional and dependent on #1723, so leaving it out is acceptable, and no doc claims it exists.

### Quality assessment

The controller-side reap is correct and does what the issue asks. The author also fixed a real latent bug: `env_destroy` used to drop the lease before the remote teardown, so a failed reap would have orphaned the container. That fix is in scope. The tests check behavior rather than just mocks: they assert the destroy command reached the right host, that leases are released or kept as appropriate, and that `env_create` still reserves on another host when reaping on a failing host fails. They would catch a regression where reaping is removed or a failure aborts the sweep. The weak spots are small:
- the `env_destroy` docstring contradicts its return value on the host-left-fleet branch;
- there is no escape hatch for leases on hosts that never come back;
- the new `tools.py` failure messages are untested;
- every probe retries unreachable hosts, which costs time.

The code follows the module's existing patterns (no bare except, stdlib only, tests in contrib), and the docs match the new behavior.

`minor`