#!/usr/bin/env python3
"""Deterministic runner that drives unattended delivery from the project board."""
import argparse
import json
import os
import re
import select
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
DEFAULT_CONTEXT_WARN_TOKENS = 100000
DEFAULT_MAX_CONTEXT_TOKENS = 0
SLOW_STEP_WARN_SECONDS = 120
MAX_DEGENERATE_REASONING = 10000
PRIORITY_ORDER = ("P0", "P1")
SIZE_ORDER = ("XS", "S", "M", "L", "XL")
_RUN_LOCK = None


def find_cli():
    """Locate cli/ghflow.py."""
    env_cli = os.environ.get("GHFLOW_CLI")
    if env_cli and Path(env_cli).is_file():
        return Path(env_cli)
    repo_cli = Path(__file__).resolve().parent.parent / "cli" / "ghflow.py"
    if repo_cli.is_file():
        return repo_cli
    raise FileNotFoundError("Could not locate cli/ghflow.py. Set GHFLOW_CLI.")


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


def check_active_runs(opencode_cmd="opencode", process_checker=None):
    """Raise RuntimeError if an unattended session was active in the last 30 minutes and its process is alive."""
    if not shutil.which(opencode_cmd):
        return
    proc = subprocess.run([opencode_cmd, "session", "list", "--format", "json"], stdin=subprocess.DEVNULL,
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
    m = re.search(r"##\s*Blocking findings\s*\n+([^\n#]+)", body, re.IGNORECASE)
    if m:
        val = m.group(1).strip().lower().rstrip(".")
        if val in ("none", "no blocking findings", "no blockers", "none —", "none -"):
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
        return "DONE"
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


def next_item(board, attempted=None):
    """Pure function selecting the next item from board state (Decision 9)."""
    attempted = attempted or set()
    in_flight = board.get("in_flight") or []
    for item in in_flight:
        num = item.get("number")
        if num in attempted or item.get("issue") in attempted or item.get("url") in attempted:
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
        if item.get("park_kind") in ("question", "blocker"):
            continue
        return item

    selection = board.get("selection") or []
    for item in selection:
        num = item.get("number")
        if num in attempted or item.get("issue") in attempted or item.get("url") in attempted:
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
            "is_draft": pr_st.get("is_draft", pr.get("is_draft", False)),
            "state": pr_st.get("state") or pr.get("state", "OPEN"),
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
        if ("triage:needs-input" in labels or "triage:blocked" in labels
                or "triage:needs-definition" in labels):
            continue
        if require_labels and not all(label in labels for label in require_labels):
            continue
        if exclude_labels and any(label in labels for label in exclude_labels):
            continue
        if any(blocker.get("state") == "OPEN" for blocker in st.get("blocked_by") or []):
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


def find_preceding_pr(child_ref, children, cli_fn=run_cli, cwd=None, child_state=None, force=False):
    """Find the preceding child whose open PR this child depends on, for stacking.

    A stack is created only for a native blocked-by link, so independent children
    branch from the default branch. ``force`` keeps the old "nearest open PR"
    behavior for a user who explicitly asks for a stack.
    """
    if not children:
        return None
    target_num = child_ref if isinstance(child_ref, int) else None
    if target_num is None:
        try:
            target_num = int(str(child_ref).rstrip("/").split("/")[-1].split("#")[-1])
        except ValueError:
            target_num = None

    idx = None
    for i, c in enumerate(children):
        if c.get("number") == target_num or c.get("url") == str(child_ref):
            idx = i
            break
    if idx is None or idx == 0:
        return None

    blocked = {blocker.get("number") for blocker in (child_state or {}).get("blocked_by") or []
               if blocker.get("number") is not None}
    for c in reversed(children[:idx]):
        if c.get("state") == "CLOSED":
            continue
        if not force and c.get("number") not in blocked:
            continue
        ref = c.get("url") or c.get("number")
        st = observe_issue(ref, cli_fn=cli_fn, cwd=cwd)
        pr = st.get("pr") or {}
        if pr.get("head_branch") and pr.get("state") == "OPEN":
            return {"number": c.get("number"), "pr": pr.get("number"), "branch": pr.get("head_branch")}
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


def context_warning(context_tokens, warn_tokens, warned):
    """Describe a session that reached the context warning threshold."""
    if warned or not warn_tokens or context_tokens < warn_tokens:
        return None
    return f"Session context reached {context_tokens} tokens (warn {warn_tokens})."


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
    cmd = [options.get("opencode_cmd", "opencode"), "run", "--auto", "--format", "json",
           "--title", f"Queue runner {step} {stamp}"]
    if options.get("model"):
        cmd += ["--model", options["model"]]
    if options.get("standalone"):
        cmd.append("--standalone")
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
    print(f"[{time.strftime('%X')}] Logging session output to {session_log}")
    if options.get("session_cwd"):
        print(f"[{time.strftime('%X')}] Session cwd: {options['session_cwd']}", flush=True)
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
            warning = context_warning(context_tokens, context_warn_tokens, context_warned)
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
        subprocess.run([options.get("opencode_cmd", "opencode"), "session", "delete", session_id],
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


def prepare_worktree(issue_url, title, owner, project, options, cli_fn=run_cli):
    """Create the task worktree from origin before the session starts.

    The worktree and branch are a runner decision, not a model choice, so the session
    cannot spend its budget surveying a stale checkout. Exit 3 means the branch or
    path already exists, which is a resumption; reuse it.
    """
    number = str(issue_url).rstrip("/").split("/")[-1]
    slug = re.sub(r"[^a-z0-9]+", "-", str(title or "").lower()).strip("-")[:40].strip("-")
    branch = f"issue-{number}-{slug}" if slug else f"issue-{number}"
    args = ["worktree", "create", issue_url, "--branch", branch]
    if owner and project:
        args += ["--owner", owner, "--project", str(project)]
    out, code = cli_fn(*args, cwd=options.get("cwd"))
    path = (out or {}).get("path") if isinstance(out, dict) else None
    if code not in (0, 3) or not path:
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

def committed_count(path, base):
    """Count commits on the worktree branch since the base revision."""
    out = git_output(["rev-list", "--count", f"{base}..HEAD"], cwd=path)
    try:
        return int(out)
    except (TypeError, ValueError):
        return None


def publish_committed(issue_url, title, worktree, repo, notes_dir, options, base_branch=None, cli_fn=run_cli):
    """Push a session's committed work and open a draft PR when none exists.

    The session keeps the content and commit role. This closes the gap that the
    epic #1434 trial showed: a session that commits and stops leaves the delivery
    invisible. ``pr create`` refuses an existing open PR, so a session that
    published its own PR keeps that PR instead of a duplicate.
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
            cli_fn("exec", "--", "git", "-C", path, "commit", "-m", commit_msg, cwd=options.get("cwd"))
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
    body_file.write_text("\n".join([
        f"Draft checkpoint for {issue_url}.",
        "",
        "The queue runner published committed work that the implementation session left unpublished.",
        "",
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
    text_file = notes_dir / f"park-{kind}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    text_file.write_text(f"## Parked ({kind})\n\n{text_or_reason}\n", encoding="utf-8")
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


def format_run_summary(records, park_failures, notes_dir, start_time, cwd=None, facts_refresh=None,
                       session_monitor=None):
    """Render the run's deliveries, parked items, worktree state, and token totals."""
    lines = ["", "## Run summary", ""]
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
        lines += ["| Issue | PR | Endpoint | Worktree dirty |", "| --- | --- | --- | --- |"]
        for record in records:
            status = worktree_status(record.get("issue"), cwd)
            dirty = "n/a" if status.get("dirty") is None else str(status["dirty"])
            lines.append(f"| {record.get('issue')} | {record.get('pr') or 'none'} | "
                         f"{record.get('endpoint')} | {dirty} |")
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
    parser.add_argument("--exclude", help="comma-separated issue numbers to skip when selecting from --parent (e.g. 1294,1295)")
    parser.add_argument("--require-label", action="append", default=[],
                        help="only select children carrying this label; repeat for several labels")
    parser.add_argument("--exclude-label", action="append", default=[],
                        help="skip children carrying this label; repeat for several labels")
    parser.add_argument("--stack", action="store_true",
                        help="stack on the nearest preceding open PR even without a native blocked-by link")
    parser.add_argument("--model", help="model override for worker sessions, in OpenCode's provider/model format (e.g. lmstudio/qwen3.8-27b-mlx@4bit)")
    parser.add_argument("--provider", help="provider prefix if not included in --model (e.g. lmstudio, ollama, google-vertex)")
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

    model = args.model
    if args.provider and model and "/" not in model:
        model = f"{args.provider}/{model}"
    elif args.provider and not model:
        model = args.provider

    options = {
        "model": model, "skill_dir": args.skill_dir, "notes_dir": notes_dir,
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
    delivery_records = []

    session_monitor = monitor_mod.Monitor(notes_dir)
    options["monitor"] = session_monitor
    options["monitor_interval"] = args.monitor_interval

    target = (", ".join(f"parent {parent}" for parent in parents) if parents
              else f"project {owner}/{project}" if owner and project else None)
    lock_info = None
    if not args.allow_concurrent:
        try:
            acquire_run_lock(notes_dir, target)
            check_active_runs()
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
    model_available = (monitor_mod.probe_model(model, options.get("opencode_cmd", "opencode"))
                       if model else None)
    endpoint_url = os.environ.get("LLAMA_CPP_BASE_URL") if args.monitor_endpoint else None
    endpoint_ok = monitor_mod.probe_endpoint(endpoint_url) if endpoint_url else None
    session_monitor.preflight(facts_out, identity=identity_out, exec_login=exec_login,
                              lock=lock_info, model=model, model_available=model_available,
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
    notebook.start(target=target, model=model, hours=args.hours, notes_dir=notes_dir)

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
        if parents:
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
            item = next_item(board, attempted)

        if item is None:
            print(f"[{time.strftime('%X')}] No more actionable items.")
            break
        issue_ref = item.get("url") or item.get("issue") or (str(item["number"]) if item.get("number") is not None else None)
        print(f"[{time.strftime('%X')}] Selected item: {issue_ref} - {item.get('title')}")
        attempted.add(issue_ref)
        published_pr = None
        pending = {}

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
                                             "endpoint": "time-park" if code == 0 else "park-failed"})
                final_states.append(dict(state))
                break
            print(f"[{time.strftime('%X')}] {issue_ref}: next step is {step}")
            if step in ("DONE", "PARKED", "WAITING"):
                print(f"[{time.strftime('%X')}] {issue_ref} reached endpoint state: {step}")
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref,
                                         "pr": (state.get("pr") or {}).get("url"), "endpoint": step})
                final_states.append(dict(state))
                if step == "DONE":
                    mark_throughput()
                    set_board_status(issue_ref, "In review", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))
                break
            if step == "park-blocker":
                pr_url = parked_pr_url(state, published_pr, cli_fn=run_cli, cwd=options.get("cwd"))
                record_park(state["issue"], pr_url, "Exceeded correction limit.")
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked"})
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
                record_park(state["issue"], pr_url, "No progress made in session.")
                delivered.append(issue_ref)
                delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked"})
                break
            previous_states[issue_ref] = curr

            # Update board status to In progress on start of implementation
            if step == "implement-issue":
                set_board_status(issue_ref, "In progress", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))

            worktree = None
            preceding_pr = find_preceding_pr(issue_ref, parent_children, cli_fn=run_cli,
                                             cwd=options.get("cwd"), child_state=state,
                                             force=args.stack) if parent_children else None
            step_options = dict(options)
            step_options["max_turns"] = issue_turn_limit(args.max_turns)
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
                    delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked"})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                if (deadline_time - time.time()) / 60 < args.floor:
                    pr_url = info.get("url") if isinstance(info, dict) else None
                    delivered.append(issue_ref)
                    delivery_records.append({"issue": state.get("issue") or issue_ref,
                                             "pr": pr_url or (state.get("pr") or {}).get("url"),
                                             "endpoint": "ready"})
                    print(f"[{time.strftime('%X')}] {issue_ref} is ready; stopping below the floor before the CI wait.", flush=True)
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
                continue
            elif step == "address-pr-review":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
            elif step == "submit-pr":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
                target_base = f"Target base branch `{preceding_pr['branch']}`. " if preceding_pr else ""
                step_options["extra_text"] = (
                    f"Direct submission: do not read shared reference files or re-verify code. {target_base}"
                    "Compose the final description with `pr body` and mark the PR ready with `pr ready --expect-head` immediately. "
                    "Be direct and concise."
                )
            elif step == "review-changes":
                existing = worktree_status(state["issue"], cwd=options.get("cwd"))
                if existing.get("path"):
                    step_options["session_cwd"] = existing["path"]
                base_ref = preceding_pr['branch'] if preceding_pr else 'origin/main'
                stacked_note = f" This PR is stacked on base `{base_ref}`; hosted CI does not run for non-main targets on this repo. Use local worktree gate checks for the review, and keep the PR a draft until hosted checks run." if preceding_pr else ""
                verdict_rule = " Verdict rules: if '## Blocking findings' is empty or None, verdict MUST be 'clean', even if non-blocking notes or follow-up ideas appear under '## Notes'. Use 'findings' only for actionable blocking defects."

                gate_note = ""
                if not options.get("no_precompute_gates", False):
                    review_wt = prepare_worktree(state["issue"], state.get("title"), owner, project, step_options, cli_fn=run_cli)
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
                model_note = (f" Post the verdict with `review verdict ... --model {options['model']}` or include `model={options['model']}` in a `pr comment` marker."
                              if options.get("model") else "")
                if earlier_blocking > 0:
                    step_options["extra_text"] = (
                        f"Scope: Re-review of correction on HEAD. Focus on the commit diff (`git diff HEAD~1..HEAD` or `git diff {base_ref}...HEAD`) "
                        f"and verifying that the earlier finding is resolved. Do not re-audit unchanged components or pre-load shared reference files.{workspace_note}{model_note}{stacked_note}{verdict_rule}{gate_note} {gate_instruction}{verification_note}"
                    )
                else:
                    step_options["extra_text"] = (
                        "Scope: Review committed changes on HEAD against the issue requirements. "
                        f"Inspect the commit diff (`git diff {base_ref}...HEAD`). {gate_instruction} "
                        f"Post the verdict comment directly with `pr comment`. "
                        f"Do not write new end-to-end integration test suites, browser harnesses, or query session databases.{workspace_note}{model_note}{stacked_note}{verdict_rule}{gate_note}{verification_note}"
                    )
            elif step == "implement-issue":
                worktree = prepare_worktree(state["issue"], state.get("title"), owner, project, step_options, cli_fn=run_cli)
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
                if preceding_pr:
                    directive += (
                        f" Stacked PR: preceding child #{preceding_pr['number']} has an open PR #{preceding_pr['pr']} on branch "
                        f"`{preceding_pr['branch']}`. Base the work on that branch rather than the default branch"
                        + (f", for example `git reset --hard {preceding_pr['branch']}` inside the prepared worktree,"
                           if worktree else "")
                        + f" and set `--base {preceding_pr['branch']}` when the draft PR is created."
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
                if step == "implement-issue":
                    live_preceding = find_preceding_pr(state["issue"], parent_children, cli_fn=run_cli,
                                                       cwd=options.get("cwd"), child_state=state,
                                                       force=args.stack) if parent_children else None
                    return publish_committed(state["issue"], state.get("title"), worktree, state.get("repo"),
                                             notes_dir, step_options,
                                             base_branch=live_preceding["branch"] if live_preceding else None,
                                             cli_fn=run_cli)
                return None

            session_monitor.phase_start("session", issue=state["issue"], step=step,
                                        remaining_minutes=remaining_minutes)
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
                    delivery_records.append({"issue": state.get("issue") or issue_ref, "pr": pr_url, "endpoint": "parked"})
                    final_states.append(dict(state))
                    flush_monitor(state, step, phase_end=True)
                    break
        if args.once:
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

    print(format_run_summary(delivery_records, park_failures, notes_dir, start_time,
                             options.get("cwd"), facts_refresh=facts_refresh,
                             session_monitor=session_monitor), flush=True)
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
