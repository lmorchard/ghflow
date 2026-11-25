### Blocking findings

1. **Native environments now depend on a working container engine on the host** (`scavenger.py`, `list_host_envs` and the `kind == "native"` hunk in `env_create`).
   - **How it fails:** the listing script runs `{host.engine} ps …` and `{host.engine} volume ls …`. If either fails, it emits `---ERROR---`. Any `ERROR` section makes `list_host_envs` return `None` for the whole host, including the native section.
   - **Why it matters:** native targets are Apple Silicon Macs. The old native path only needed `mkdir`, never an engine. On a Mac with no podman/docker, or with podman machine stopped, three things break:
     - `env_create(kind="native")` always raises "Could not verify the native execution slot".
     - `env_list` and `env_reap` never see that host's native lease files. The host counts as unreachable, so expired native workspaces are never reaped.
   - **What the issue requires:** the native single-occupancy check should read the lease files on the host. It says nothing about needing the engine to answer.
   - **Test gap:** the tests use a fake runner that always returns a well-formed container section, so they cannot catch this.
   - **Fix:** treat an engine failure as "no container answer" separately from the native answer. For example, return per-section success, and let the native check and reconcile use whatever sections did succeed.

2. **Native workspaces created before this change are dropped from the cache and never reaped** (`reconcile_leases` together with `parse_native_leases`).
   - **How it fails:** older native workspaces have no `.scavenger-lease.json`. Once their host answers, `reconcile_leases` treats the host's listing as the full record. It drops the cached entry because "the host answered without it".
   - **Result:** after the first `env-list` or `reap` following the upgrade, in-flight native workspaces become exactly what the issue is trying to remove: orphans nothing reaps. The single-occupancy check also ignores them, so a second native lease can be granted on a busy Mac.
   - **Fix:** either backfill a lease file for cached native records whose workspace directory exists, or keep cached native records whose directory still exists. The listing script could emit workspace directories that have no lease file.

### Non-blocking findings

- **Every miss now probes the whole fleet, serially, while holding the cache lock** (`find_lease` → `sync_leases`). This hits `env_create` for any new `env_id` (the normal case) and `scavenger_env_info`/`exec`/`sync`/`terminal` with an unknown id. Each host can take up to the 20 s timeout. Sleeping or offline hosts therefore add long delays, and other writers wait on `lease_lock()` the whole time. Consider doing the SSH listing outside the lock and locking only for the read-merge-write, querying hosts in parallel, or checking only the selected host in `env_create`.
- **`update_lease`/`remove_lease` on a corrupt cache** move it aside and then write `{}` plus one record. They do not rebuild from the hosts. The next `sync_leases` repairs reachable hosts, and the quarantined file preserves the evidence, so this is acceptable. Still, it differs from the documented rule that a corrupt cache "is rebuilt from the hosts".
- **`load_leases()` without a fleet** still returns `{}` for a corrupt cache. It does log and set the file aside. No production caller in the diff uses that path, but the old "empty on corrupt" behavior survives as a public API. Consider making `fleet` required, or naming the no-fleet form as cache-only.
- **`reconcile_leases` fill rule** copies cached values into any field equal to `None`, `0`, or `0.0`. That also matches `False` and legitimate zero values. Today's fields make this mostly harmless, but it is fragile if fields are added.
- **`parse_labels` for Docker** splits on `,`, so a label value that contains a comma would be parsed wrongly. Our own labels are numeric or safe names, so the risk is low.
- **Volume discovery is label-only.** The issue allows "by name or label", so this is acceptable. But unlabelled `scavenger-vol-*` volumes from before the change become invisible once their container is gone.
- **The native host lock is controller-local** (`lease_lock(host.name)`). It does not prevent a second controller from racing the check-then-claim. The issue does not require cross-controller safety, but the comment "Check and claim in one step" overstates the guarantee.
- **Test issues:**
  - `test_update_lease_keeps_concurrent_writers_records` is sequential, so it does not test concurrency. The name overclaims; the lock test covers exclusivity instead.
  - `test_lease_lock_is_exclusive_across_file_descriptors` does `import fcntl` inside the function, against AGENTS.md's rule that stdlib imports go at module level.
- **Scope:** the `is_safe_name` validation of `env_id`, and excluding the lease file from `tar` in `env_sync` down, go beyond the issue. Both are justified: `env_id` is now embedded in a single-quoted JSON payload in a remote shell command, and the lease file should not leak into synced output. They should be called out in the PR description.

### Requirements coverage

- **Each host is the record; `env_list`/`env_reap` read container labels on each reachable host, and volumes by name or label:** partially met.
  - `list_host_envs` runs `ps --all --filter label=decafclaw.env_id --format json` and `volume ls --filter label=…`, and parses Podman arrays and Docker JSON lines. Volumes are now labelled at creation. `cmd_env_list`, `scavenger_env_list` and `env_reap` call `sync_leases`.
  - Gaps: a host with no working engine yields no listing at all (Blocking 1), and pre-existing native workspaces are lost (Blocking 2).
- **Native workspace holds a lease file; the single-occupancy check reads these files on the host:** partially met.
  - `.scavenger-lease.json` is written by the claim command, and the check reads it via `list_host_envs` under `lease_lock(host.name)`.
  - The check fails closed whenever the container engine query fails, and workspaces without a lease file are ignored.
- **`leases.json` is a cache; a corrupt cache is logged and rebuilt from the hosts:** met. `_read_cache_or_quarantine` logs and keeps the file as `leases.json.corrupt-<time>`. `sync_leases` and `load_leases(fleet)` rebuild from the hosts. `test_corrupt_cache_is_rebuilt_from_hosts_not_dropped` covers this.
- **Writes to the cache take a file lock:** met. `lease_lock()` uses `fcntl.flock`. All writes go through `save_leases`, `update_lease`, `remove_lease` or `sync_leases` under the lock, with per-PID temp files.

### Quality assessment

The core design is sound and follows the issue closely:
- Each host is treated as the record, and the cache is merged with host listings.
- A host that cannot answer is never mistaken for an empty host.
- Corrupt caches are quarantined.
- `env_destroy` only drops the cache entry after the host teardown succeeds.

The tests check real behavior: label parsing for both engines, reconcile semantics (host wins, offline or retired hosts keep their records), reaping after the cache is deleted, keeping the record when teardown fails, and the native lease file being written and read. They would catch plausible regressions in the merge and reap logic.

However, every fake host returns a successful engine section. That hides the native-host coupling to the container engine, and nothing exercises upgrading over existing native workspaces. Both gaps can break the native path on real Macs. Running fleet-wide SSH while holding the cache lock on every lookup miss is also a latency risk. Scope is mostly disciplined, and the code fits the module's stdlib-only style, apart from one function-local import in a test.

**Verdict:** needs-work