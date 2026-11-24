### Blocking findings

1. **The native check fails when the container engine fails.** In `scavenger.py`, `list_host_script` / `parse_host_listing` (new hunk around `list_host_script`), the remote script runs `{engine} ps ... || echo ---FAILED---` and `{engine} volume ls ... || echo ---FAILED---`. `parse_host_listing` then returns `None` for the whole host on any `---FAILED---`, including the native section. The native single-occupancy check in `env_create` (the `if kind == "native":` hunk) treats `None` as fatal: "Cannot verify native execution slot". `reconcile_leases` treats the same host as unreachable, and `env_reap` then skips it. So whenever the engine on an Apple Silicon host is absent or not working, this happens:
   - Native environments can no longer be created.
   - Existing native workspaces on that host are never reaped.

   On macOS this is common: podman needs a running `podman machine`. The issue asks for the native check to "read these files on the host", and that has nothing to do with engine health. The native section should be parsed on its own, and only the container and volume sections should be marked untrusted. Native creation should not depend on the engine.

### Non-blocking findings

- **Native workspaces created before this change are dropped from the cache.** They have no `.scavenger-lease.json`. Once their host is reachable, `reconcile_leases` deletes their cache entries, because they are not in the listing and `created_at < started`. After that they are invisible to the occupancy check, `env-list` and `reap`, so they are orphaned. Containers made before this change still work because they already carried the `env_id` and `expires_at` labels. Consider a fallback that recognises a bare `workspaces/<id>` directory, or a note about migration.
- **Moving a corrupt cache aside happens outside the lock.** `load_leases` can call `os.replace(LEASES_FILE, quarantine)` when called from `find_lease`, which does not hold the lock. If another process does a locked `_write_leases` between this process's failed read and its `os.replace`, a freshly written valid cache can be moved aside. A transient `OSError`, such as a permission error, also moves the file aside. Doing the move under `_leases_lock()` would avoid this.
- **Fleet scans are slow and sequential.** `reconcile_leases` SSHes to every host in turn with a 20s timeout. The following now pay that cost:
  - every `env_list`;
  - every `reap`;
  - every `env_create`, because a new `env_id` is always a cache miss in `find_lease`, and native creates add one more listing;
  - every cache miss in the tool layer.

  Hosts that sleep and wake on Wake-on-LAN make this slow. Scanning in parallel, or skipping the full scan in `env_create`, would help.
- **The scan-start guard in `reconcile_leases` has a race.** Suppose `env_create` starts before a reconcile scan (`created_at < started`), the listing runs before the container exists, and the lease is recorded before `apply`. The new cache entry is then deleted. Only the cache is affected and the next reconcile restores it from the labels, but the comment overstates what the guard protects.
- **The occupancy check is not atomic.** Two native creates at the same time on one host can both see the slot free (list, then write). This was already true before the change, and the issue does not require atomicity, but it is worth a note.
- **An unreachable-host warning can be lost.** `tools.py` `scavenger_env_list` returns "No active environment reservations." before the unreachable note is added. If every host is unreachable and the cache is empty, the user gets a misleading "none" with no warning.
- **An unreadable native lease file frees the slot.** Such a file is ignored with only a warning, so the host looks free.
- **Volume labels can go stale.** `volume create {labels} ... || true` does not relabel an existing volume, so a reused `env_id` keeps old volume labels. The merge order (container labels win) hides this in most cases.
- **Imports break the AGENTS.md convention.** In `test_tools.py`, `import threading` in `test_concurrent_cache_updates_do_not_lose_leases` and `import fcntl` in `test_cache_lock_is_exclusive_across_processes` are inside the functions. AGENTS.md wants stdlib imports at module level. The removal of the inline `import base64` lines in `scavenger.py` is a good fix.
- **The concurrency test is weak.** The 20-thread lost-update test may pass even without the lock, because of the GIL. The `LOCK_NB` probe test is the one that actually proves the lock is exclusive.

### Requirements coverage

- **Hosts as the record; `env_list`/`env_reap` read container labels and volumes on each reachable host: met.** The `list_host_script` command matches the issue. Podman and Docker output are both parsed (`parse_engine_json`, `parse_labels`). Volumes are now labelled and listed. Unreachable hosts keep their cached records.
- **Native lease file in `workspaces/<env_id>/`, and the occupancy check reads it on the host: partially met.** The file is written in `env_create` and read via `list_host_envs`. The read only succeeds if the container engine commands also succeed (blocking finding 1), and workspaces created before this change have no lease file.
- **`leases.json` becomes a cache; a corrupt cache is logged and rebuilt: met.** `load_leases` logs and moves the file aside. `reconcile_leases` and `find_lease` rebuild it from the hosts. `test_corrupt_cache_is_logged_and_rebuilt_not_dropped` covers this.
- **Writes to the cache take a file lock: met.** `_leases_lock`, `save_leases` and `update_leases` handle this, and reconcile, create and destroy all go through `update_leases`. The one gap is that the corrupt-file move happens outside the lock.

### Quality assessment

The design is sound and is a faithful reading of the issue. The hosts are the record, the cache is reconciled from them, unreachable hosts are handled carefully (cached records kept, not reaped), and teardown no longer drops a lease when it fails. The tests check real behaviour through a fake SSH runner:
- label parsing for podman and Docker formats;
- reconciliation, including stale entries and unreachable hosts;
- rebuilding a corrupt cache;
- the issue's manual check (delete the cache, then list and reap);
- host-side native occupancy;
- the lock being exclusive.

These tests would catch most plausible regressions. They do not catch the main defect, because the fake listing always succeeds for the container section. In that defect, one SSH script ties native lease discovery to container engine health, which can block native creates and stop native workspaces from being reaped on Mac hosts. Scope is reasonable: routing the tool layer through `find_lease` and the safer `env_destroy` follow directly from the issue. Sequential full-fleet scans on common paths and the two import-convention slips are smaller maintainability concerns.

**Verdict:** needs-work