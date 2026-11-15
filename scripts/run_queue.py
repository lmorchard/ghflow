#!/usr/bin/env python3
"""Deterministic runner that drives unattended delivery from the project board."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

DEFAULT_FLOOR_MINUTES = 30
CORRECTION_LIMIT = 2


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
    return out or {}, proc.returncode


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


def next_step(state, correction_limit=CORRECTION_LIMIT):
    """Pure function returning the next operation for an observed issue state."""
    labels = state.get("labels") or []
    if "triage:needs-input" in labels:
        return "PARKED"
    pr = state.get("pr")
    if not pr or not pr.get("url"):
        return "implement-issue"
    current_head = pr.get("head")
    verdicts = state.get("review_verdicts") or []
    head_verdict = next((v for v in verdicts if v.get("head") == current_head), None)
    is_draft = pr.get("is_draft", pr.get("draft", False))
    if is_draft:
        if not head_verdict:
            return "review-changes"
        v_type = (head_verdict.get("verdict") or "").lower()
        if v_type in ("findings", "blocked"):
            earlier_blocking = sum(1 for v in verdicts if v.get("verdict") in ("findings", "blocked"))
            return "park-blocker" if earlier_blocking >= correction_limit else "address-pr-review"
        if v_type == "clean":
            return "submit-pr"
        return "review-changes"

    # PR is ready (not a draft)
    ci = (state.get("ci") or "").lower()
    if ci in ("pending", ""):
        return "wait-ci"
    if ci in ("failing", "failed", "error") or state.get("unresolved_threads"):
        return "address-pr-review"
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
            "is_draft": pr_st.get("is_draft", pr.get("is_draft", False)),
        }
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
    h_out, code = cli_fn(*args, cwd=options.get("cwd"))
    if code != 0:
        return False, f"Handoff creation failed: {h_out}"

    prompt_text = compose_prompt(options["skill_dir"], h_out.get("dispatch_prompt", ""))
    cmd = [options.get("opencode_cmd", "opencode"), "run", "--format", "json",
           "--title", f"Queue runner {step} {stamp}"]
    if options.get("model"):
        cmd += ["--model", options["model"]]
    if options.get("standalone"):
        cmd.append("--standalone")
    cmd.append(prompt_text)
    if shutil.which("caffeinate") and sys.platform == "darwin":
        cmd = ["caffeinate", "-i", *cmd]

    env = dict(os.environ, OPENCODE_DISABLE_AUTOUPDATE="1")
    proc = subprocess.run(cmd, stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          cwd=options.get("cwd"), env=env, timeout=options.get("session_timeout", 3600))
    session_id = None
    if proc.stdout:
        m = re.search(r'"session_id":\s*"([^"]+)"', proc.stdout) or re.search(r'"id":\s*"([^"]+)"', proc.stdout)
        if m:
            session_id = m.group(1)
    if session_id:
        subprocess.run([options.get("opencode_cmd", "opencode"), "session", "delete", session_id],
                       stdin=subprocess.DEVNULL, capture_output=True)
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
    parser.add_argument("--model", help="model override for worker sessions")
    parser.add_argument("--hours", type=float, default=8.0, help="maximum run duration in hours (default 8)")
    parser.add_argument("--floor", type=int, default=DEFAULT_FLOOR_MINUTES, help="minimum minutes required to start a new issue")
    parser.add_argument("--once", action="store_true", help="drive exactly one item to desired state and exit")
    parser.add_argument("--allow-concurrent", action="store_true", help="bypass active session check")
    parser.add_argument("--skill-dir", default=str(Path(__file__).resolve().parent.parent), help="path to ghflow skill root")
    parser.add_argument("--notes-dir", help="custom task notes directory")
    args = parser.parse_args(argv)

    if not args.allow_concurrent:
        check_active_runs()

    owner, project = discover_project(args.project if args.project and "/" in args.project else None)
    if args.owner:
        owner = args.owner
    if args.project and "/" not in args.project:
        project = int(args.project)

    start_time = time.time()
    deadline_time = start_time + args.hours * 3600
    deadline_str = time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(deadline_time))
    notes_dir = Path(args.notes_dir) if args.notes_dir else Path.home() / ".local/state/ghflow/notes" / f"runner-{time.strftime('%Y%m%d-%H%M%S')}"
    notes_dir.mkdir(parents=True, exist_ok=True)

    options = {
        "model": args.model, "skill_dir": args.skill_dir, "notes_dir": notes_dir,
        "deadline": deadline_str, "cwd": os.getcwd(), "standalone": True,
    }
    attempted, delivered = set(), []
    previous_states = {}

    while True:
        if time.time() >= deadline_time:
            break
        board = observe_board(owner, project)
        item = next_item(board, attempted)
        if item is None:
            break
        issue_ref = item.get("issue") or item.get("url") or item.get("number")
        attempted.add(issue_ref)

        # Issue reconciliation loop
        while True:
            remaining_minutes = (deadline_time - time.time()) / 60
            if remaining_minutes < args.floor:
                break
            state = observe_issue(issue_ref)
            step = next_step(state)
            if step in ("DONE", "PARKED", "WAITING"):
                delivered.append(issue_ref)
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

            success, info = run_session(step, state["issue"], notes_dir, options)
            if not success:
                # Retry once in fresh session
                success, info = run_session(step, state["issue"], notes_dir, options)
                if not success:
                    pr_url = (state.get("pr") or {}).get("url") or ""
                    park_issue(state["issue"], pr_url, "blocker", f"Session failed repeatedly: {info}", notes_dir)
                    delivered.append(issue_ref)
                    break
        if args.once:
            break

    if delivered:
        run_cli("queue", "summary", *[str(d) for d in delivered], "--owner", owner, "--project", str(project))
    return 0


if __name__ == "__main__":
    sys.exit(main())
