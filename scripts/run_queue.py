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

DEFAULT_FLOOR_MINUTES = 30
CORRECTION_LIMIT = 2
DEFAULT_MAX_TURNS = 100
DEFAULT_SESSION_TIMEOUT = 5400
MAX_DEGENERATE_REASONING = 16000


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
    projects = [p for p in data.get("projectsV2") or [] if isinstance(p, dict) and not p.get("closed")]
    if len(projects) == 1:
        proj = projects[0]
        owner = ((proj.get("owner") or {}).get("login")) or ""
        number = proj.get("number")
        if owner and number is not None:
            return owner, int(number)
    if not projects:
        raise RuntimeError("No open projects found for repository. Pass --project OWNER/NUMBER.")
    names = [f"{(p.get('owner') or {}).get('login')}/{p.get('number')} ({p.get('title')})" for p in projects]
    raise RuntimeError(f"Multiple open projects found: {', '.join(names)}. Pass --project OWNER/NUMBER.")


def check_active_runs(opencode_cmd="opencode"):
    """Raise RuntimeError if an unattended session was active in the last 30 minutes."""
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
        raise RuntimeError("An unattended burndown session was active in the last 30 minutes:\n  " +
                           "\n  ".join(active) + "\nPass --allow-concurrent to override.")


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
    head_verdict = next((v for v in verdicts if v.get("head") == current_head), None)
    verdict_blocking = head_verdict and (head_verdict.get("verdict") in ("findings", "blocked"))
    verdict_clean = head_verdict and (head_verdict.get("verdict") == "clean")

    has_blocking_feedback = bool(changes_requested) or verdict_blocking
    earlier_blocking = sum(1 for r in reviews if r.get("state") == "CHANGES_REQUESTED") + \
                       sum(1 for v in verdicts if v.get("verdict") in ("findings", "blocked"))

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
    if ci in ("pending", ""):
        return "wait-ci"
    if ci in ("failing", "failed", "error") or state.get("unresolved_threads"):
        return "address-pr-review"
    if has_blocking_feedback:
        return "park-blocker" if earlier_blocking >= correction_limit else "address-pr-review"
    if state.get("pending_review_requests"):
        return "WAITING"
    if ci in ("green", "passed"):
        return "DONE"
    return "DONE"


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
        "labels": issue.get("labels") or [],
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


def next_item_for_parent(children, attempted=None, cli_fn=run_cli, cwd=None):
    """Select the next child item from a parent issue's sub-issues."""
    attempted = attempted or set()
    for child in children:
        if child.get("state") == "CLOSED":
            continue
        ref = child.get("url") or child.get("number")
        if ref in attempted or child.get("number") in attempted:
            continue
        st = observe_issue(ref, cli_fn=cli_fn, cwd=cwd)
        if "triage:needs-input" in (st.get("labels") or []):
            continue
        step = next_step(st)
        if step not in ("DONE", "PARKED", "WAITING") and st.get("pr"):
            return child

    for child in children:
        if child.get("state") == "CLOSED":
            continue
        ref = child.get("url") or child.get("number")
        if ref in attempted or child.get("number") in attempted:
            continue
        st = observe_issue(ref, cli_fn=cli_fn, cwd=cwd)
        if "triage:needs-input" in (st.get("labels") or []):
            continue
        step = next_step(st)
        if step in ("DONE", "PARKED", "WAITING"):
            continue
        return child
    return None


def find_preceding_pr(child_ref, children, cli_fn=run_cli, cwd=None):
    """Find the immediate preceding child with an open unmerged PR for branch stacking."""
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

    for c in reversed(children[:idx]):
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

def compose_prompt(skill_dir, handoff_prompt):
    """Compose the prompt from SKILL.md body without YAML frontmatter and the handoff prompt."""
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


def run_session(step, issue_url, notes_dir, options, cli_fn=run_cli):
    """Create a handoff and execute one OpenCode session."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    handoff_file = notes_dir / f"handoff-{step}-{stamp}.md"
    args = ["handoff", step, issue_url, "--out", str(handoff_file)]
    if step == "review-changes":
        args.append("--verdict")
    if options.get("model"):
        args += ["--review-plan", f"model {options['model']}"]
    if options.get("deadline"):
        args += ["--deadline", str(options["deadline"])]
    if options.get("extra_text"):
        extra_file = notes_dir / f"directive-{step}-{stamp}.md"
        extra_file.write_text(options["extra_text"], encoding="utf-8")
        args += ["--extra", str(extra_file)]
    h_out, code = cli_fn(*args, cwd=options.get("cwd"))
    if code != 0:
        return False, f"Handoff creation failed: {h_out}"

    prompt_text = compose_prompt(options["skill_dir"], h_out.get("dispatch_prompt", ""))
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
    session_log = notes_dir / f"session-{step}-{stamp}.log"
    print(f"[{time.strftime('%X')}] Logging session output to {session_log}")
    log_fp = open(session_log, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, cwd=options.get("cwd"), env=env, bufsize=1)
    session_id = None
    step_num = 0
    max_turns = options.get("max_turns", DEFAULT_MAX_TURNS)
    timeout_sec = options.get("session_timeout", DEFAULT_SESSION_TIMEOUT)
    start_ts = time.time()
    abort_reason = None

    def process_line(line_str):
        nonlocal session_id, step_num, abort_reason
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
            print(f"[{time.strftime('%X')}] [turn {step_num}] Step finish (in: {in_tok}, out: {out_tok} tokens)", flush=True)
            if out_tok == 0 and (reason_tok >= MAX_DEGENERATE_REASONING or reason == "length"):
                abort_reason = f"Session stalled in reasoning loop ({reason_tok} reasoning tokens, 0 output)"
        elif ev_type == "error":
            err = event.get("error") or part.get("error") or {}
            if isinstance(err, dict) and err.get("type") == "output-limit":
                abort_reason = f"Session output limit exceeded: {err.get('message', 'output truncated')}"

    try:
        has_fd = hasattr(proc.stdout, "fileno")
        if has_fd:
            while True:
                if time.time() - start_ts > timeout_sec:
                    abort_reason = f"Session exceeded timeout ({timeout_sec}s)"
                    break
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
        log_fp.close()

    if session_id:
        subprocess.run([options.get("opencode_cmd", "opencode"), "session", "delete", session_id],
                       stdin=subprocess.DEVNULL, capture_output=True)
    if abort_reason:
        return False, abort_reason
    return proc.returncode == 0, session_id or ""


def park_issue(issue_url, pr_url, kind, text_or_reason, notes_dir, cli_fn=run_cli, cwd=None):
    """Park an issue with ghflow park."""
    text_file = notes_dir / f"park-{kind}-{time.strftime('%Y%m%d-%H%M%S')}.md"
    text_file.write_text(f"## Parked ({kind})\n\n{text_or_reason}\n", encoding="utf-8")
    return cli_fn("park", issue_url, "--pr", pr_url, "--kind", kind, "--text", str(text_file), cwd=cwd)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Deterministic runner for unattended delivery from the project board.")
    parser.add_argument("--owner", help="project board owner login")
    parser.add_argument("--project", help="project board number or OWNER/NUMBER")
    parser.add_argument("--parent", help="parent issue number, URL, or OWNER/REPO#NUMBER to burndown its sub-issues")
    parser.add_argument("--model", help="model override for worker sessions, in OpenCode's provider/model format (e.g. lmstudio/qwen3.8-27b-mlx@4bit)")
    parser.add_argument("--provider", help="provider prefix if not included in --model (e.g. lmstudio, ollama, google-vertex)")
    parser.add_argument("--hours", type=float, default=8.0, help="maximum run duration in hours (default 8)")
    parser.add_argument("--floor", type=int, default=DEFAULT_FLOOR_MINUTES, help="minimum minutes required to start a new issue")
    parser.add_argument("--once", action="store_true", help="drive exactly one item to desired state and exit")
    parser.add_argument("--allow-concurrent", action="store_true", help="bypass active session check")
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parent.parent), help="path to ghflow skill root")
    parser.add_argument("--notes-dir", help="custom task notes directory")
    parser.add_argument("--max-turns", type=int, default=DEFAULT_MAX_TURNS, help="maximum turns per session (default 100)")
    parser.add_argument("--session-timeout", type=int, default=DEFAULT_SESSION_TIMEOUT, help="maximum seconds per session (default 5400)")
    args = parser.parse_args(argv)

    if not args.allow_concurrent:
        check_active_runs()

    owner = args.owner
    project = None
    if args.project:
        if "/" in args.project:
            owner, project = discover_project(args.project)
        else:
            project = int(args.project)

    if not args.parent and not project:
        owner, project = discover_project()
        if args.owner:
            owner = args.owner
    elif args.parent and not project:
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
    }
    attempted, delivered = set(), []
    previous_states = {}

    parent_children = None
    while True:
        if time.time() >= deadline_time:
            break
        if args.parent:
            print(f"[{time.strftime('%X')}] Reading parent issue {args.parent}...")
            parent_data = observe_parent(args.parent, cwd=options.get("cwd"))
            parent_children = parent_data.get("children") or []
            item = next_item_for_parent(parent_children, attempted, cli_fn=run_cli, cwd=options.get("cwd"))
        else:
            print(f"[{time.strftime('%X')}] Reading board for project {owner}/{project}...")
            board = observe_board(owner, project)
            item = next_item(board, attempted)

        if item is None:
            print(f"[{time.strftime('%X')}] No more actionable items.")
            break
        issue_ref = item.get("url") or item.get("issue") or (str(item["number"]) if item.get("number") is not None else None)
        print(f"[{time.strftime('%X')}] Selected item: {issue_ref} - {item.get('title')}")
        attempted.add(issue_ref)
        # Issue reconciliation loop
        while True:
            remaining_minutes = (deadline_time - time.time()) / 60
            if remaining_minutes < args.floor:
                print(f"[{time.strftime('%X')}] Time budget floor reached ({remaining_minutes:.1f}m < {args.floor}m). Stopping.")
                break
            state = observe_issue(issue_ref)
            step = next_step(state)
            print(f"[{time.strftime('%X')}] {issue_ref}: next step is {step}")
            if step in ("DONE", "PARKED", "WAITING"):
                print(f"[{time.strftime('%X')}] {issue_ref} reached endpoint state: {step}")
                delivered.append(issue_ref)
                if step == "DONE":
                    set_board_status(issue_ref, "In review", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))
                break
            if step == "park-blocker":
                pr_url = (state.get("pr") or {}).get("url") or ""
                park_issue(state["issue"], pr_url, "blocker", "Exceeded correction limit.", notes_dir)
                delivered.append(issue_ref)
                break
            if step == "wait-ci":
                time.sleep(15)
                continue

            prev = previous_states.get(issue_ref)
            curr = (step, (state.get("pr") or {}).get("head"), (state.get("review_verdicts") or [{}])[-1].get("verdict"))
            if prev == curr:
                pr_url = (state.get("pr") or {}).get("url") or ""
                park_issue(state["issue"], pr_url, "blocker", "No progress made in session.", notes_dir)
                delivered.append(issue_ref)
                break
            previous_states[issue_ref] = curr

            # Update board status to In progress on start of implementation
            if step == "implement-issue":
                set_board_status(issue_ref, "In progress", owner, project, cli_fn=run_cli, cwd=options.get("cwd"))

            preceding_pr = find_preceding_pr(issue_ref, parent_children, cli_fn=run_cli, cwd=options.get("cwd")) if parent_children else None
            step_options = dict(options)
            earlier_blocking = sum(1 for r in (state.get("reviews") or []) if r.get("state") == "CHANGES_REQUESTED") + \
                               sum(1 for v in (state.get("review_verdicts") or []) if v.get("verdict") in ("findings", "blocked"))
            if step == "submit-pr":
                target_base = f"Target base branch `{preceding_pr['branch']}`. " if preceding_pr else ""
                step_options["extra_text"] = (
                    f"Direct submission: do not read shared reference files or re-verify code. {target_base}"
                    "Compose the final description with `pr body` and mark the PR ready with `pr ready --expect-head` immediately. "
                    "Be direct and concise."
                )
            elif step == "review-changes":
                base_ref = preceding_pr['branch'] if preceding_pr else 'origin/main'
                if earlier_blocking > 0:
                    step_options["extra_text"] = (
                        f"Scope: Re-review of correction on HEAD. Focus on the commit diff (`git diff HEAD~1..HEAD` or `git diff {base_ref}...HEAD`) "
                        "and verifying that the earlier finding is resolved. Do not re-audit unchanged components or pre-load shared reference files."
                    )
                else:
                    step_options["extra_text"] = (
                        "Scope: Review committed changes on HEAD against the issue requirements. "
                        f"Inspect the commit diff (`git diff {base_ref}...HEAD`), run existing project test gates (`make check`, `make test`), "
                        "and post the verdict comment directly with `pr comment`. "
                        "Do not write new end-to-end integration test suites, browser harnesses, or query session databases."
                    )
            elif step == "implement-issue" and preceding_pr:
                step_options["extra_text"] = (
                    f"Stacked PR: Preceding child #{preceding_pr['number']} has an open PR #{preceding_pr['pr']} on branch `{preceding_pr['branch']}`. "
                    f"Base your implementation on branch `{preceding_pr['branch']}` (`git checkout -b <branch> {preceding_pr['branch']}`) rather than `origin/main`. "
                    f"When creating the draft PR, set `--base {preceding_pr['branch']}`."
                )
            print(f"[{time.strftime('%X')}] Starting {step} session for {issue_ref}...")
            success, info = run_session(step, state["issue"], notes_dir, step_options)
            print(f"[{time.strftime('%X')}] Session finished (success={success}, id={info})")
            if not success:
                print(f"[{time.strftime('%X')}] Session failed, retrying once in fresh session...")
                success, info = run_session(step, state["issue"], notes_dir, step_options)
                if not success:
                    pr_url = (state.get("pr") or {}).get("url") or ""
                    park_issue(state["issue"], pr_url, "blocker", f"Session failed repeatedly: {info}", notes_dir)
                    delivered.append(issue_ref)
                    break
        if args.once:
            break

    if delivered and owner and project:
        run_cli("queue", "summary", *[str(d) for d in delivered], "--owner", owner, "--project", str(project))
    elif delivered:
        print(f"[{time.strftime('%X')}] Burndown complete. Delivered items: {', '.join(str(d) for d in delivered)}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
