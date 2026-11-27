#!/usr/bin/env python3
"""Deterministic runner that drives unattended delivery from the project board."""
import argparse
import json
import os
import re
import select
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import monitor as monitor_mod
import narrative

DEFAULT_FLOOR_MINUTES = 30
CORRECTION_LIMIT = 2
DEFAULT_MAX_TURNS = 150
DEFAULT_SESSION_TIMEOUT = 5400
DEFAULT_STEP_IDLE_TIMEOUT = 900
# Context thresholds are measured by step_context_tokens(), which sums uncached
# input plus cache reads plus cache writes. On a long agentic session most of
# that total is cache traffic, so a 100k warning fired on ordinary work: the
# 2026-11-27 burndown produced three alerts at 105k/131k/111k while every
# session completed normally. A warning that always fires carries no signal, so
# the default moved to a level that means "this prompt is genuinely large".
# Raise with --context-warn-tokens if a deployment really does run smaller.
DEFAULT_CONTEXT_WARN_TOKENS = 200000
DEFAULT_MAX_CONTEXT_TOKENS = 0
LOCAL_MODEL_PROVIDERS = ("lmstudio", "ollama", "mlx", "rec", "llama.cpp")
SLOW_STEP_WARN_SECONDS = 120
MAX_DEGENERATE_REASONING = 10000
PRIORITY_ORDER = ("P0", "P1")
SIZE_ORDER = ("XS", "S", "M", "L", "XL")
_RUN_LOCK = None


def resolve_worker_cmd(options=None):
    """Resolve the executable command for running worker sessions.

    Precedence:
    1. options["worker_cmd"]
    2. options["opencode_cmd"] (deprecated alias)
    3. GHFLOW_WORKER_CMD environment variable
    4. GHFLOW_OPENCODE_CMD environment variable (deprecated alias)
    5. "opencode" default
    """
    opts = options or {}
    return (
        opts.get("worker_cmd")
        or opts.get("opencode_cmd")
        or os.environ.get("GHFLOW_WORKER_CMD")
        or os.environ.get("GHFLOW_OPENCODE_CMD")
        or "opencode"
    )


def find_cli():
    """Locate cli/ghflow.py."""
    env_cli = os.environ.get("GHFLOW_CLI")
    if env_cli and Path(env_cli).is_file():
        return Path(env_cli)
    repo_cli = Path(__file__).resolve().parent.parent / "cli" / "ghflow.py"
    if repo_cli.is_file():
        return repo_cli
    raise FileNotFoundError("Could not locate cli/ghflow.py. Set GHFLOW_CLI.")


def parse_worker_major(version):
    """Return the worker's major version from its --version text, or 1 when unreadable."""
    match = re.search(r"(\d+)\.\d+", version or "")
    return int(match.group(1)) if match else 1


_WORKER_MAJOR_CACHE = {}


def worker_major(worker_cmd=None):
    """Return the OpenCode major version for worker_cmd, cached per command.

    ``--standalone`` only exists in OpenCode 2.x; 1.x rejects it and prints help
    instead of running, which fails every session. The probe is best-effort: an
    unreadable version falls back to 1, the conservative choice.
    """
    worker = worker_cmd or resolve_worker_cmd()
    if worker in _WORKER_MAJOR_CACHE:
        return _WORKER_MAJOR_CACHE[worker]
    version = ""
    try:
        proc = subprocess.run([worker, "--version"], capture_output=True, text=True, timeout=10)
        version = (proc.stdout or "") + (proc.stderr or "")
    except (OSError, subprocess.SubprocessError):
        version = ""
    major = parse_worker_major(version)
    _WORKER_MAJOR_CACHE[worker] = major
    return major


def worker_run_flags(worker_cmd=None):
    """Return the flags that start an isolated worker run for this OpenCode major."""
    return ["--standalone"] if worker_major(worker_cmd) >= 2 else []


def run_cli(*args, cwd=None, cli_path=None):
    """Run a ghflow command as a subprocess and return parsed JSON output and exit code."""
    cli = str(cli_path or find_cli())
    cmd = [sys.executable, cli, *args]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    out = None
    if proc.stdout.strip():
        try:
            out = json.loads(proc.stdout)
        except json.JSONDecodeError:
            out = {"raw": proc.stdout}
    if not out:
        out = {}
    if proc.returncode != 0:
        err = proc.stderr.strip()
        if err:
            out["stderr"] = err
            if "error" not in out:
                out["error"] = err
    return out, proc.returncode


def load_board_index(owner, project, cli_fn=run_cli):
    """Return issue number -> board fields for every Issue on the board."""
    if not owner or not project:
        return {}
    data, code = cli_fn("queue", "items", "--owner", str(owner), "--project", str(project))
    if code != 0:
        print(f"[{time.strftime('%X')}] Board item read failed (exit {code}); using sub-issue order", flush=True)
        return {}
    return {item["number"]: item for item in data.get("items") or []
            if isinstance(item, dict) and isinstance(item.get("number"), int)}


def board_rank(number, board_index=None):
    """Rank a child by board priority, then size, then issue number."""
    item = (board_index or {}).get(number) or {}
    priority = item.get("priority")
    p_rank = PRIORITY_ORDER.index(priority) if priority in PRIORITY_ORDER else (
        len(PRIORITY_ORDER) if priority else len(PRIORITY_ORDER) + 1)
    size = (item.get("size") or "").upper()
    s_rank = SIZE_ORDER.index(size) if size in SIZE_ORDER else len(SIZE_ORDER)
    return (p_rank, s_rank, number)


def issue_turn_limit(explicit=None):
    """Return the session turn cap: explicit override, else the flat default."""
    return explicit or DEFAULT_MAX_TURNS


def normalize_model(value, provider=None):
    """Apply the run-wide provider prefix to a model ID without a slash."""
    value = str(value).strip()
    if provider and "/" not in value:
        return f"{provider}/{value}"
    return value


def is_local_model(model):
    """Return whether a model ID uses a local provider."""
    value = str(model)
    provider = value.split("/", 1)[0] if "/" in value else ""
    return provider in LOCAL_MODEL_PROVIDERS


def select_models(implementation, review, provider=None, allow_remote=False):
    """Normalize and validate the implementation and review models.

    Returns ``(models, error)``. Both models must use a local provider unless
    ``allow_remote`` is set, which admits any provider — a homelab gateway or a
    cloud API — for a run that deliberately asks for one.
    """
    models = {"implementation": normalize_model(implementation, provider),
              "review": normalize_model(review, provider)}
    if allow_remote:
        return models, None
    for role, model in models.items():
        if not is_local_model(model):
            return None, (f"{role} model `{model}` is not local. "
                          f"Use a local provider: {', '.join(LOCAL_MODEL_PROVIDERS)}. "
                          f"Pass --allow-remote-models to use a homelab gateway or cloud provider.")
    return models, None


def remote_model_notice(models):
    """Name the non-local providers a run will use, or return None when all are local."""
    remote = [f"{role} `{model}`"
              for role, model in models.items()
              if not is_local_model(model)]
    if not remote:
        return None
    return (f"Using non-local models ({', '.join(remote)}). "
            f"These may incur cost; local providers are preferred.")


def format_models(models):
    """Render one issue's model choice for the run summary."""
    if not models:
        return "-"
    return f"{models.get('implementation', '-')} / {models.get('review', '-')}"


def unload_local_models(model, runner=None, which=None, home=None):
    """Unload LM Studio models before a session that uses another model."""
    if os.environ.get("GHFLOW_NO_MODEL_UNLOAD"):
        return {"status": "skipped", "reason": "disabled"}
    value = str(model)
    provider = value.split("/", 1)[0] if "/" in value else ""
    if provider != "lmstudio":
        return {"status": "skipped", "reason": "not lmstudio"}
    which = which or shutil.which
    lms = which("lms")
    if not lms:
        candidate = Path(home or Path.home()) / ".lmstudio" / "bin" / "lms"
        lms = str(candidate) if candidate.is_file() else None
    if not lms:
        return {"status": "skipped", "reason": "lms not found"}
    runner = runner or subprocess.run
    try:
        result = runner([lms, "unload", "--all"], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"status": "failed", "reason": str(error)}
    reason = (result.stdout or result.stderr or "").strip()
    return {"status": "unloaded" if result.returncode == 0 else "failed", "reason": reason}


def verification_lines(body):
    """Return the issue's Verify lines, if it declares them."""
    return [line.strip() for line in (body or "").splitlines()
            if re.match(r"^\s*\*\*Verify\.\*\*", line, re.IGNORECASE)]


def acquire_run_lock(notes_dir, target=None, lock_path=None):
    """Hold one advisory lock for the run; refuse when another runner holds it.

    The lock file also records the holder for a human. The file lock is released by
    the operating system when the process exits, so a crash does not require a stale
    PID cleanup.

    Without ``lock_path``, ``GHFLOW_RUNNER_LOCK`` names the file, and the default is
    ``~/.local/state/ghflow/runner.lock``. Tests set the variable so that they never
    take a live runner's lock.
    """
    global _RUN_LOCK
    if _RUN_LOCK is not None:
        # A CLI process runs one queue. A second call in the same process (tests)
        # reuses the held descriptor instead of fighting its own lock.
        fp = _RUN_LOCK
        fp.seek(0)
        fp.truncate()
        fp.write(json.dumps({
            "pid": os.getpid(),
            "started": time.strftime("%Y-%m-%d %H:%M:%S"),
            "target": target,
            "notes_dir": str(notes_dir),
        }) + "\n")
        fp.flush()
        return fp
    path = Path(lock_path or os.environ.get("GHFLOW_RUNNER_LOCK")
                or Path.home() / ".local/state/ghflow/runner.lock")
    path.parent.mkdir(parents=True, exist_ok=True)
    fp = open(path, "a+", encoding="utf-8")
    try:
        import fcntl
    except ImportError:
        fcntl = None
    if fcntl is not None:
        try:
            fcntl.flock(fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            fp.seek(0)
            holder = fp.read().strip()
            fp.close()
            raise RuntimeError(f"Another queue runner holds {path}: {holder or 'unknown holder'}")
    fp.seek(0)
    fp.truncate()
    fp.write(json.dumps({
        "pid": os.getpid(),
        "started": time.strftime("%Y-%m-%d %H:%M:%S"),
        "target": target,
        "notes_dir": str(notes_dir),
    }) + "\n")
    fp.flush()
    _RUN_LOCK = fp
    return fp


def read_run_lock_holder(lock_path=None):
    """Return the current lock holder record, or an error record."""
    path = Path(lock_path or os.environ.get("GHFLOW_RUNNER_LOCK")
                or Path.home() / ".local/state/ghflow/runner.lock")
    try:
        holder = json.loads(path.read_text(encoding="utf-8").strip() or "{}")
    except (OSError, ValueError) as error:
        return {"path": str(path), "error": str(error)}
    holder["path"] = str(path)
    return holder


def project_owner(project):
    """Return the owner login for a projectsV2 node, from its owner or path."""
    owner = project.get("owner")
    if isinstance(owner, dict):
        login = owner.get("login")
        if isinstance(login, str) and login:
            return login
    for key in ("resourcePath", "url"):
        value = project.get(key)
        if not isinstance(value, str):
            continue
        match = re.search(r"/(?:users|orgs)/([^/]+)/projects/\d+", value)
        if match:
            return match.group(1)
    return None


def discover_project(owner_project=None, cwd=None, gh_cmd="gh"):
    """Return (owner, number) for the project board, or raise an error."""
    if owner_project:
        parts = owner_project.split("/")
        if len(parts) == 2 and parts[1].isdigit():
            return parts[0], int(parts[1])
        raise ValueError(f"Invalid --project format '{owner_project}'; expected OWNER/NUMBER.")
    proc = subprocess.run([gh_cmd, "repo", "view", "--json", "projectsV2"], cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to query repository projects: {proc.stderr.strip()}")
    data = json.loads(proc.stdout) if proc.stdout.strip() else {}
    raw = data.get("projectsV2") or []
    if isinstance(raw, dict):
        raw = raw.get("Nodes") or raw.get("nodes") or []
    projects = [p for p in raw if isinstance(p, dict) and not p.get("closed")]
    if len(projects) == 1:
        proj = projects[0]
        owner = project_owner(proj) or ""
        number = proj.get("number")
        if owner and number is not None:
            return owner, int(number)
    if not projects:
        raise RuntimeError("No open projects found for repository. Pass --project OWNER/NUMBER.")
    names = [f"{project_owner(p) or '?'}/{p.get('number')} ({p.get('title')})" for p in projects]
    raise RuntimeError(f"Multiple open projects found: {', '.join(names)}. Pass --project OWNER/NUMBER.")


def is_runner_or_session_process_alive(current_pid=None):
    """Check if another run_queue.py or an opencode run process is alive on the system."""
    if current_pid is None:
        current_pid = os.getpid()
    try:
        proc = subprocess.run(["ps", "-eo", "pid,args"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if proc.returncode != 0:
            proc = subprocess.run(["ps", "-eo", "pid,command"], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
        if proc.returncode != 0:
            return True
        stdout = proc.stdout.strip()
        if stdout.startswith(("[", "{")):
            return True
        for line in stdout.splitlines():
            parts = line.strip().split(None, 1)
            if len(parts) < 2:
                continue
            try:
                pid = int(parts[0])
            except ValueError:
                continue
            if pid == current_pid:
                continue
            cmd = parts[1]
            if "opencode run" in cmd and "def is_runner_or_session_process_alive" not in cmd:
                return True
        return False
    except Exception:
        return True


def check_active_runs(worker_cmd=None, process_checker=None):
    """Raise RuntimeError if an unattended session was active in the last 30 minutes and its process is alive."""
    cmd = worker_cmd or resolve_worker_cmd()
    if not shutil.which(cmd):
        return
    proc = subprocess.run([cmd, "session", "list", "--format", "json"], stdin=subprocess.DEVNULL,
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return
    try:
        sessions = json.loads(proc.stdout)
    except (ValueError, json.JSONDecodeError):
        return
    now_ms = time.time() * 1000
    active = []
    for s in sessions if isinstance(sessions, list) else []:
        t = s.get("time")
        updated = t.get("updated") if isinstance(t, dict) else (t or s.get("updated"))
        title = str(s.get("title") or "")
        if (title.startswith("Unattended burndown") or title.startswith("Queue runner")) and isinstance(updated, (int, float)):
            if now_ms - updated < 30 * 60 * 1000:
                active.append(f"{s.get('id')} ({title})")
    if active:
        is_alive = process_checker() if process_checker is not None else is_runner_or_session_process_alive()
        if is_alive:
            raise RuntimeError("An unattended burndown session was active in the last 30 minutes:\n  " +
                               "\n  ".join(active) + "\nPass --allow-concurrent to override.")
        print(f"[{time.strftime('%X')}] Stale unattended session records found in database, "
              "but no active runner or worker process is alive. Proceeding.", flush=True)


def is_verdict_blocking(verdict_entry):
    """Determine whether a review verdict entry contains blocking feedback."""
    if not verdict_entry:
        return False
    v = verdict_entry.get("verdict")
    if v == "blocked":
        return True
    if v != "findings":
        return False
    body = verdict_entry.get("body") or ""
    m = re.search(r"##\s*Blocking findings[ \t]*\n(.*?)(?:\n##|\Z)",
                  body, re.IGNORECASE | re.DOTALL)
    if m:
        val = m.group(1).strip().lower().rstrip(".")
        if val in ("", "none", "no blocking findings", "no blockers",
                   "none —", "none -", "- none", "- no blocking findings"):
            return False
    return True


def next_step(state, correction_limit=CORRECTION_LIMIT, machine_login="MokaGnome"):
    """Pure function returning the next operation for an observed issue state."""
    labels = state.get("labels") or []
    if "triage:needs-input" in labels:
        return "PARKED"
    pr = state.get("pr")
    if not pr or not pr.get("url"):
        return "implement-issue"

    current_head = pr.get("head")
    is_draft = pr.get("is_draft", pr.get("draft", False))
    if pr.get("mergeable") == "CONFLICTING":
        return "repair-conflict"
    reviews = state.get("reviews") or []
    rev_summary = state.get("review_summary") or {}

    # Native GitHub reviews covering the current head
    head_reviews = [r for r in reviews if r.get("covers_head") or r.get("commit") == current_head]
    changes_requested = rev_summary.get("changes_requested") or [
        r.get("author") for r in head_reviews if r.get("state") == "CHANGES_REQUESTED"
    ]
    approved = (rev_summary.get("state") == "approved") or any(r.get("state") == "APPROVED" for r in head_reviews)

    # Also check review verdicts (fallback for automated inter-agent comment markers)
    verdicts = state.get("review_verdicts") or []
    head_verdict = next((v for v in reversed(verdicts) if v.get("head") == current_head), None)
    verdict_blocking = is_verdict_blocking(head_verdict)
    verdict_clean = head_verdict and (head_verdict.get("verdict") == "clean" or not verdict_blocking)

    has_blocking_feedback = bool(changes_requested) or verdict_blocking
    earlier_blocking = sum(1 for r in reviews if r.get("state") == "CHANGES_REQUESTED") + \
                       sum(1 for v in verdicts if is_verdict_blocking(v))

    if is_draft:
        if not head_reviews and not head_verdict:
            return "review-changes"
        if has_blocking_feedback:
            return "park-blocker" if earlier_blocking >= correction_limit else "address-pr-review"
        if approved or verdict_clean or head_reviews:
            return "submit-pr"
        return "review-changes"

    # PR is ready (not a draft)
    ci = (state.get("ci") or "").lower()
    if ci in ("pending", "", "incomplete"):
        return "wait-ci"
    if ci in ("failing", "failed", "error", "missing") or state.get("unresolved_threads"):
        return "address-pr-review"
    if has_blocking_feedback:
        return "park-blocker" if earlier_blocking >= correction_limit else "address-pr-review"
    if state.get("pending_review_requests"):
        return "WAITING"
    if ci in ("green", "passed"):
        # A stale local verdict means the head changed since review, for
        # example after a conflict repair. Require a review at the current
        # head; a PR with no local verdict keeps the DONE path for human review.
        verdicts = state.get("review_verdicts") or []
        return "review-changes" if verdicts and not (verdict_clean or approved) else "DONE"
    if ci == "none":
        # No hosted checks are configured. A clean review on the current head is the
        # evidence; without it, request a review instead of declaring success.
        return "DONE" if verdict_clean else "review-changes"
    return "WAITING"


CHEAP_BELOW_FLOOR_STEPS = ("DONE", "PARKED", "park-blocker")


def should_stop_for_floor(step, remaining_minutes, floor, deterministic_pr=True):
    """Return whether the time floor stops this step.

    The floor prevents starting a long session. It does not block a cheap
    deterministic step that finishes an issue, such as marking a reviewed
    draft ready or recording an endpoint.
    """
    if remaining_minutes >= floor:
        return False
    if step in CHEAP_BELOW_FLOOR_STEPS:
        return False
    if step == "submit-pr" and deterministic_pr:
        return False
    return True


def phase_boundary_park(state, step, remaining_minutes, floor):
    """Describe the time park for a draft that the floor leaves unfinished.

    The floor ends a phase. When the issue has an open draft with committed
    work, the park names the PR and the remaining steps, so the next run can
    resume from the record instead of an In progress issue with no park.
    """
    pr = state.get("pr") or {}
    if not pr.get("url") or not (pr.get("is_draft") or pr.get("draft")):
        return None
    head = pr.get("head") or "unknown"
    return (
        f"The time budget floor ({floor} min; {remaining_minutes:.1f} min remained) stopped the run before `{step}`. "
        f"The pull request {pr['url']} is a draft with committed work at {head}. "
        f"Remaining steps: `{step}`, then `submit-pr`."
    )


def next_item(board, attempted=None, exclude=None):
    """Pure function selecting the next item from board state (Decision 9).

    ``exclude`` is an operator denylist of issue numbers. It applies to every
    tier — in-flight, parked, and Ready selection — because an operator who
    says "do not touch #1344" means it regardless of which column the issue
    currently sits in. Before this was threaded through, `--exclude` reached
    only the parent-issue path, so a board run silently ran excluded issues.
    """
    attempted = attempted or set()
    exclude = exclude or set()

    def denied(item):
        num = item.get("number")
        return num in exclude or item.get("issue") in exclude or item.get("url") in exclude

    in_flight = board.get("in_flight") or []
    for item in in_flight:
        num = item.get("number")
        if num in attempted or item.get("issue") in attempted or item.get("url") in attempted:
            continue
        if denied(item):
            continue
        if "triage:needs-input" in (item.get("labels") or []):
            continue
        step = item.get("step")
        if step not in ("DONE", "PARKED", "WAITING"):
            return item

    parked = board.get("parked") or []
    for item in parked:
        num = item.get("number")
        if num in attempted or item.get("issue") in attempted or item.get("url") in attempted:
            continue
        if denied(item):
            continue
        if item.get("park_kind") in ("question", "blocker"):
            continue
        return item

    selection = board.get("selection") or []
    for item in selection:
        num = item.get("number")
        if num in attempted or item.get("issue") in attempted or item.get("url") in attempted:
            continue
        if denied(item):
            continue
        if "triage:needs-input" in (item.get("labels") or []):
            continue
        return item
    return None


def observe_issue(issue_ref, cli_fn=run_cli, cwd=None):
    """Query live GitHub facts and pr-state for an issue."""
    facts, _ = cli_fn("facts", "--issue", str(issue_ref), cwd=cwd)
    issue = facts.get("issue") or {}
    prs = issue.get("prs") or []
    pr = prs[0] if prs else None
    state = {
        "issue": issue.get("url") or str(issue_ref),
        "url": issue.get("url") or str(issue_ref),
        "number": issue_ref if isinstance(issue_ref, int) else (issue.get("number")),
        "title": issue.get("title"),
        "body": issue.get("body") or "",
        "repo": (facts.get("repository") or {}).get("remote"),
        "labels": issue.get("labels") or [],
        "blocked_by": issue.get("blocked_by") or [],
        "blocking": issue.get("blocking") or [],
        "pr": pr,
        "ci": None,
        "review_verdicts": [],
        "pending_review_requests": [],
        "unresolved_threads": False,
    }
    if pr and pr.get("number"):
        repo = facts.get("repository", {}).get("remote")
        pr_st, _ = cli_fn("pr-state", str(pr["number"]), *([f"--repo={repo}"] if repo else []), cwd=cwd)
        state["ci"] = pr_st.get("ci")
        state["pr"] = {
            "number": pr["number"],
            "url": pr.get("url"),
            "head": pr_st.get("head") or pr.get("head"),
            "head_branch": pr_st.get("head_branch") or pr.get("head_branch"),
            "base": pr_st.get("base") or pr.get("base"),
            "is_draft": pr_st.get("is_draft", pr.get("is_draft", False)),
            "state": pr_st.get("state") or pr.get("state", "OPEN"),
            "mergeable": pr_st.get("mergeable"),
        }
        state["reviews"] = pr_st.get("reviews") or []
        state["review_summary"] = pr_st.get("review_summary") or {}
        state["comments"] = pr_st.get("comments") or []
        state["review_verdicts"] = pr_st.get("review_verdicts") or []
        state["pending_review_requests"] = pr_st.get("pending_review_requests") or []
    return state


def parked_pr_url(state, published=None, cli_fn=run_cli, cwd=None):
    """Return the linked PR URL, using the published result before a re-read."""
    for candidate in (state.get("pr"), published):
        if isinstance(candidate, dict) and candidate.get("url"):
            return candidate["url"]
    ref = state.get("issue") or state.get("url")
    if not ref:
        return ""
    refreshed = observe_issue(ref, cli_fn=cli_fn, cwd=cwd)
    return ((refreshed.get("pr") or {}).get("url")) or ""


def observe_board(owner, project, cli_fn=run_cli, cwd=None, attempted=None):
    """Read the whole board and categorize in-flight, parked, and ready items."""
    attempted = attempted or set()
    q_sel, _ = cli_fn("queue", "select", "--owner", owner, "--project", str(project), cwd=cwd)
    in_flight = []
    # Check In progress and In review columns
    for col in ("In progress", "In review"):
        col_data, _ = cli_fn("queue", "select", "--owner", owner, "--project", str(project), f"--status={col}", cwd=cwd)
        for it in col_data.get("selection") or []:
            st = observe_issue(it.get("url") or it.get("number"), cli_fn=cli_fn, cwd=cwd)
            st["step"] = next_step(st)
            in_flight.append(st)
    return {
        "in_flight": in_flight,
        "parked": q_sel.get("parked") or [],
        "selection": q_sel.get("selection") or [],
    }


def parse_issue_ref(issue_ref):
    """Normalize issue ref for gh CLI commands."""
    s = str(issue_ref).strip()
    if s.startswith("http://") or s.startswith("https://"):
        return [s]
    if "#" in s:
        repo, num = s.split("#", 1)
        return [num, "--repo", repo] if repo else [num]
    return [s]


def observe_parent(parent_ref, gh_cmd="gh", cwd=None):
    """Query parent issue and its native sub-issues via gh issue view."""
    cmd = [gh_cmd, "issue", "view", *parse_issue_ref(parent_ref),
           "--json", "number,title,state,url,subIssues,subIssuesSummary"]
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"Failed to query parent issue {parent_ref}: {proc.stderr.strip()}")
    data = json.loads(proc.stdout)
    nodes = (data.get("subIssues") or {}).get("nodes") or []
    return {
        "parent": {
            "number": data.get("number"),
            "title": data.get("title"),
            "state": data.get("state"),
            "url": data.get("url"),
            "summary": data.get("subIssuesSummary") or {},
        },
        "children": nodes,
    }


def next_item_for_parent(children, attempted=None, cli_fn=run_cli, cwd=None, exclude=None,
                         require_labels=None, exclude_labels=None, board_index=None):
    """Select the next child, honoring board order, labels, and native blocked-by links."""
    attempted = attempted or set()
    exclude = exclude or set()
    require_labels = [label for label in (require_labels or []) if label]
    exclude_labels = [label for label in (exclude_labels or []) if label]
    candidates = []
    for child in children:
        if child.get("state") == "CLOSED" or child.get("number") in exclude:
            continue
        ref = child.get("url") or child.get("number")
        if ref in attempted or child.get("number") in attempted:
            continue
        st = observe_issue(ref, cli_fn=cli_fn, cwd=cwd)
        labels = st.get("labels") or []
        if "triage:needs-input" in labels or "triage:needs-definition" in labels:
            continue
        if require_labels and not all(label in labels for label in require_labels):
            continue
        if exclude_labels and any(label in labels for label in exclude_labels):
            continue
        blockers = [blocker for blocker in st.get("blocked_by") or []
                    if blocker.get("state") == "OPEN"]
        if len(blockers) > 1:
            continue
        if len(blockers) == 1 and not find_base_pr(ref, children, cli_fn=cli_fn, cwd=cwd, child_state=st):
            continue
        step = next_step(st)
        if step in ("DONE", "PARKED", "WAITING"):
            continue
        candidates.append({**child, "_state": st, "_step": step,
                           "_rank": board_rank(child.get("number"), board_index)})
    candidates.sort(key=lambda entry: entry["_rank"])
    for entry in candidates:
        if entry["_state"].get("pr"):
            return {key: value for key, value in entry.items() if not key.startswith("_")}
    for entry in candidates:
        return {key: value for key, value in entry.items() if not key.startswith("_")}
    return None


def find_base_pr(child_ref, children, cli_fn=run_cli, cwd=None, child_state=None):
    """Find the open PR of the child's one open native blocker.

    The native blocked-by link is the only stack source. A child with no blocker,
    more than one open blocker, or a blocker without an open PR has no base.
    """
    if not children:
        return None
    state = child_state or observe_issue(child_ref, cli_fn=cli_fn, cwd=cwd)
    blockers = [blocker for blocker in state.get("blocked_by") or []
                if blocker.get("state") == "OPEN"]
    if len(blockers) != 1:
        return None
    number = blockers[0].get("number")
    if number is None:
        return None
    child = next((candidate for candidate in children if candidate.get("number") == number), None)
    if child is None or child.get("state") == "CLOSED":
        return None
    st = observe_issue(child.get("url") or child.get("number"), cli_fn=cli_fn, cwd=cwd)
    pr = st.get("pr") or {}
    if pr.get("head_branch") and pr.get("state") == "OPEN":
        return {"number": number, "pr": pr.get("number"), "branch": pr.get("head_branch"),
                "url": pr.get("url")}
    return None


def set_board_status(issue_ref, status, owner=None, project=None, cli_fn=run_cli, cwd=None):
    """Move an issue to a status on the project board, ignoring errors if unconfigured."""
    if not owner or not project:
        return
    try:
        cli_fn("board", "set-status", str(issue_ref), "--owner", owner, "--project", str(project),
               "--status", status, cwd=cwd)
    except Exception:
        pass

def compose_prompt(skill_dir, handoff_prompt, step=None):
    """Compose the session prompt.

    When a specific worker step is given (e.g. implement-issue, review-changes),
    generates a focused, minimal worker directive, omitting the 21-operation table
    and high-level coordinator rules. Falls back to SKILL.md body if step is None.
    """
    if step:
        role_map = {
            "implement-issue": ("ghflow-build-slim", "skills/build-slim/SKILL.md"),
            "address-pr-review": ("ghflow-build-slim", "skills/build-slim/SKILL.md"),
            "repair-conflict": ("ghflow-build-slim", "skills/build-slim/SKILL.md"),
            "review-changes": ("ghflow-review-slim", "skills/review-slim/SKILL.md"),
            # The facts refresh has no slim role; inline its task procedure so the
            # session does not have to read a reference file.
            "prepare-project-facts": ("ghflow:prepare-project-facts",
                                      "references/tasks/prepare-project-facts.md"),
        }
        role_name, role_skill = role_map.get(step, (f"ghflow:{step}", "SKILL.md"))
        cli_py = Path(skill_dir) / "cli" / "ghflow.py"
        task_ref = Path(skill_dir) / "references" / "tasks" / f"{step}.md"
        slim_file = Path(skill_dir) / role_skill

        inlined_rules = ""
        if slim_file.is_file():
            content = slim_file.read_text(encoding="utf-8")
            lines = content.splitlines()
            if lines and lines[0].strip() == "---":
                end_idx = 1
                while end_idx < len(lines) and lines[end_idx].strip() != "---":
                    end_idx += 1
                lines = lines[end_idx + 1:]
            inlined_rules = "\n".join(lines).strip().replace("ABSOLUTE_SKILL_DIRECTORY", str(skill_dir))

        task_line = (
            f"Task reference: `{task_ref}`. Operative rules are inlined above.\n"
            "Do not spend tool turns reading external reference files; proceed directly to your task."
            if task_ref.is_file() else ""
        )
        body = inlined_rules or (
            f"# {role_name}: {step}\n\n"
            f"You are executing the `{step}` operation for an assigned issue in an isolated worktree.\n"
            "Execution mode: Local-model single session. Stay in this session; do not spawn subagents.\n\n"
            "Tools:\n"
            f'GHFLOW_CLI is set in the environment; if it is unset, export GHFLOW_CLI="{cli_py}".\n'
            'python3 "$GHFLOW_CLI" --help\n\n'
            "Code exploration:\n"
            'Use `python3 "$GHFLOW_CLI" tags brief <symbol>...` for compact definitions and file outlines, `tags find <symbol> --refs` for references, and `tags outline <file>` for file structure.'
        )
        return (
            f"{body}\n\n"
            f"{task_line}\n\n"
            f"Base directory for this skill: {skill_dir}\n\n"
            f"{handoff_prompt}"
        )

    skill_md = Path(skill_dir) / "SKILL.md"
    body = skill_md.read_text(encoding="utf-8") if skill_md.is_file() else ""
    lines = body.splitlines()
    if lines and lines[0].strip() == "---":
        end_idx = 1
        while end_idx < len(lines) and lines[end_idx].strip() != "---":
            end_idx += 1
        lines = lines[end_idx + 1:]
    clean_body = "\n".join(lines).strip()
    return f"{clean_body}\n\nBase directory for this skill: {skill_dir}\n\n{handoff_prompt}"


def primary_checkout_change(before, after):
    """Return the status change when a session changed the primary checkout.

    OpenCode's shell can start in the project checkout instead of the task
    worktree. Warn when a session leaves changes there, because those changes
    belong to no task branch.
    """
    if before is None or after is None or before == after:
        return None
    return {"before": before, "after": after}


def recent_session_actions(log_path, limit=5):
    """Return short summaries of the last tool calls in a session log."""
    if not log_path:
        return []
    actions = []
    try:
        with open(log_path, encoding="utf-8", errors="replace") as log_file:
            for line in log_file:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                part = event.get("part") or {}
                if not (event.get("type") in ("tool", "tool_use") or part.get("type") == "tool"):
                    continue
                name = part.get("name") or part.get("tool") or "tool"
                tool_input = (part.get("state") or {}).get("input") or {}
                detail = tool_input.get("command") or tool_input.get("filePath") or tool_input.get("path") or ""
                actions.append(f"{name}: {str(detail)[:120]}")
    except OSError:
        return []
    return actions[-limit:]


def retry_directive(extra_text, actions, step=None):
    """Append the prior attempt's last actions to a retry directive."""
    if not actions:
        return extra_text
    lines = ["", "", "The previous attempt ended without a change. Its last actions:"]
    lines += [f"- {action}" for action in actions]
    if step in ("implement-issue", "address-pr-review"):
        lines.append("Start by making the first edit; do not repeat this investigation.")
    else:
        lines.append("Continue the assigned task from these actions; do not repeat the investigation.")
    return (extra_text or "") + "\n".join(lines)


def slow_step_warning(now, last_event_ts, step_idle_timeout, warned):
    """Describe a step that has waited too long for its first event."""
    if warned or now - last_event_ts <= SLOW_STEP_WARN_SECONDS:
        return None
    return (f"No session events for {int(now - last_event_ts)}s; "
            f"waiting up to {step_idle_timeout}s")


def context_warning(context_tokens, warn_tokens, warned, tokens=None):
    """Describe a session that reached the context warning threshold."""
    if warned or not warn_tokens or context_tokens < warn_tokens:
        return None
    detail = context_breakdown(tokens) if tokens else ""
    return (f"Session context reached {context_tokens} tokens (warn {warn_tokens}){detail}.")


def context_breakdown(tokens):
    """Render the input/cache split behind a context figure.

    The warning used to report a single number, and that number is the sum of
    uncached input plus cache reads plus cache writes (see
    ``step_context_tokens``). Without the split an operator cannot tell a
    genuinely large prompt from an accounting artifact, so a threshold that
    fires is not actionable.
    """
    tokens = tokens or {}
    cache = tokens.get("cache") or {}
    parts = [
        f"input={int(tokens.get('input') or 0)}",
        f"cache_read={int(cache.get('read') or 0)}",
        f"cache_write={int(cache.get('write') or 0)}",
    ]
    return " [" + ", ".join(parts) + "]"


def context_cap_reason(context_tokens, max_tokens):
    """Describe a session that reached the context cap, or None."""
    if not max_tokens or context_tokens < max_tokens:
        return None
    return f"Session context reached {context_tokens} tokens (cap {max_tokens})"


def step_context_tokens(tokens):
    """Return a step's context size, including cached prompt tokens."""
    tokens = tokens or {}
    cache = tokens.get("cache") or {}
    return (int(tokens.get("input") or 0)
            + int(cache.get("read") or 0)
            + int(cache.get("write") or 0))


SESSION_TRAILER_KEY = "Ghflow-Session"
SESSION_HOOK = "prepare-commit-msg"
SESSION_HOOK_SCRIPT = """#!/bin/sh
# Add the ghflow session trailer and keep the repository's own hooks.
original="${GHFLOW_ORIGINAL_HOOKS_PATH:-}"
if [ -n "$original" ] && [ -x "$original/prepare-commit-msg" ]; then
    "$original/prepare-commit-msg" "$@" || exit $?
fi
[ -n "${GHFLOW_SESSION:-}" ] || exit 0
git interpret-trailers --in-place --no-divider --if-exists addIfDifferent \\
    --trailer "Ghflow-Session: ${GHFLOW_SESSION}" "$1" || true
exit 0
"""


def session_reference(notes_dir, session_log):
    """Return the trailer value for a session log, relative to the notes root."""
    notes_dir = Path(notes_dir)
    session_log = Path(session_log)
    try:
        relative = session_log.relative_to(notes_dir.parent)
    except ValueError:
        relative = Path(session_log.name)
    return str(relative.with_suffix(""))


def original_hooks_path(session_cwd):
    """Return the repository's hook directory before the session override."""
    if not session_cwd or not Path(session_cwd).is_dir():
        return None
    configured = git_output(["config", "--get", "core.hooksPath"], cwd=session_cwd)
    if configured:
        path = Path(configured).expanduser()
        if not path.is_absolute():
            root = git_output(["rev-parse", "--show-toplevel"], cwd=session_cwd)
            if root:
                path = Path(root) / path
        return str(path)
    common = git_output(["rev-parse", "--path-format=absolute", "--git-common-dir"], cwd=session_cwd)
    if common:
        return str(Path(common) / "hooks")
    return None


def write_session_hooks(notes_dir, original_hooks=None):
    """Create the hook directory and preserve every other repository hook."""
    hooks_dir = Path(notes_dir) / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    original = Path(original_hooks) if original_hooks else None
    if original and original.is_dir() and original.resolve() != hooks_dir.resolve():
        for entry in original.iterdir():
            if (entry.name == SESSION_HOOK or not entry.is_file()
                    or not os.access(entry, os.X_OK)):
                continue
            target = hooks_dir / entry.name
            if target.exists():
                continue
            target.write_text(f"#!/bin/sh\nexec {shlex.quote(str(entry))} \"$@\"\n",
                              encoding="utf-8")
            target.chmod(0o755)
    hook = hooks_dir / SESSION_HOOK
    hook.write_text(SESSION_HOOK_SCRIPT, encoding="utf-8")
    hook.chmod(0o755)
    return hooks_dir


def session_git_environment(notes_dir, session_log, session_cwd):
    """Build the git environment that adds the session trailer to session commits."""
    env = {"GHFLOW_SESSION": session_reference(notes_dir, session_log)}
    original = original_hooks_path(session_cwd)
    if not original:
        return env
    hooks_dir = write_session_hooks(notes_dir, original)
    env.update({
        "GHFLOW_ORIGINAL_HOOKS_PATH": original,
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.hooksPath",
        "GIT_CONFIG_VALUE_0": str(hooks_dir),
    })
    return env


def run_session(step, issue_url, notes_dir, options, cli_fn=run_cli, log_hook=None):
    """Create a handoff and execute one OpenCode session.

    ``log_hook`` receives the session log path before the session is deleted, so a
    caller can summarize it without guessing the name.
    """
    stamp = time.strftime("%Y%m%d-%H%M%S")
    handoff_file = notes_dir / f"handoff-{step}-{stamp}.md"
    args = ["handoff", step, *([issue_url] if issue_url else []), "--out", str(handoff_file), "--runner"]
    if step == "review-changes":
        args.append("--verdict")
    if options.get("facts_path"):
        args += ["--facts-path", str(options["facts_path"])]
    if options.get("model"):
        args += ["--review-plan", f"model {options['model']}"]
    if options.get("deadline"):
        args += ["--deadline", str(options["deadline"])]
    if options.get("branch"):
        args += ["--branch", options["branch"]]
    if options.get("extra_text"):
        extra_file = notes_dir / f"directive-{step}-{stamp}.md"
        extra_file.write_text(options["extra_text"], encoding="utf-8")
        args += ["--extra", str(extra_file)]
    h_out, code = cli_fn(*args, cwd=options.get("cwd"))
    if code != 0:
        return False, f"Handoff creation failed: {h_out}"

    session_monitor = options.get("monitor")
    if session_monitor is not None:
        session_monitor.handoff_model(step, handoff_file, options.get("model"))

    prompt_text = compose_prompt(options["skill_dir"], h_out.get("dispatch_prompt", ""), step=step)
    worker_cmd = resolve_worker_cmd(options)
    cmd = [worker_cmd, "run", "--auto", "--format", "json",
           "--title", f"Queue runner {step} {stamp}"]
    if options.get("model"):
        cmd += ["--model", options["model"]]
    if options.get("standalone"):
        cmd += worker_run_flags(worker_cmd)
    cmd.append(prompt_text)
    if shutil.which("caffeinate") and sys.platform == "darwin":
        cmd = ["caffeinate", "-i", *cmd]

    env = dict(os.environ, OPENCODE_DISABLE_AUTOUPDATE="1")
    if options.get("skill_dir"):
        env["GHFLOW_CLI"] = str((Path(options["skill_dir"]) / "cli" / "ghflow.py").resolve())
    session_cwd = options.get("session_cwd") or options.get("cwd")
    primary_cwd = options.get("cwd")
    primary_before = None
    if primary_cwd and session_cwd and Path(session_cwd).resolve() != Path(primary_cwd).resolve():
        primary_before = git_output(["status", "--porcelain"], cwd=primary_cwd)
    session_log = notes_dir / f"session-{step}-{stamp}.log"
    env.update(session_git_environment(notes_dir, session_log, session_cwd))
    print(f"[{time.strftime('%X')}] Logging session output to {session_log}")
    if options.get("session_cwd"):
        print(f"[{time.strftime('%X')}] Session cwd: {options['session_cwd']}", flush=True)
    if options.get("standalone"):
        major = worker_major(worker_cmd)
        print(f"[{time.strftime('%X')}] Worker {worker_cmd} is OpenCode {major}.x; "
              f"{'passing --standalone' if major >= 2 else 'no --standalone (2.x only)'}", flush=True)
    log_fp = open(session_log, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, cwd=session_cwd, env=env, bufsize=1)
    session_id = None
    step_num = 0
    max_turns = options.get("max_turns") or DEFAULT_MAX_TURNS
    timeout_sec = options.get("session_timeout", DEFAULT_SESSION_TIMEOUT)
    step_idle_timeout = options.get("step_idle_timeout", DEFAULT_STEP_IDLE_TIMEOUT)
    start_ts = time.time()
    last_event_ts = time.time()
    abort_reason = None
    slow_step_warned = False
    context_warn_tokens = options.get("context_warn_tokens", DEFAULT_CONTEXT_WARN_TOKENS)
    max_context_tokens = options.get("max_context_tokens", DEFAULT_MAX_CONTEXT_TOKENS)
    context_warned = False
    last_context_tokens = None
    monitor_interval = options.get("monitor_interval", monitor_mod.DEFAULT_INTERVAL_SECONDS)
    last_sample = start_ts

    def sample_session():
        if session_monitor is None:
            return
        session_monitor.session_sample(
            step=step, issue=issue_url, session_id=session_id,
            alive=proc.poll() is None,
            last_event_age=time.time() - last_event_ts,
            context_tokens=last_context_tokens,
            turns=step_num,
            age=time.time() - start_ts,
            limits={"step_idle_timeout": step_idle_timeout,
                    "session_timeout": timeout_sec,
                    "max_turns": max_turns,
                    "context_warn_tokens": context_warn_tokens,
                    "max_context_tokens": max_context_tokens})
        session_monitor.write()
        print(session_monitor.status_line(), flush=True)

    def process_line(line_str):
        nonlocal session_id, step_num, abort_reason, last_event_ts, slow_step_warned, context_warned, last_context_tokens
        last_event_ts = time.time()
        slow_step_warned = False
        log_fp.write(line_str)
        log_fp.flush()
        stripped = line_str.strip()
        if not stripped:
            return
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            return
        if not session_id and event.get("sessionID"):
            session_id = event["sessionID"]
            print(f"[{time.strftime('%X')}] Session ID: {session_id}", flush=True)
        ev_type = event.get("type")
        part = event.get("part") or {}
        if ev_type == "step_start":
            step_num += 1
            if step_num > max_turns:
                abort_reason = f"Session exceeded turn limit ({max_turns})"
        elif ev_type == "tool" or part.get("type") == "tool":
            tool_name = part.get("name") or part.get("tool") or event.get("name") or "tool"
            tool_in = (part.get("state") or {}).get("input") or {}
            cmd_summary = tool_in.get("command") or tool_in.get("filePath") or tool_in.get("path") or ""
            if cmd_summary:
                cmd_summary = f" {cmd_summary[:60]}"
            print(f"[{time.strftime('%X')}] [turn {step_num}] Tool: {tool_name}{cmd_summary}", flush=True)
        elif ev_type == "step_finish" or part.get("type") == "step-finish":
            tokens = part.get("tokens") or {}
            in_tok = tokens.get("input", 0)
            out_tok = tokens.get("output", 0)
            reason_tok = tokens.get("reasoning", 0)
            reason = part.get("reason") or event.get("reason")
            context_tokens = step_context_tokens(tokens)
            last_context_tokens = context_tokens
            print(f"[{time.strftime('%X')}] [turn {step_num}] Step finish (in: {in_tok}, out: {out_tok} tokens, "
                  f"context: {context_tokens})", flush=True)
            warning = context_warning(context_tokens, context_warn_tokens, context_warned, tokens)
            if warning:
                print(f"[{time.strftime('%X')}] Warning: {warning}", flush=True)
                log_fp.write(json.dumps({"type": "runner_warning", "reason": warning,
                                         "timestamp": int(time.time() * 1000)}) + "\n")
                log_fp.flush()
                context_warned = True
            cap_reason = context_cap_reason(context_tokens, max_context_tokens)
            if cap_reason:
                abort_reason = cap_reason
            if out_tok == 0 and (reason_tok >= MAX_DEGENERATE_REASONING or reason == "length"):
                abort_reason = f"Session stalled in reasoning loop ({reason_tok} reasoning tokens, 0 output)"
        elif ev_type == "error":
            err = event.get("error") or part.get("error") or {}
            if isinstance(err, dict) and err.get("type") == "output-limit":
                abort_reason = f"Session output limit exceeded: {err.get('message', 'output truncated')}"

    sample_session()
    try:
        has_fd = hasattr(proc.stdout, "fileno")
        if has_fd:
            while True:
                now = time.time()
                if now - last_sample >= monitor_interval:
                    last_sample = now
                    sample_session()
                if now - start_ts > timeout_sec:
                    abort_reason = f"Session exceeded timeout ({timeout_sec}s)"
                    break
                if now - last_event_ts > step_idle_timeout:
                    abort_reason = f"Session idle timeout ({step_idle_timeout}s without events)"
                    break
                message = slow_step_warning(now, last_event_ts, step_idle_timeout, slow_step_warned)
                if message:
                    print(f"[{time.strftime('%X')}] {message}", flush=True)
                    slow_step_warned = True
                if abort_reason:
                    break
                if proc.poll() is not None:
                    for line in proc.stdout:
                        process_line(line)
                        if abort_reason:
                            break
                    break
                rlist, _, _ = select.select([proc.stdout], [], [], 1.0)
                if not rlist:
                    continue
                line = proc.stdout.readline()
                if not line:
                    break
                process_line(line)
        else:
            for line in proc.stdout:
                if time.time() - start_ts > timeout_sec:
                    abort_reason = f"Session exceeded timeout ({timeout_sec}s)"
                    break
                process_line(line)
                if abort_reason:
                    break
            if not abort_reason and time.time() - start_ts > timeout_sec:
                abort_reason = f"Session exceeded timeout ({timeout_sec}s)"
        if abort_reason:
            print(f"[{time.strftime('%X')}] {abort_reason}. Terminating session...", flush=True)
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        else:
            proc.wait(timeout=10 if has_fd else timeout_sec)
    finally:
        if abort_reason:
            try:
                log_fp.write(json.dumps({"type": "runner_abort", "reason": abort_reason,
                                         "timestamp": int(time.time() * 1000)}) + "\n")
                log_fp.flush()
            except Exception:
                pass
        log_fp.close()

    if log_hook:
        try:
            log_hook(session_log)
        except Exception as error:
            print(f"[{time.strftime('%X')}] Session log hook failed: {error}", flush=True)

    if session_id:
        worker_cmd = resolve_worker_cmd(options)
        subprocess.run([worker_cmd, "session", "delete", session_id],
                       stdin=subprocess.DEVNULL, capture_output=True)
    if primary_before is not None:
        change = primary_checkout_change(primary_before,
                                         git_output(["status", "--porcelain"], cwd=primary_cwd))
        if change:
            print(f"[{time.strftime('%X')}] Warning: the primary checkout changed during the session. "
                  f"Work only in the task worktree.", flush=True)
    success = proc.returncode == 0 and not abort_reason
    if session_monitor is not None:
        session_monitor.session_end(step, success, abort_reason or "", session_id, session_log)
        session_monitor.write(force=True)
        print(session_monitor.status_line(), flush=True)
    if abort_reason:
        return False, abort_reason
    return success, session_id or ""


def prepare_worktree(issue_url, title, owner, project, options, cli_fn=run_cli, base_branch=None):
    """Create the task worktree from origin before the session starts.

    The worktree and branch are a runner decision, not a model choice, so the session
    cannot spend its budget surveying a stale checkout. ``base_branch`` starts a
    stacked child from the base PR branch. Exit 3 means the branch or path already
    exists, which is a resumption; reuse it.
    """
    number = str(issue_url).rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", str(title or "").lower()).strip("-")[:40].strip("-")
    branch = f"issue-{number}-{slug}" if slug else f"issue-{number}"
    args = ["worktree", "create", issue_url, "--branch", branch]
    if base_branch:
        args += ["--base", base_branch]
    if owner and project:
        args += ["--owner", owner, "--project", str(project)]
    out, code = cli_fn(*args, cwd=options.get("cwd"))
    path = (out or {}).get("path") if isinstance(out, dict) else None
    # A board write can fail on a token without the ``project`` scope while the
    # worktree itself was created and set up. That must not discard usable work:
    # without a worktree reference the runner cannot publish the session's
    # commits, and the issue parks as "no progress" (#272).
    errors = (out or {}).get("errors") if isinstance(out, dict) else None
    fatal = [e for e in (errors or []) if e.get("part") != "board"]
    if code == 2 and path and not fatal:
        print(f"[{time.strftime('%X')}] Worktree prepared at {path} with a non-fatal board error; "
              f"continuing without the board update", flush=True)
    elif code not in (0, 3) or not path:
        print(f"[{time.strftime('%X')}] Worktree preparation failed (exit {code}): {out}", flush=True)
        return None
    setup = (out or {}).get("worktree_setup") if isinstance(out, dict) else None
    print(f"[{time.strftime('%X')}] Worktree {'created' if code == 0 else 'reused'} at {path}", flush=True)
    if setup and setup.get("source") == "project_facts":
        print(f"[{time.strftime('%X')}] Applied the project facts worktree declaration "
              f"(copy: {', '.join(setup.get('copy') or []) or 'none'}; "
              f"setup: {', '.join(setup.get('setup') or []) or 'none'})", flush=True)
    return {"branch": branch, "path": path, "created": code == 0,
            "base": (out or {}).get("base") if isinstance(out, dict) else None, "setup": setup}


def git_output(args, cwd=None):
    """Run a read-only git command and return stripped stdout, or None on failure."""
    if cwd and not Path(cwd).is_dir():
        return None
    try:
        proc = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
        return proc.stdout.strip() if proc.returncode == 0 else None
    except OSError:
        return None

def prepare_conflict_merge(path, base, run=subprocess.run, git=git_output):
    """Fetch and merge the base into a PR worktree and report the conflicts.

    ``ok`` is true when git merged without conflicts. ``files`` names the
    unresolved paths. A merge that fails for another reason leaves ``files``
    empty so the caller can report it instead of starting a repair session.
    """
    if not path or not Path(path).is_dir():
        return {"ok": False, "reason": "The worktree is missing.", "files": []}
    fetch = run(["git", "fetch", "origin", base], cwd=path, capture_output=True, text=True)
    if fetch.returncode != 0:
        return {"ok": False, "reason": (fetch.stderr or fetch.stdout).strip(), "files": []}
    merge = run(["git", "merge", "--no-edit", f"origin/{base}"], cwd=path,
                capture_output=True, text=True)
    files = git(["diff", "--name-only", "--diff-filter=U"], cwd=path) or ""
    return {"ok": merge.returncode == 0,
            "reason": ((merge.stdout or "") + (merge.stderr or "")).strip(),
            "files": [line for line in files.splitlines() if line]}


def committed_count(path, base):
    """Count commits on the worktree branch since the base revision."""
    out = git_output(["rev-list", "--count", f"{base}..HEAD"], cwd=path)
    try:
        return int(out)
    except (TypeError, ValueError):
        return None


def stall_reason(worktree, step, base_branch=None):
    """Describe why a run stopped making progress, naming unpublished commits.

    A session that commits work which nothing publishes looks identical to a
    session that did nothing, because the loop only compares step, PR head, and
    verdict. Say which one happened instead of blaming the model (#272).
    """
    path = (worktree or {}).get("path")
    branch = (worktree or {}).get("branch")
    if path and branch:
        count_ref = base_branch or (worktree or {}).get("base") or "origin/main"
        count = committed_count(path, count_ref)
        if count:
            return (f"{count} commit(s) on `{branch}` are unpublished: no pull request exists, "
                    f"so the next step stayed `{step}`. Publish the branch or fix the runner's "
                    f"publish step.")
    return "No progress made in session."


def publish_committed(issue_url, title, worktree, repo, notes_dir, options, base_branch=None,
                      stack=None, session_ref=None, cli_fn=run_cli):
    """Push a session's committed work and open a draft PR when none exists.

    The session keeps the content and commit role. This closes the gap that the
    epic #1434 trial showed: a session that commits and stops leaves the delivery
    invisible. ``pr create`` refuses an existing open PR, so a session that
    published its own PR keeps that PR instead of a duplicate. A commit this
    function makes carries the session trailer when ``session_ref`` is given.
    """
    if not worktree or not worktree.get("path"):
        return None
    if not repo:
        print(f"[{time.strftime('%X')}] Cannot publish: the issue's repository is unknown", flush=True)
        return None
    path, branch = worktree["path"], worktree["branch"]
    generated = (worktree.get("setup") or {}).get("generated") or []
    base_ref = worktree.get("base") or "origin/main"
    count_ref = base_ref
    if base_branch:
        for candidate in (base_branch, f"origin/{base_branch}"):
            if git_output(["rev-parse", "--verify", "--quiet", candidate], cwd=path):
                count_ref = candidate
                break
    count = committed_count(path, count_ref)
    if not count:
        status = git_output(["status", "--porcelain"], cwd=path)
        if status:
            print(f"[{time.strftime('%X')}] Committing uncommitted worktree changes for {branch}", flush=True)
            cli_fn("exec", "--", "git", "-C", path, "add", "-A", cwd=options.get("cwd"))
            for pattern in generated:
                cli_fn("exec", "--", "git", "-C", path, "reset", "--", pattern, cwd=options.get("cwd"))
            if generated:
                print(f"[{time.strftime('%X')}] Excluded generated paths from the commit: {', '.join(generated)}", flush=True)
            number = str(issue_url).rstrip("/").split("/")[-1].split("#")[-1]
            commit_msg = f"refactor: {title or branch} (Closes #{number})"
            commit_args = ["git", "-C", path, "commit", "-m", commit_msg]
            if session_ref:
                commit_args += ["--trailer", f"{SESSION_TRAILER_KEY}: {session_ref}"]
            cli_fn("exec", "--", *commit_args, cwd=options.get("cwd"))
            count = committed_count(path, count_ref)
    if not count:
        return None
    if generated:
        for pattern in generated:
            output, code = cli_fn("exec", "--", "git", "-C", path, "restore",
                                  "--source=HEAD", "--staged", "--worktree", "--", pattern,
                                  cwd=options.get("cwd"))
            if code != 0:
                print(f"[{time.strftime('%X')}] Could not restore generated path {pattern}: {output}",
                      flush=True)
    print(f"[{time.strftime('%X')}] Publishing {count} committed change(s) from {branch}", flush=True)
    pushed, code = cli_fn("exec", "--", "git", "-C", path, "push", "-u", "origin", branch,
                          cwd=options.get("cwd"))
    if code != 0:
        print(f"[{time.strftime('%X')}] Push failed (exit {code}): {pushed}", flush=True)
        return None
    head = git_output(["rev-parse", "HEAD"], cwd=path)
    if not head:
        print(f"[{time.strftime('%X')}] Could not read the worktree head after the push", flush=True)
        return None
    number = str(issue_url).rstrip("/").split("/")[-1]
    subjects = git_output(["log", "--format=- `%h` %s", f"{count_ref}..HEAD"], cwd=path) or ""
    body_file = notes_dir / f"draft-pr-{number}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    stack_lines = []
    if base_branch and stack:
        stack_lines = ["## Stack", "",
                       f"Part of a stack on `{base_branch}` (PR #{stack.get('pr')}).", ""]
    body_file.write_text("\n".join([
        f"Draft checkpoint for {issue_url}.",
        "",
        "The queue runner published committed work that the implementation session left unpublished.",
        "",
        *stack_lines,
        "## Commits",
        "",
        subjects,
        "",
        f"Part of #{number}",
        "",
    ]), encoding="utf-8")
    base = base_branch or base_ref.removeprefix("origin/") or "main"
    if base_branch:
        remote_heads = git_output(["ls-remote", "--heads", "origin", base_branch], cwd=path)
        if not remote_heads:
            base = base_ref.removeprefix("origin/") or "main"
    out, code = cli_fn("pr", "create", "--repo", repo, "--head", branch, "--base", base,
                       "--title", title or branch, "--body-file", str(body_file), "--draft",
                       "--expect-head", head, cwd=options.get("cwd"))
    url = (out or {}).get("url") if isinstance(out, dict) else None
    if code == 0:
        if isinstance(out, dict):
            out["head"] = head
        print(f"[{time.strftime('%X')}] Opened draft PR {url} at {head[:7]}", flush=True)
        return out
    if code == 3:
        print(f"[{time.strftime('%X')}] An open PR already exists for {branch}; no duplicate created", flush=True)
        return None
    print(f"[{time.strftime('%X')}] Draft PR creation failed (exit {code}): {out}", flush=True)
    return None


def published_pr_state(published):
    """Build a PR view from a publish result when the issue link lags.

    ``facts --issue`` can trail ``pr create`` by a few seconds. Seeding this
    view keeps the reconciliation loop on the review step instead of parking a
    successful publish as no progress.
    """
    if not isinstance(published, dict) or not published.get("url"):
        return None
    return {
        "number": published.get("number"),
        "url": published.get("url"),
        "head": published.get("head"),
        "head_branch": published.get("head_branch"),
        "is_draft": True,
        "state": "OPEN",
    }


def stale_facts_warning(facts):
    """Return a warning when origin's project facts name stale sources."""
    project = (facts or {}).get("project_facts") or {}
    origin = project.get("origin") or {}
    stale = origin.get("stale_sources") or []
    if not stale:
        return None
    paths = ", ".join(source.get("path", "?") for source in stale)
    return (f"project facts are stale on origin for: {paths}. "
            f"Workers branch from origin and may read an outdated file.")


def prepare_facts_worktree(repo_root, default_branch, cli_fn=run_cli):
    """Create the refresh branch and worktree the runner hands to the facts session."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    branch = f"facts-refresh-{stamp}"
    path = Path(repo_root) / ".claude" / "worktrees" / branch
    out, code = cli_fn("exec", "--", "git", "worktree", "add", "-b", branch, str(path),
                       f"origin/{default_branch}", cwd=repo_root)
    if code != 0:
        print(f"[{time.strftime('%X')}] Facts refresh worktree failed (exit {code}): {out}", flush=True)
        return None
    print(f"[{time.strftime('%X')}] Facts refresh worktree at {path} on branch {branch}", flush=True)
    return {"branch": branch, "path": str(path)}


def find_open_pr(repo, branch, cwd, cli_fn=run_cli):
    """Return the open PR record for a branch, or None when the read finds none."""
    if not repo:
        return None
    out, code = cli_fn("exec", "--", "gh", "pr", "list", "--repo", repo, "--head", branch,
                       "--state", "open", "--json", "url,number,headRefOid,isDraft,baseRefName", cwd=cwd)
    if code == 0 and isinstance(out, list) and out:
        return out[0]
    return None


def dispatch_facts_refresh(facts_out, options, notes_dir, cli_fn=run_cli, session_fn=None):
    """Refresh origin's stale project facts before the first issue.

    Returns the refresh record and the refreshed file path. The record is
    always present when origin reports stale sources, so a failed dispatch
    stays visible in the run summary. The caller points later handoffs at the
    returned path only when the refresh is verified.
    """
    origin = (((facts_out or {}).get("project_facts") or {}).get("origin") or {})
    if origin.get("present") is False:
        # Writing the first facts file is a separate task the user requests.
        return None, None
    stale = origin.get("stale_sources") or []
    if not stale:
        return None, None
    stale_names = [source.get("path", "?") if isinstance(source, dict) else str(source)
                   for source in stale]
    repository = (facts_out or {}).get("repository") or {}
    checkout = (facts_out or {}).get("checkout") or {}
    root = checkout.get("primary_root") or checkout.get("root") or options.get("cwd")
    default_branch = repository.get("default_branch") or "main"
    record = {"status": "failed", "stale_sources": stale_names, "remaining_stale_sources": [],
              "reason": None, "pr": None, "branch": None, "path": None, "head": None}
    if not root:
        record["reason"] = "The subject checkout is unknown."
        return record, None

    worktree = prepare_facts_worktree(root, default_branch, cli_fn=cli_fn)
    if not worktree:
        record["reason"] = "The runner could not create the refresh worktree."
        return record, None
    record.update(branch=worktree["branch"], path=worktree["path"])

    refresh_options = dict(options)
    refresh_options["session_cwd"] = worktree["path"]
    refresh_options["branch"] = worktree["branch"]
    refresh_options["extra_text"] = (
        f"Work in the prepared worktree at {worktree['path']} on branch {worktree['branch']}, "
        f"created from origin/{default_branch}. Refresh `.ghflow/project.md` there, commit it, "
        "push the branch, and open a ready PR to the default branch. Do not create another "
        "worktree, do not request review, and do not merge. Return the PR URL and the refreshed file path."
    )
    session_fn = session_fn or run_session
    success, info = session_fn("prepare-project-facts", None, notes_dir, refresh_options, cli_fn=cli_fn)
    if not success:
        record["reason"] = f"The refresh session failed: {info}."
        return record, None

    refreshed = Path(worktree["path"]) / ".ghflow" / "project.md"
    if not refreshed.is_file():
        record["reason"] = "The refresh session wrote no .ghflow/project.md."
        return record, None
    changed = git_output(["diff", "--name-only", f"origin/{default_branch}...HEAD"],
                         cwd=worktree["path"])
    files = sorted(line.strip() for line in (changed or "").splitlines() if line.strip())
    if files != [".ghflow/project.md"]:
        record["reason"] = ("The refresh branch changes "
                            f"{', '.join(files) or 'no files'}; only .ghflow/project.md is allowed.")
        return record, None
    verified, code = cli_fn("facts", cwd=worktree["path"])
    local = ((verified or {}).get("project_facts") or {}) if isinstance(verified, dict) else {}
    remaining = local.get("stale_sources") or []
    record["remaining_stale_sources"] = [source.get("path", "?") if isinstance(source, dict) else str(source)
                                        for source in remaining]
    if code != 0 or not local.get("present") or remaining:
        record["reason"] = "The refreshed copy still reports stale or missing sources."
        return record, None
    if not git_output(["ls-remote", "--heads", "origin", worktree["branch"]], cwd=worktree["path"]):
        record["reason"] = "The refresh branch was not pushed."
        return record, None
    head = git_output(["rev-parse", "HEAD"], cwd=worktree["path"])
    pr = None
    for attempt in range(3):
        pr = find_open_pr(repository.get("remote"), worktree["branch"], options.get("cwd"), cli_fn=cli_fn)
        if pr:
            break
        if attempt < 2:
            time.sleep(2)
    if not pr:
        record["reason"] = "The refresh branch is pushed but no open PR was found."
        return record, None
    if head and pr.get("headRefOid") not in (None, head):
        record["reason"] = "The refresh PR head does not match the refreshed branch head."
        return record, None
    if pr.get("baseRefName") not in (None, default_branch):
        record["reason"] = f"The refresh PR targets {pr.get('baseRefName')}, not {default_branch}."
        return record, None
    record.update(status="refreshed", pr=pr.get("url"), head=head, pr_draft=pr.get("isDraft"))
    return record, str(refreshed)


def restore_generated_paths(wt_path, paths):
    """Restore tracked files that a gate regenerated in a worktree.

    ``paths`` are repo-relative paths from the project facts. A failed restore
    is not fatal; the worker's own restore instruction still applies.
    """
    if not wt_path or not paths:
        return []
    restored = []
    for rel in paths:
        try:
            proc = subprocess.run(
                ["git", "restore", "--", rel],
                cwd=wt_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, timeout=30,
            )
            if proc.returncode == 0:
                restored.append(rel)
        except Exception:
            continue
    if restored:
        print(f"[{time.strftime('%X')}] Restored gate-generated path(s): {', '.join(restored)}", flush=True)
    return restored


def run_precomputed_gate(wt_path, timeout=300, generated_paths=None):
    """Run local project test gates deterministically before a review-changes session."""
    if not wt_path or not Path(wt_path).is_dir():
        return None
    makefile = Path(wt_path) / "Makefile"
    if not makefile.is_file():
        return None
    try:
        content = makefile.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return None
    if not re.search(r"^check\s*:", content, re.MULTILINE):
        return None

    print(f"[{time.strftime('%X')}] Running pre-computed test gate (make check) in {wt_path}...", flush=True)
    try:
        proc = subprocess.run(["make", "check"], cwd=wt_path, stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, text=True, timeout=timeout)
        restore_generated_paths(wt_path, generated_paths)
        output = proc.stdout or ""
        test_match = re.search(r"(\d+\s+passed(?:,\s+\d+\s+skipped)?)", output)
        test_info = f", {test_match.group(1)}" if test_match else ""
        if proc.returncode == 0:
            print(f"[{time.strftime('%X')}] Pre-computed gate passed: make check exit 0{test_info}", flush=True)
            return {
                "success": True,
                "command": "make check",
                "exit_code": 0,
                "summary": f"make check passed (exit 0{test_info})",
                "text": f"Pre-computed gate status at head: `make check` passed (exit 0{test_info}). "
                        "Local gates are verified; do not spend turns re-running full test suites unless investigating a specific defect."
            }
        else:
            tail = "\n".join(output.strip().splitlines()[-5:])
            print(f"[{time.strftime('%X')}] Pre-computed gate failed: exit {proc.returncode}", flush=True)
            return {
                "success": False,
                "command": "make check",
                "exit_code": proc.returncode,
                "summary": f"make check failed (exit {proc.returncode})",
                "text": f"Pre-computed gate status at head: `make check` FAILED (exit {proc.returncode}):\n{tail}\n"
                        "Focus review on investigating this failure."
            }
    except subprocess.TimeoutExpired:
        print(f"[{time.strftime('%X')}] Pre-computed gate timed out after {timeout}s", flush=True)
        restore_generated_paths(wt_path, generated_paths)
        return {
            "success": False,
            "command": "make check",
            "exit_code": -1,
            "summary": f"make check timed out after {timeout}s",
            "text": f"Pre-computed gate timed out after {timeout}s. Verify test gates manually."
        }
    except Exception as e:
        print(f"[{time.strftime('%X')}] Pre-computed gate error: {e}", flush=True)
        restore_generated_paths(wt_path, generated_paths)
        return None


EXCLUDE_SYMBOL_KEYWORDS = {
    "python", "javascript", "typescript", "test", "tests", "pytest", "vitest",
    "true", "false", "none", "null", "self", "return", "import", "export",
    "class", "function", "method", "issue", "pull", "request", "branch",
    "commit", "worktree", "repo", "make", "check", "file", "files", "code",
    "line", "lines", "error", "errors", "fail", "fails", "failed", "pass",
    "passes", "passed", "todo", "fix", "args", "kwargs", "main", "base",
    "head", "diff", "spec", "plan", "notes", "type", "types", "data",
}

CODE_SUFFIXES = (
    ".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx",
    ".go", ".rs", ".java", ".c", ".h", ".cpp", ".hpp", ".sh", ".rb",
)
GENERATED_OR_DOC_PATHS = ("docs/", ".ghflow/", "node_modules/", "tui/node_modules/")
_SYMBOL_SOURCE_WARNED = False


def refresh_tags(cwd=None):
    """Refresh the ctags index for the subject checkout when it is missing or stale."""
    if not cwd or not Path(cwd).is_dir():
        return None
    try:
        from cli import tags as tags_mod
    except ImportError:
        print(f"[{time.strftime('%X')}] Symbol index: ctags module unavailable; using git grep", flush=True)
        return None
    tags_file = tags_mod.locate_tags_file(repo_root=cwd)
    head = git_output(["rev-parse", "HEAD"], cwd=cwd)
    stale = tags_file is None or not tags_file.is_file()
    if not stale:
        try:
            head_time = int(git_output(["log", "-1", "--format=%ct", head], cwd=cwd) or 0)
            stale = tags_file.stat().st_mtime < head_time or (time.time() - tags_file.stat().st_mtime > 3600)
        except (OSError, TypeError, ValueError):
            stale = True
    if not stale:
        return {"tags_file": str(tags_file), "refreshed": False}
    result, code = tags_mod.generate_tags(repo_root=cwd)
    if code == 0:
        print(f"[{time.strftime('%X')}] Symbol index: refreshed {result.get('symbols_indexed')} symbols "
              f"from {result.get('files_indexed')} files with {result.get('generator')}", flush=True)
        return result
    print(f"[{time.strftime('%X')}] Symbol index: ctags refresh failed; using git grep: {result}", flush=True)
    return result


def _is_code_path(path):
    """Return whether a repository path is a source file rather than docs or generated data."""
    if path.startswith(GENERATED_OR_DOC_PATHS) or path.endswith((".md", ".json", ".yaml", ".yml", ".lock")):
        return False
    return path.endswith(CODE_SUFFIXES)



def extract_candidate_symbols(title, body=""):
    """Extract backticked identifiers and distinct symbol names from issue text."""
    candidates = []
    seen = set()
    text = f"{title or ''}\n{body or ''}"

    # 1. Backticked tokens: `foo`, `#bar`, `_baz`
    for m in re.finditer(r"`([^`\n]+)`", text):
        raw = m.group(1).strip()
        clean = re.sub(r"\(\s*\)$", "", raw).strip()
        clean_id = clean.lstrip("#")
        if re.match(r"^[a-zA-Z_][a-zA-Z0-9_]{2,}$", clean_id):
            lower = clean_id.lower()
            if lower not in EXCLUDE_SYMBOL_KEYWORDS and lower not in seen:
                seen.add(lower)
                candidates.append(clean_id)

    # 2. Distinctive identifiers matching _*[a-zA-Z0-9_]+ in title
    for m in re.finditer(r"\b(_+[a-zA-Z0-9_]{2,}|[a-z]+[A-Z][a-zA-Z0-9_]+|[A-Z][a-z0-9]+[A-Z][a-zA-Z0-9]+)\b", title or ""):
        sym = m.group(1).strip()
        lower = sym.lower()
        if lower not in EXCLUDE_SYMBOL_KEYWORDS and lower not in seen:
            seen.add(lower)
            candidates.append(sym)

    return candidates[:5]


def find_subsystem_symbols(symbols, cwd=None, limit_per_symbol=3):
    """Find definition locations for symbols using ctags, with a code-only git grep fallback."""
    if not symbols or not cwd or not Path(cwd).is_dir():
        return []

    global _SYMBOL_SOURCE_WARNED
    tags_mod = None
    try:
        from cli import tags as tags_mod
    except ImportError:
        try:
            import tags as tags_mod
        except ImportError:
            pass
    if tags_mod is None and not _SYMBOL_SOURCE_WARNED:
        print(f"[{time.strftime('%X')}] Symbol index: ctags module unavailable; using git grep", flush=True)
        _SYMBOL_SOURCE_WARNED = True

    results = []
    for sym in symbols:
        clean_sym = sym.lstrip("#")
        matches = []
        source = "ctags"
        # 1. Try tags lookup first (exact definitions)
        if tags_mod:
            try:
                tag_res, code = tags_mod.find_tags(clean_sym, repo_root=cwd, exact=True)
                if code == 0 and tag_res.get("matches"):
                    for m in tag_res["matches"][:limit_per_symbol]:
                        line = m.get("line") or 1
                        loc = f"{m['path']}:{line}"
                        kind = f"[{m['kind']}] " if m.get("kind") else ""
                        scope = f"[{m['scope']}] " if m.get("scope") else ""
                        snip = m.get("pattern") or f"{kind}{scope}{m.get('name')}"
                        if snip.startswith("/^") and snip.endswith("$/"):
                            snip = snip[2:-2]
                        matches.append((loc, snip))
            except Exception:
                pass

        # 2. Fall back to git grep if no tag matches were found
        if not matches:
            source = "grep"
            try:
                proc = subprocess.run(
                    ["git", "grep", "-n", "-I", "-m", str(limit_per_symbol), "--", clean_sym],
                    cwd=cwd, capture_output=True, text=True, timeout=10
                )
                if proc.returncode == 0 and proc.stdout.strip():
                    lines = proc.stdout.strip().splitlines()
                    code_lines = [ln for ln in lines if _is_code_path(ln.split(":", 1)[0])]
                    for match_line in code_lines[:limit_per_symbol]:
                        parts = match_line.split(":", 2)
                        if len(parts) >= 2:
                            loc = f"{parts[0]}:{parts[1]}"
                            code_snip = parts[2].strip() if len(parts) > 2 else ""
                            matches.append((loc, code_snip))
            except Exception:
                pass

        if matches:
            results.append({"symbol": sym, "matches": matches, "source": source})

    return results


def format_symbol_index(symbol_results):
    """Format symbol discovery locations for injection into task directive."""
    if not symbol_results:
        return ""
    lines = ["Target symbol locations in repository:"]
    if any(res.get("source") == "grep" for res in symbol_results):
        lines.append("(ctags unavailable or no definition found; matches are from git grep)")
    for res in symbol_results:
        sym = res["symbol"]
        for loc, snip in res["matches"]:
            if snip:
                lines.append(f"- `{sym}` at `{loc}`: `{snip[:80]}`")
            else:
                lines.append(f"- `{sym}` at `{loc}`")
    return "\n".join(lines)


def park_issue(issue_url, pr_url, kind, text_or_reason, notes_dir, cli_fn=run_cli, cwd=None):
    """Park an issue with ghflow park, naming the PR only when one exists."""
    if kind == "time":
        next_step = "Resume with the local model after the time budget resets."
    else:
        next_step = ("Make sure that the issue is well-defined. If it is, retry with a different "
                     "local model or a person. If not, fix the preparation first. Do not use a cloud model.")
    text_file = notes_dir / f"park-{kind}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    text_file.write_text(f"## Parked ({kind})\n\n{text_or_reason}\n\nNext step: {next_step}\n", encoding="utf-8")
    args = ["park", issue_url]
    if pr_url:
        args += ["--pr", pr_url]
    args += ["--kind", kind, "--text", str(text_file)]
    out, code = cli_fn(*args, cwd=cwd)
    if code != 0:
        print(f"[{time.strftime('%X')}] Park failed (exit {code}): {out}", flush=True)
    return out, code

def find_issue_notes(issue_ref, notes_dir):
    """Locate summary, decisions, and review markdown files in notes_dir for an issue."""
    if not notes_dir or not Path(notes_dir).is_dir():
        return {}
    number = str(issue_ref).rstrip("/").split("/")[-1].split("#")[-1]
    res = {}
    for path in sorted(Path(notes_dir).glob(f"*{number}*")):
        if not path.is_file():
            continue
        name = path.stem.lower()
        if "summary" in name and "summary" not in res:
            res["summary"] = str(path)
        elif ("review" in name or "verdict" in name) and "review" not in res:
            res["review"] = str(path)
        elif "decision" in name and "decisions" not in res:
            res["decisions"] = str(path)
        elif "body" in name and "body" not in res:
            res["body"] = str(path)
    return res


def execute_submit_pr(state, owner, project, notes_dir, options, cli_fn=run_cli):
    """Submit a PR deterministically: compose body from notes, mark ready, and move board status."""
    pr = state.get("pr") or {}
    pr_url = pr.get("url")
    pr_num = pr.get("number")
    current_head = pr.get("head")
    issue_url = state.get("issue") or ""
    issue_num = str(issue_url).rstrip("/").split("/")[-1].split("#")[-1]
    repo = state.get("repo")
    target_pr = pr_url or (f"{repo}#{pr_num}" if repo and pr_num else str(pr_num or ""))

    notes = find_issue_notes(issue_url, notes_dir)
    body_file = None

    if repo and pr_num and notes_dir:
        out_file = Path(notes_dir) / f"pr-body-final-{issue_num}.md"
        body_args = ["pr", "body", str(pr_num), "--repo", repo, "--out", str(out_file), "--issue-number", str(issue_num)]
        if notes.get("summary"):
            body_args += ["--summary", notes["summary"]]
        if notes.get("review"):
            body_args += ["--review", notes["review"]]
        if notes.get("decisions"):
            body_args += ["--decisions", notes["decisions"]]
        out, code = cli_fn(*body_args, cwd=options.get("cwd"))
        if code == 0 and out_file.is_file():
            body_file = str(out_file)

    ready_args = ["pr", "ready", target_pr]
    if repo:
        ready_args += ["--repo", repo]
    if current_head:
        ready_args += ["--expect-head", current_head]
    if body_file:
        ready_args += ["--body-file", body_file]
    if owner and project:
        ready_args += ["--issue", str(issue_url), "--owner", owner, "--project", str(project), "--status", "In review"]

    out, code = cli_fn(*ready_args, cwd=options.get("cwd"))
    return code == 0, out


def worktree_status(issue_ref, cwd=None):
    """Find the issue's worktree and count its uncommitted paths."""
    number = str(issue_ref).rstrip("/").split("/")[-1].split("#")[-1]
    listing = git_output(["worktree", "list", "--porcelain"], cwd=cwd)
    if not listing:
        return {"path": None, "dirty": None}
    for block in listing.split("\n\n"):
        lines = block.splitlines()
        branch = next((line.removeprefix("branch refs/heads/") for line in lines
                       if line.startswith("branch refs/heads/")), "")
        if f"issue-{number}-" in branch or branch == f"issue-{number}":
            path = next((line.removeprefix("worktree ") for line in lines
                         if line.startswith("worktree ")), None)
            status = git_output(["status", "--porcelain"], cwd=path) if path else None
            return {"path": path, "dirty": len(status.splitlines()) if status is not None else None}
    return {"path": None, "dirty": None}


def review_independence_note(model, review_model):
    """Warn when the reviewer is the implementing model, or say the review is independent.

    A same-model reviewer is weakly independent: it is the same weights that
    wrote the diff, re-reading it with a fresh context. That is worth something
    but it is not adversarial, and the 2026-11-27 burndown showed the cost —
    thirteen consecutive `clean` verdicts carried two real defects through,
    including a "fix" for a behavior that never failed. Surfacing the pairing
    at preflight lets an operator notice a batch that will have no dissent in it.
    """
    if not model or not review_model:
        return None
    if model.strip() == review_model.strip():
        return (f"review model `{review_model}` is the implementation model; "
                f"expect weak independence — pass a different --review-model for "
                f"review that can disagree")
    return f"review is independent: implementation `{model}`, review `{review_model}`"


GUARD_PATH_MARKERS = (
    "tools/prompt_tools.py",
    "tools/admin_tools.py",
    "secret_policy.py",
    "tools/shell_tools.py",
    "tools/skill_tools.py",
    "prompts/",
)


def guard_touching_paths(state, options, cli_fn=run_cli, cwd=None, git=None):
    """Return changed paths in this delivery that hold a permission boundary or admin guard.

    Reviewing a diff that removes a refusal or an allowlist entry is a
    different question from reviewing a refactor. The reviewer needs to know a
    guard file is in the diff so it asks the right question; nothing in the
    diff itself announces it.

    Paths come from local git in the prepared review worktree, not from the
    GitHub API: `ghflow pr` has no changed-files command and `pr-state` does not
    carry them. Returns an empty list when the worktree or diff is unavailable,
    which keeps the note advisory rather than blocking.
    """
    from pathlib import Path as _Path

    git = git or git_output
    worktree = options.get("session_cwd")
    base = options.get("review_base") or "origin/main"
    if not worktree or not _Path(str(worktree)).is_dir():
        return []
    try:
        changed = git(["diff", "--name-only", f"{base}..HEAD"], cwd=str(worktree)) or ""
    except Exception:
        return []
    hits = []
    for name in changed.splitlines():
        name = name.strip()
        if name and any(marker in name for marker in GUARD_PATH_MARKERS):
            hits.append(name)
    return sorted(set(hits))[:8]


def format_run_summary(records, park_failures, notes_dir, start_time, cwd=None, facts_refresh=None,
                       session_monitor=None, model_note=None):
    """Render the run's deliveries, parked items, worktree state, and token totals."""
    lines = ["", "## Run summary", ""]
    if model_note:
        lines += [f"- Model: {model_note}.", ""]
    if session_monitor is not None:
        snapshot = session_monitor.snapshot()
        lines += ["## Monitor", "",
                  f"- Alerts: {len(snapshot['alerts'])}",
                  f"- Reports: `{snapshot['reports']['json']}` and `{snapshot['reports']['markdown']}`."]
        for alert in snapshot["alerts"]:
            lines.append(f"- {alert['name']} ({alert['phase']}): {alert['message']}")
        lines.append("")
    if facts_refresh:
        lines += ["## Project facts refresh", ""]
        if facts_refresh.get("status") == "refreshed":
            lines.append(f"- Refreshed: PR {facts_refresh.get('pr') or 'not read'} on branch "
                         f"`{facts_refresh.get('branch')}`; handoffs used `{facts_refresh.get('path')}`.")
        else:
            stale = ", ".join(facts_refresh.get("stale_sources") or []) or "none reported"
            lines.append(f"- Failed: {facts_refresh.get('reason')} Stale sources: {stale}.")
        lines.append("")
    if records:
        lines += ["| Issue | PR | Endpoint | Models (impl / review) | Worktree dirty |",
                  "| --- | --- | --- | --- | --- |"]
        for record in records:
            status = worktree_status(record.get("issue"), cwd)
            dirty = "n/a" if status.get("dirty") is None else str(status["dirty"])
            lines.append(f"| {record.get('issue')} | {record.get('pr') or 'none'} | "
                         f"{record.get('endpoint')} | {format_models(record.get('models'))} | {dirty} |")
    else:
        lines.append("No items reached an endpoint.")
    if park_failures:
        lines += ["", "Park failures:"]
        for entry in park_failures:
            lines.append(f"- {entry.get('issue')}: {entry.get('reason')}")
    followups = Path(notes_dir) / "followups.md"
    if followups.is_file():
        try:
            text = followups.read_text(encoding="utf-8").strip()
        except OSError:
            text = ""
        if text:
            lines += ["", "## Follow-ups", "", text]
    try:
        from cli.session import format_tokens, parse_session_log
        logs = sorted(Path(notes_dir).glob("session-*.log"))
        totals = [parse_session_log(log) for log in logs]
        turns = sum(p.get("total_turns", 0) for p in totals)
        output = sum(p.get("total_output_tokens", 0) for p in totals)
        reasoning = sum(p.get("total_reasoning_tokens", 0) for p in totals)
        if logs:
            lines += ["", f"Sessions: {len(logs)}, turns: {turns}, output: {format_tokens(output)}, "
                          f"reasoning: {format_tokens(reasoning)}"]
    except Exception:
        pass
    lines += ["", f"Duration: {(time.time() - start_time) / 3600:.1f}h"]
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic runner for unattended delivery from the project board.")
    parser.add_argument("--owner", help="project board owner login")
    parser.add_argument("--project", help="project board number or OWNER/NUMBER")
    parser.add_argument("--parent", action="append", dest="parents",
                        help="parent issue number, URL, or OWNER/REPO#NUMBER to burndown; repeat for several parents")
    parser.add_argument("--issue",
                        help="drive one issue URL directly, bypassing parent and board selection")
    parser.add_argument("--exclude", help="comma-separated issue numbers to skip when selecting from --parent (e.g. 1294,1295)")
    parser.add_argument("--require-label", action="append", default=[],
                        help="only select children carrying this label; repeat for several labels")
    parser.add_argument("--exclude-label", action="append", default=[],
                        help="skip children carrying this label; repeat for several labels")
    parser.add_argument("--model", required=True,
                        help="local implementation model in OpenCode's provider/model format (e.g. lmstudio/qwen3.8-27b-mlx@4bit)")
    parser.add_argument("--review-model", required=True,
                        help="local review model in OpenCode's provider/model format (e.g. lmstudio/recursivesi/flint)")
    parser.add_argument("--provider", help="local provider prefix for a model ID without a slash (e.g. lmstudio, ollama)")
    parser.add_argument("--allow-remote-models", action="store_true",
                        help="allow homelab gateway or cloud providers (e.g. otari/); local models remain the default")
    parser.add_argument("--hours", type=float, default=8.0, help="maximum run duration in hours (default 8)")
    parser.add_argument("--floor", type=int, default=DEFAULT_FLOOR_MINUTES, help="minimum minutes required to start a new issue")
    parser.add_argument("--once", action="store_true", help="drive exactly one item to desired state and exit")
    parser.add_argument("--allow-concurrent", action="store_true", help="bypass active session check")
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parent.parent), help="path to ghflow skill root")
    parser.add_argument("--notes-dir", help="custom task notes directory")
    parser.add_argument("--max-turns", type=int, default=None,
                        help="maximum turns per session (default 150)")
    parser.add_argument("--session-timeout", type=int, default=DEFAULT_SESSION_TIMEOUT, help="maximum seconds per session (default 5400)")
    parser.add_argument("--step-idle-timeout", type=int, default=DEFAULT_STEP_IDLE_TIMEOUT,
                        help=f"maximum idle seconds without stream events before session abort (default {DEFAULT_STEP_IDLE_TIMEOUT})")
    parser.add_argument("--context-warn-tokens", type=int, default=DEFAULT_CONTEXT_WARN_TOKENS,
                        help=f"warn when a step reaches this input and cached-prompt token count (default {DEFAULT_CONTEXT_WARN_TOKENS})")
    parser.add_argument("--max-context-tokens", type=int, default=DEFAULT_MAX_CONTEXT_TOKENS,
                        help="stop a session at a step boundary at this input and cached-prompt token count (default 0, off)")
    parser.add_argument("--no-precompute-gates", action="store_true",
                        help="do not run pre-computed test gates before review-changes")
    parser.add_argument("--require-facts-refresh", action="store_true",
                        help="stop before the first issue when a stale-facts refresh fails")
    parser.add_argument("--no-symbol-indexing", action="store_true",
                        help="do not index subsystem symbols before implement-issue")
    parser.add_argument("--narrative-category", default=narrative.DEFAULT_CATEGORY, help="discussion category slug for the run notebook (default lab-notebook)")
    parser.add_argument("--no-notebook", action="store_true", help="do not publish the run narrative to GitHub Discussions")
    parser.add_argument("--no-deterministic-pr", action="store_true",
                        help="dispatch an LLM worker session for submit-pr instead of submitting deterministically")
    parser.add_argument("--monitor-interval", type=int, default=monitor_mod.DEFAULT_INTERVAL_SECONDS,
                        help=f"seconds between monitor samples during a session (default {monitor_mod.DEFAULT_INTERVAL_SECONDS})")
    parser.add_argument("--monitor-endpoint", action="store_true",
                        help="probe LLAMA_CPP_BASE_URL for the model endpoint check")
    parser.add_argument("--worker-cmd",
                        help="worker executable command (e.g. opencode, custom wrapper; default: opencode or GHFLOW_WORKER_CMD)")
    parser.add_argument("--opencode-cmd", dest="worker_cmd",
                        help="deprecated alias for --worker-cmd")
    args = parser.parse_args(argv)
    if args.context_warn_tokens < 0 or args.max_context_tokens < 0:
        parser.error("--context-warn-tokens and --max-context-tokens must be 0 or greater")
    if args.monitor_interval < 0:
        parser.error("--monitor-interval must be 0 or greater")

    exclude = set()
    if args.exclude:
        try:
            exclude = {int(n.strip().lstrip("#")) for n in args.exclude.split(",") if n.strip()}
        except ValueError:
            parser.error("--exclude takes comma-separated issue numbers")
    parents = args.parents or []
    direct_issue = args.issue
    require_labels = [label for label in args.require_label if label]
    exclude_labels = [label for label in args.exclude_label if label]

    owner = args.owner
    project = None
    if args.project:
        if "/" in args.project:
            owner, project = discover_project(args.project)
        else:
            project = int(args.project)

    if not parents and not project:
        owner, project = discover_project()
        if args.owner:
            owner = args.owner
    elif parents and not project:
        try:
            disc_owner, disc_project = discover_project(cwd=os.getcwd())
            owner = owner or disc_owner
            project = disc_project
        except Exception:
            pass
    start_time = time.time()
    deadline_time = start_time + args.hours * 3600
    deadline_str = time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(deadline_time))
    notes_dir = Path(args.notes_dir) if args.notes_dir else Path.home() / ".local/state/ghflow/notes" / f"runner-{time.strftime('%Y%m%d-%H%M%S')}"
    notes_dir.mkdir(parents=True, exist_ok=True)

    selected_models, model_error = select_models(args.model, args.review_model, args.provider,
                                                 allow_remote=args.allow_remote_models)
    if model_error:
        print(f"[{time.strftime('%X')}] {model_error}", flush=True)
        return 1
    model = selected_models["implementation"]
    review_model = selected_models["review"]

    notice = remote_model_notice(selected_models)
    if notice:
        print(f"[{time.strftime('%X')}] {notice}", flush=True)
    independence = review_independence_note(model, review_model)
    if independence:
        print(f"[{time.strftime('%X')}] {independence}", flush=True)

    resolved_cmd = resolve_worker_cmd({"worker_cmd": args.worker_cmd})
    options = {
        "model": model, "review_model": review_model,
        "skill_dir": args.skill_dir, "notes_dir": notes_dir,
        "worker_cmd": resolved_cmd,
        "opencode_cmd": resolved_cmd,
        "deadline": deadline_str, "cwd": os.getcwd(), "standalone": True,
        "max_turns": args.max_turns, "session_timeout": args.session_timeout,
        "step_idle_timeout": args.step_idle_timeout,
        "context_warn_tokens": args.context_warn_tokens,
        "max_context_tokens": args.max_context_tokens,
        "no_precompute_gates": args.no_precompute_gates,
        "no_symbol_indexing": args.no_symbol_indexing,
        "deterministic_pr": not args.no_deterministic_pr,
    }
    attempted, delivered, park_failures = set(), [], []
    last_model = None
    delivery_records = []

    session_monitor = monitor_mod.Monitor(notes_dir)
    options["monitor"] = session_monitor
    options["monitor_interval"] = args.monitor_interval

    if direct_issue:
        target = f"issue {direct_issue}"
    elif parents:
        target = ", ".join(f"parent {parent}" for parent in parents)
    elif owner and project:
        target = f"project {owner}/{project}"
    else:
        target = None
    lock_info = None
    if not args.allow_concurrent:
        try:
            acquire_run_lock(notes_dir, target)
            check_active_runs(worker_cmd=resolved_cmd)
        except RuntimeError as error:
            lock_info = {"error": str(error)}
            session_monitor.add("runner_lock", "preflight", monitor_mod.STOP,
                                monitor_mod.FAIL, str(error), lock_info)
            session_monitor.write(force=True)
            print(session_monitor.status_line(), flush=True)
            raise
        lock_info = read_run_lock_holder()
    else:
        lock_info = read_run_lock_holder()
    if not args.no_symbol_indexing:
        refresh_tags(options["cwd"])
    facts_out = {}
    try:
        facts_out, _ = run_cli("facts", cwd=options.get("cwd"))
        warning = stale_facts_warning(facts_out)
        if warning:
            print(f"[{time.strftime('%X')}] Warning: {warning}", flush=True)
    except Exception as error:
        print(f"[{time.strftime('%X')}] Project facts check skipped: {error}", flush=True)
    identity_out, _ = run_cli("identity", cwd=options.get("cwd"))
    exec_user, _ = run_cli("exec", "--", "gh", "api", "user", cwd=options.get("cwd"))
    exec_login = exec_user.get("login") if isinstance(exec_user, dict) else None
    model_available = monitor_mod.probe_model(model, resolved_cmd)
    review_available = monitor_mod.probe_model(review_model, resolved_cmd)
    endpoint_url = os.environ.get("LLAMA_CPP_BASE_URL") if args.monitor_endpoint else None
    endpoint_ok = monitor_mod.probe_endpoint(endpoint_url) if endpoint_url else None
    session_monitor.preflight(facts_out, identity=identity_out, exec_login=exec_login,
                              lock=lock_info, model=model, model_available=model_available,
                              review_model=review_model, review_available=review_available,
                              endpoint_configured=endpoint_url, endpoint_ok=endpoint_ok)
    session_monitor.budget.update({"hours": args.hours, "floor_minutes": args.floor,
                                   "remaining_minutes": round((deadline_time - time.time()) / 60, 1)})
    session_monitor.write(force=True)
    print(session_monitor.status_line(), flush=True)
    if session_monitor.stopped:
        print(f"[{time.strftime('%X')}] Monitor stop: {session_monitor.stopped}", flush=True)
        return 1
    stale_note = stale_facts_warning(facts_out)
    facts_refresh = None
    if stale_note:
        print(f"[{time.strftime('%X')}] Dispatching the project facts refresh before the first issue...", flush=True)
        facts_refresh, refreshed_facts_path = dispatch_facts_refresh(facts_out, options, notes_dir, cli_fn=run_cli)
        if facts_refresh.get("status") == "refreshed":
            options["facts_path"] = refreshed_facts_path
            stale_note = None
            print(f"[{time.strftime('%X')}] Project facts refreshed at {refreshed_facts_path} "
                  f"(PR {facts_refresh.get('pr') or 'not read'}); handoffs point at that copy.", flush=True)
        else:
            print(f"[{time.strftime('%X')}] Project facts refresh failed: {facts_refresh.get('reason')} "
                  "Continuing with the stale-source note.", flush=True)
            if args.require_facts_refresh:
                print(f"[{time.strftime('%X')}] Stopping: --require-facts-refresh and the refresh failed.", flush=True)
                return 1
        if facts_refresh.get("status") == "refreshed":
            session_monitor.add("facts_refresh", "preflight", monitor_mod.ALERT, monitor_mod.PASS,
                                f"Project facts refreshed from origin (PR {facts_refresh.get('pr') or 'not read'}).",
                                {"pr": facts_refresh.get("pr"), "path": facts_refresh.get("path")})
        else:
            session_monitor.add("facts_refresh", "preflight", monitor_mod.ALERT, monitor_mod.FAIL,
                                f"Project facts refresh failed: {facts_refresh.get('reason')}",
                                {"pr": facts_refresh.get("pr"),
                                 "stale_sources": facts_refresh.get("stale_sources")})
        session_monitor.write(force=True)
        print(session_monitor.status_line(), flush=True)
    generated_paths = (((facts_out or {}).get("project_facts") or {}).get("worktree") or {}).get("generated") or []
    notebook = narrative.RunNotebook(cli_fn=run_cli, cwd=options.get("cwd"),
                                     category=args.narrative_category,
                                     enabled=not args.no_notebook)
    notebook.start(target=target, model=model,
                   hours=args.hours, notes_dir=notes_dir)

    def note_session(step, issue_url, success, info, log_path, state):
        """Summarize one session attempt and append it to the run notebook."""
        if not notebook.available:
            return
        summary, source = narrative.summarize_session(step, issue_url, success, info,
                                                      log_path or "", options)
        telemetry_str = None
        if log_path:
            try:
                from cli.session import parse_session_log, format_tokens
                p = parse_session_log(log_path)
                if p.get("total_turns"):
                    telemetry_str = (
                        f"{p['total_turns']} turns, "
                        f"{format_tokens(p['current_context_tokens'])} context, "
                        f"{format_tokens(p['total_output_tokens'])} out, "
                        f"{format_tokens(p['total_reasoning_tokens'])} reasoning "
                        f"(peak {format_tokens(p['peak_reasoning_tokens'])})"
                    )
            except Exception:
                pass

        pr = state.get("pr") or {}
        posted = notebook.step(step, issue_url, summary, pr_url=pr.get("url"), head=pr.get("head"),
                               telemetry=telemetry_str)
        if posted is not None:
            source_desc = f"{source} summary"
            if telemetry_str:
                source_desc += f"; {telemetry_str}"
            print(f"[{time.strftime('%X')}] Notebook step note posted ({source_desc})", flush=True)
    def record_park(issue_url, pr_url, text, kind="blocker"):
        """Park an issue and keep a failed park visible in the run result."""
        out, code = park_issue(issue_url, pr_url, kind, text, notes_dir, cli_fn=run_cli)
        if code != 0:
            park_failures.append({"issue": issue_url, "reason": text, "output": out})
        return code

    previous_states = {}
    selection_recorded = False
    recorded_parents = set()
    monitor_selection = []
    final_states = []
    throughput_marks = []

    def mark_throughput():
        done = sum(1 for record in delivery_records if record.get("endpoint") == "DONE")
        if done:
            throughput_marks.append({"name": f"issue {done}",
                                     "hours_per_done": round((time.time() - start_time) / 3600 / done, 2)})

    parent_children = None
    parent_index = 0
    current_parent = None
    board_index = {}
    while True:
        if session_monitor.stopped:
            break
        if time.time() >= deadline_time:
            break
        if direct_issue:
            item = {"url": direct_issue}
        elif parents:
            if parent_index >= len(parents):
                print(f"[{time.strftime('%X')}] No more parent issues.")
                break
            parent_ref = parents[parent_index]
            if parent_children is None or current_parent != parent_ref:
                print(f"[{time.strftime('%X')}] Reading parent issue {parent_ref}...")
                parent_data = observe_parent(parent_ref, cwd=options.get("cwd"))
                parent_children = parent_data.get("children") or []
                current_parent = parent_ref
                board_index = load_board_index(owner, project, cli_fn=run_cli)
            if parent_ref not in recorded_parents:
                monitor_selection.extend(parent_children or [])
                session_monitor.selection(parent_children, required_labels=require_labels,
                                          exclude_labels=exclude_labels)
                session_monitor.write(force=True)
                print(session_monitor.status_line(), flush=True)
                recorded_parents.add(parent_ref)
            item = next_item_for_parent(parent_children, attempted, cli_fn=run_cli, cwd=options.get("cwd"),
                                        exclude=exclude, require_labels=require_labels,
                                        exclude_labels=exclude_labels, board_index=board_index)
            if item is None:
                print(f"[{time.strftime('%X')}] Parent {parent_ref} has no more actionable items.")
                parent_index += 1
                parent_children = None
                current_parent = None
                board_index = {}
                continue
        else:
            print(f"[{time.strftime('%X')}] Reading board for project {owner}/{project}...")
            board = observe_board(owner, project)
            if not selection_recorded:
                monitor_selection = ((board.get("parked") or [])
                                     + (board.get("selection") or []))
                session_monitor.selection(monitor_selection, required_labels=require_labels,
                                          exclude_labels=exclude_labels)
                session_monitor.write(force=True)
                print(session_monitor.status_line(), flush=True)
                selection_recorded = True
            item = next_item(board, attempted, exclude=exclude)

        if item is None:
            print(f"[{time.strftime('%X')}] No more actionable items.")
            break
        issue_ref = item.get("url") or item.get("issue") or (str(item["number"]) if item.get("number") is not None else None)
        print(f"[{time.strftime('%X')}] Selected item: {issue_ref} - {item.get('title')}")
        attempted.add(issue_ref)
        published_pr = None
        pending = {}
        repair_attempts = 0

        def flush_monitor(state, step, phase_end=False):
            entry = pending.pop("entry", None)
            if entry:
                session_monitor.after_step(entry["step"], state, success=entry["success"],
                                           info=entry["info"], published=entry["published"],
                                           worktree=entry["worktree"])
            if phase_end:
                session_monitor.phase_end("issue", issue=state.get("issue") or issue_ref, step=step,
                                          state=state,
                                          remaining_minutes=(deadline_time - time.time()) / 60)
            session_monitor.write(force=True)
            print(session_monitor.status_line(), flush=True)

        session_monitor.phase_start("issue", issue=issue_ref,
                                    remaining_minutes=(deadline_time - time.time()) / 60)
        session_monitor.write(force=True)
        print(session_monitor.status_line(), flush=True)
        # Issue reconciliation loop
        while True:
            state = observe_issue(issue_ref)
            if not state.get("pr"):
                seeded = published_pr_state(published_pr)
                if seeded:
                    state["pr"] = seeded
            step = next_step(state)
            remaining_minutes = (deadline_time - time.time()) / 60
            flush_monitor(state, step, phase_end=step in ("DONE", "PARKED", "WAITING"))
            if session_monitor.stopped:
                print(f"[{time.strftime('%X')}] Monitor stop: {session_monitor.stopped}", flush=True)
                break
            if should_stop_for_floor(step, remaining_minutes, args.floor,
                                     options.get("deterministic_pr", True)):
                print(f"[{time.strftime('%X')}] Time budget floor reached ({remaining_minutes:.1f}m < {args.floor}m) before {step}. Stopping.")
                flush_monitor(state, step, phase_end=True)
                park_text = phase_boundary_park(state, step, remaining_minutes, args.floor)
                if park_text:
                    pr_url = (state.get("pr") or {}).get("url")
                    code = record_park(state["issue"], pr_url, park_text, kind="time")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url,
                                             "endpoint": "time-park" if code == 0 else "park-failed",
                                             "models": selected_models})
                final_states.append(dict(state))
                break
            print(f"[{time.strftime('%X')}] {issue_ref}: next step is {step}")
            if step in ("DONE", "PARKED", "WAITING"):
                print(f"[{time.strftime('%X')}] {issue_ref} reached endpoint state: {step}")
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref,
                                         "pr": (state.get("pr") or {}).get("url"), "endpoint": step,
                                         "models": selected_models})
                final_states.append(dict(state))
                if step == "DONE":
                    mark_throughput()
                    set_board_status(issue_ref, "In review", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))
                break
            if step == "park-blocker":
                pr_url = parked_pr_url(state, published_pr, cli_fn=run_cli, cwd=options.get("cwd"))
                record_park(state["issue"], pr_url, "Exceeded correction limit.")
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked", "models": selected_models})
                final_states.append(dict(state))
                flush_monitor(state, step, phase_end=True)
                break
            if step == "wait-ci":
                time.sleep(15)
                continue

            prev = previous_states.get(issue_ref)
            curr = (step, (state.get("pr") or {}).get("head"), (state.get("review_verdicts") or [{}])[-1].get("verdict"))
            if prev == curr:
                pr_url = parked_pr_url(state, published_pr, cli_fn=run_cli, cwd=options.get("cwd"))
                record_park(state["issue"], pr_url, stall_reason(worktree, step))
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked", "models": selected_models})
                break
            previous_states[issue_ref] = curr

            # Update board status to In progress on start of implementation
            if step == "implement-issue":
                set_board_status(issue_ref, "In progress", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))

            worktree = None
            base_pr = find_base_pr(issue_ref, parent_children, cli_fn=run_cli,
                                   cwd=options.get("cwd"), child_state=state) if parent_children else None
            pr_base = (state.get("pr") or {}).get("base")
            stack_base = (base_pr if base_pr and (not pr_base or pr_base == base_pr["branch"])
                          else None)
            worktree_base = pr_base or (stack_base["branch"] if stack_base else None)
            review_base = f"origin/{worktree_base}" if worktree_base else "origin/main"
            step_options = dict(options)
            step_options["max_turns"] = issue_turn_limit(args.max_turns)
            if selected_models:
                step_options["model"] = (selected_models["review"] if step == "review-changes"
                                         else selected_models["implementation"])
            earlier_blocking = sum(1 for r in (state.get("reviews") or []) if r.get("state") == "CHANGES_REQUESTED") + \
                               sum(1 for v in (state.get("review_verdicts") or []) if is_verdict_blocking(v))
            verification = verification_lines(state.get("body"))
            verification_note = (
                " Issue verification: " + " ".join(verification) +
                " Run these focused tests during iteration; before finishing, run the project gates once with "
                "`python3 \"$GHFLOW_CLI\" gate --summary --cmd \"make check\" --cmd \"make test\"` "
                "(use the project facts gate commands)."
                if verification else ""
            )
            if step == "submit-pr" and options.get("deterministic_pr", True):
                print(f"[{time.strftime('%X')}] Submitting PR for {issue_ref} deterministically...", flush=True)
                success, info = execute_submit_pr(state, owner, project, notes_dir, step_options, cli_fn=run_cli)
                print(f"[{time.strftime('%X')}] PR submission {'succeeded' if success else 'failed'}: {info}", flush=True)
                checkpoint = f"**PR submitted** — `{step}` for {state['issue']}."
                if notebook.discussion and notebook.discussion.get("url"):
                    checkpoint += f" Run narrative: {notebook.discussion['url']}"
                narrative.post_issue_checkpoint(run_cli, state["issue"], checkpoint, cwd=options.get("cwd"))
                note_session(step, state["issue"], success, "deterministic", None, state)
                if success:
                    pr = state.setdefault("pr", {})
                    pr["is_draft"] = False
                    if isinstance(info, dict) and info.get("url"):
                        pr["url"] = pr.get("url") or info["url"]
                pending["entry"] = {"step": "submit-pr", "success": success, "info": info,
                                    "published": info if isinstance(info, dict) else None,
                                    "worktree": worktree_status(state["issue"], cwd=options.get("cwd"))}
                if not success:
                    pr_url = parked_pr_url(state, published_pr, cli_fn=run_cli, cwd=options.get("cwd"))
                    record_park(state["issue"], pr_url, f"Deterministic PR submission failed: {info}")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked", "models": selected_models})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                if (deadline_time - time.time()) / 60 < args.floor:
                    pr_url = info.get("url") if isinstance(info, dict) else None
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref,
                                             "pr": pr_url or (state.get("pr") or {}).get("url"),
                                             "endpoint": "ready", "models": selected_models})
                    print(f"[{time.strftime('%X')}] {issue_ref} is ready; stopping below the floor before the CI wait.", flush=True)
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                continue
            elif step == "address-pr-review":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
            elif step == "repair-conflict":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                path = existing.get("path")
                branch = git_output(["rev-parse", "--abbrev-ref", "HEAD"], cwd=path) if path else None
                pr_url = (state.get("pr") or {}).get("url")
                if not path or not branch:
                    record_park(state["issue"], pr_url,
                                "The conflicting PR has no task worktree to repair.")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref,
                                             "pr": pr_url, "endpoint": "parked",
                                             "models": selected_models})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                repair_attempts += 1
                if repair_attempts > CORRECTION_LIMIT:
                    record_park(state["issue"], pr_url,
                                "Conflict repair did not settle within the correction limit.")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref,
                                             "pr": pr_url, "endpoint": "parked",
                                             "models": selected_models})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                base_name = worktree_base or "main"
                worktree = {"path": path, "branch": branch, "base": f"origin/{base_name}",
                            "setup": {"generated": generated_paths}}
                step_options["session_cwd"] = path
                step_options["branch"] = branch
                merge_state = prepare_conflict_merge(path, base_name)
                files = merge_state.get("files") or []
                if not merge_state.get("ok") and not files:
                    record_park(state["issue"], pr_url,
                                f"The base merge failed without conflict files: {merge_state.get('reason')}")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref,
                                             "pr": pr_url, "endpoint": "parked",
                                             "models": selected_models})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                if files:
                    step_options["extra_text"] = (
                        f"The runner merged `origin/{base_name}` into this worktree and left conflicts in: "
                        f"{', '.join(files)}. Resolve every conflict marker. Preserve both intents; do not "
                        "drop either side to make the merge quiet. Keep the issue scope. Run the focused "
                        "tests and the project gate once. Commit the merge and push to the same branch "
                        "with `python3 \"$GHFLOW_CLI\" exec -- git ...`."
                    )
                else:
                    step_options["extra_text"] = (
                        f"The runner merged `origin/{base_name}` cleanly. Run the focused tests, commit "
                        "any remaining change, and push to the same branch."
                    )
            elif step == "submit-pr":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
                target_base = f"Target base branch `{stack_base['branch']}`. " if stack_base else ""
                step_options["extra_text"] = (
                    f"Direct submission: do not read shared reference files or re-verify code. {target_base}"
                    "Compose the final description with `pr body` and mark the PR ready with `pr ready --expect-head` immediately. "
                    "Be direct and concise."
                )
            elif step == "review-changes":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
                base_ref = review_base
                step_options["review_base"] = base_ref
                stacked_note = f" This PR is stacked on base `{stack_base['branch']}`; hosted CI does not run for non-main targets on this repo. Use local worktree gate checks for the review, and keep the PR a draft until hosted checks run." if stack_base else ""
                verdict_rule = " Verdict rules: if '## Blocking findings' is empty or None, verdict MUST be 'clean', even if non-blocking notes or follow-up ideas appear under '## Notes'. Use 'findings' only for actionable blocking defects."

                gate_note = ""
                if not options.get("no_precompute_gates", False):
                    review_wt = prepare_worktree(state["issue"], state.get("title"), owner, project, step_options,
                                                 cli_fn=run_cli,
                                                 base_branch=worktree_base)
                    if review_wt and review_wt.get("path"):
                        step_options["session_cwd"] = review_wt["path"]
                        gate_res = run_precomputed_gate(review_wt["path"], generated_paths=generated_paths)
                        if gate_res and gate_res.get("text"):
                            gate_note = f" {gate_res['text']}"
                            checkpoint = f"**Gate check** — `{step}` for {state['issue']}: {gate_res['summary']}."
                            if notebook.discussion and notebook.discussion.get("url"):
                                checkpoint += f" Run narrative: {notebook.discussion['url']}"
                            narrative.post_issue_checkpoint(run_cli, state["issue"], checkpoint, cwd=options.get("cwd"))

                gate_instruction = (
                    "The runner already ran `make check` at this head; use `review inspect --no-gate` and do not repeat that command. "
                    "Run the remaining project gates and the issue's focused verification tests with one "
                    "`gate --summary --cmd ...` call."
                    if gate_note else
                    "Run `review inspect`; run the project gates once with "
                    "`gate --summary --cmd \"make check\" --cmd \"make test\"` (use the project facts gate commands)."
                )
                workspace_note = (
                    " The OpenCode shell starts in the project checkout; cd to the task worktree or use absolute paths."
                    + (f" Worktree: {step_options['session_cwd']}." if step_options.get("session_cwd") else "")
                )
                model_note = (f" Post the verdict with `review verdict ... --model {step_options['model']}` or include `model={step_options['model']}` in a `pr comment` marker."
                              if step_options.get("model") else "")
                guard_note = ""
                guard_paths = guard_touching_paths(state, step_options, cli_fn=run_cli, cwd=options.get("cwd"))
                if guard_paths:
                    guard_note = (f" Guard watch: this diff touches {', '.join(guard_paths)}. "
                                  "If it removes or weakens a refusal, allowlist entry, symlink or redirect check, "
                                  "confirmation gate, or permission boundary, the verdict MUST be `blocked`, not "
                                  "`clean` or `findings` — the user decides whether that protection is removed, "
                                  "and the builder cannot resolve it. Say plainly which protection the diff removes.")
                if earlier_blocking > 0:
                    step_options["extra_text"] = (
                        f"Scope: Re-review of correction on HEAD. Focus on the commit diff (`git diff HEAD~1..HEAD` or `git diff {base_ref}...HEAD`) "
                        f"and verifying that the earlier finding is resolved. Do not re-audit unchanged components or pre-load shared reference files.{workspace_note}{model_note}{stacked_note}{verdict_rule}{gate_note}{guard_note} {gate_instruction}{verification_note}"
                    )
                else:
                    step_options["extra_text"] = (
                        "Scope: Review committed changes on HEAD against the issue requirements. "
                        f"Inspect the commit diff (`git diff {base_ref}...HEAD`). {gate_instruction} "
                        f"Post the verdict comment directly with `pr comment`. "
                        f"Do not write new end-to-end integration test suites, browser harnesses, or query session databases.{workspace_note}{model_note}{stacked_note}{verdict_rule}{gate_note}{guard_note}{verification_note}"
                    )
            elif step == "implement-issue":
                worktree = prepare_worktree(state["issue"], state.get("title"), owner, project, step_options,
                                            cli_fn=run_cli,
                                            base_branch=worktree_base)
                if worktree:
                    step_options["session_cwd"] = worktree["path"]
                directive = (
                    "Workspace: the runner prepared the task worktree. The OpenCode shell starts in the project checkout, "
                    "so prefix each shell command with `cd <worktree>` or use absolute paths. "
                    "Do not edit the primary checkout, and do not survey the code with `git show origin/...` or "
                    "`git grep origin/...` instead of the worktree: those reads publish nothing. "
                    "`GHFLOW_CLI` is already set in the environment; use `python3 \"$GHFLOW_CLI\"` and do not re-export it. "
                    "For symbol lookups, run `python3 \"$GHFLOW_CLI\" tags brief SYMBOL...` before `grep` or a full read. Use `tags outline FILE` to choose line ranges. "
                    "The task worktree is already prepared; do not run `worktree prepare`. "
                    "Focus solely on editing files in the worktree and passing the project gates. "
                    "Run the gate sequence once with `python3 \"$GHFLOW_CLI\" gate --summary --cmd \"make check\" --cmd \"make test\"` "
                    "(use the project facts gate commands); do not repeat a command the helper already ran. "
                    "Do not push to remote or create pull requests; the runner publishes all worktree progress and handles PR creation automatically."
                )
                if worktree:
                    step_options["branch"] = worktree["branch"]
                    if worktree["created"]:
                        directive += (
                            f" Worktree: {worktree['path']} on branch {worktree['branch']}, created now."
                            " Do the project's worktree setup there, then read and edit the files in it."
                        )
                    else:
                        directive += (
                            f" Worktree: {worktree['path']} on branch {worktree['branch']}, reused from an earlier attempt."
                            " Read its uncommitted changes and its task notes first, and continue that work instead of"
                            " starting a competing implementation or resetting the branch."
                        )
                    setup = worktree.get("setup") or {}
                    if setup.get("source") == "project_facts":
                        directive += (
                            " The runner applied the project facts worktree declaration"
                            f" (copy: {', '.join(setup.get('copy') or []) or 'none'};"
                            f" setup: {', '.join(setup.get('setup') or []) or 'none'})."
                            " Do not repeat those steps; check only where a command did not apply."
                        )
                    elif not worktree["created"]:
                        directive += (
                            " Do the project's worktree setup only where it is still missing,"
                            " so an existing configuration is not overwritten."
                        )
                else:
                    directive += (
                        " No worktree was prepared, so create it with `worktree create ISSUE_URL --branch BRANCH`, "
                        "which bases the branch on `origin/<default-branch>`."
                    )
                if stack_base:
                    directive += (
                        f" Stacked PR: base child #{stack_base['number']} has an open PR #{stack_base['pr']} on branch "
                        f"`{stack_base['branch']}`. "
                        + ("The runner created this worktree from that branch. " if worktree else
                           f"Create the worktree with `worktree create ISSUE_URL --branch BRANCH --base {stack_base['branch']}`. ")
                        + f"Set `--base {stack_base['branch']}` when the draft PR is created. "
                        + f"Name the stack and PR #{stack_base['pr']} in the PR body."
                    )
                if not options.get("no_symbol_indexing", False):
                    symbols = extract_candidate_symbols(state.get("title"), state.get("body", ""))
                    if symbols and worktree and worktree.get("path"):
                        sym_matches = find_subsystem_symbols(symbols, cwd=worktree["path"])
                        sym_text = format_symbol_index(sym_matches)
                        if sym_text:
                            directive += f"\n\n{sym_text}"
                checkpoint = f"**Work started** — `{step}` for {state['issue']}."
                if worktree:
                    checkpoint += f" Branch `{worktree['branch']}` in `{worktree['path']}`."
                if notebook.discussion and notebook.discussion.get("url"):
                    checkpoint += f" Run narrative: {notebook.discussion['url']}"
                narrative.post_issue_checkpoint(run_cli, state["issue"], checkpoint,
                                                cwd=options.get("cwd"))
                directive += verification_note
                directive += (
                    " Commit a checkpoint as soon as the change is coherent and the focused tests pass, "
                    "before the full gate run. If the full gate finds a fix, make a follow-up commit."
                )
                if generated_paths:
                    directive += (
                        " The project facts list generated paths: " + ", ".join(generated_paths) +
                        ". If `make check` regenerates them, restore them with "
                        "`git restore -- <paths>` before committing; do not commit generated drift."
                    )
                step_options["extra_text"] = directive
            if stale_note:
                step_options["extra_text"] = (
                    (step_options.get("extra_text") or "") + " " + stale_note +
                    " Read the current files in your worktree and do not rely on the stale facts sections."
                ).strip()
            captured = {}

            def publish_step_work():
                """Publish committed implementation work that the session left unpublished."""
                if step in ("implement-issue", "repair-conflict"):
                    session_ref = None
                    if captured.get("log"):
                        session_ref = session_reference(notes_dir, Path(captured["log"]))
                    return publish_committed(state["issue"], state.get("title"), worktree, state.get("repo"),
                                             notes_dir, step_options,
                                             base_branch=stack_base["branch"] if stack_base else None,
                                             stack=stack_base, session_ref=session_ref, cli_fn=run_cli)
                return None

            session_monitor.phase_start("session", issue=state["issue"], step=step,
                                        remaining_minutes=remaining_minutes)
            step_model = step_options.get("model")
            if step_model != last_model:
                unload = unload_local_models(step_model)
                if unload.get("status") == "unloaded":
                    print(f"[{time.strftime('%X')}] Unloaded LM Studio models before {step}.", flush=True)
                elif unload.get("status") == "failed":
                    print(f"[{time.strftime('%X')}] Model unload failed: {unload.get('reason')}", flush=True)
                last_model = step_model
            print(f"[{time.strftime('%X')}] Starting {step} session for {issue_ref}...")
            success, info = run_session(step, state["issue"], notes_dir, step_options,
                                        log_hook=lambda path: captured.update(log=path))
            print(f"[{time.strftime('%X')}] Session finished (success={success}, id={info})")
            note_session(step, state["issue"], success, info, captured.get("log"), state)
            published_pr = publish_step_work() or published_pr
            pending["entry"] = {"step": step, "success": success, "info": info,
                                "published": published_pr,
                                "worktree": worktree_status(state["issue"], cwd=options.get("cwd"))}
            if not success:
                print(f"[{time.strftime('%X')}] Session failed, retrying once in fresh session...")
                prior_actions = recent_session_actions(captured.get("log"))
                if prior_actions:
                    step_options["extra_text"] = retry_directive(step_options.get("extra_text"),
                                                                prior_actions, step=step)
                captured = {}
                success, info = run_session(step, state["issue"], notes_dir, step_options,
                                            log_hook=lambda path: captured.update(log=path))
                note_session(step, state["issue"], success, info, captured.get("log"), state)
                published_pr = publish_step_work() or published_pr
                pending["entry"] = {"step": step, "success": success, "info": info,
                                    "published": published_pr,
                                    "worktree": worktree_status(state["issue"], cwd=options.get("cwd"))}
                if not success:
                    pr_url = parked_pr_url(state, published_pr, cli_fn=run_cli, cwd=options.get("cwd"))
                    record_park(state["issue"], pr_url, f"Session failed repeatedly: {info}")
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked", "models": selected_models})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
        if args.once or direct_issue:
            break

    toil_report = None
    toil_res = None
    try:
        from audit_toil import audit_toil, format_markdown_report
        toil_res, _ = audit_toil(dirs=[str(notes_dir)], min_strikes=3)
        patterns = toil_res.get("patterns") or []
        if patterns:
            toil_report = format_markdown_report(patterns, toil_res.get("scanned", 0))
            print(f"\n[{time.strftime('%X')}] Toil audit detected {len(patterns)} pattern(s) hitting Strike 3:\n{toil_report}\n", flush=True)
    except Exception as e:
        print(f"[{time.strftime('%X')}] Toil audit skipped: {e}", flush=True)

    budget = {"hours": args.hours, "floor_minutes": args.floor,
              "elapsed_hours": round((time.time() - start_time) / 3600, 2),
              "remaining_minutes": round((deadline_time - time.time()) / 60, 1)}
    session_monitor.finish(records=delivery_records, selection=list(attempted),
                           states=final_states, toil=toil_res,
                           phase_throughput=throughput_marks, budget=budget)
    session_monitor.write(force=True)
    print(session_monitor.status_line(), flush=True)

    model_note = f"implementation `{model}`, review `{review_model}`"
    print(format_run_summary(delivery_records, park_failures, notes_dir, start_time,
                             options.get("cwd"), facts_refresh=facts_refresh,
                             session_monitor=session_monitor, model_note=model_note), flush=True)
    notebook.finish(delivered, park_failures, toil_report=toil_report)
    summary_rows = None
    if delivered and owner and project:
        summary_out, summary_code = run_cli("queue", "summary", *[str(d) for d in delivered],
                                            "--owner", owner, "--project", str(project))
        if summary_out.get("table"):
            print(summary_out["table"], flush=True)
        if summary_code != 0:
            print(f"[{time.strftime('%X')}] Queue summary exited {summary_code}: {summary_out.get('errors')}", flush=True)
        else:
            summary_rows = summary_out.get("rows")
    elif delivered:
        print(f"[{time.strftime('%X')}] Burndown complete. Delivered items: {', '.join(str(d) for d in delivered)}")
    session_monitor.summary_coverage(summary_rows)
    session_monitor.write(force=True)
    print(session_monitor.status_line(), flush=True)
    if session_monitor.stopped:
        print(f"[{time.strftime('%X')}] Monitor stop: {session_monitor.stopped}", flush=True)
        return 1
    if park_failures:
        print(f"[{time.strftime('%X')}] {len(park_failures)} park attempt(s) failed; these items were not recorded:")
        for entry in park_failures:
            print(f"  {entry['issue']}: {entry['reason']}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
