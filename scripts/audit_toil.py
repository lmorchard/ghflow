#!/usr/bin/env python3
"""Audit runner session logs for repeated procedural toil (Three Strikes and You Automate).

Scans session logs, extracts tool invocations and shell commands, normalizes
variable parameters (SHAs, URLs, paths, temp files), and identifies operation
sequences that repeat across distinct sessions.
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SHA_RE = re.compile(r"\b[0-9a-fA-F]{7,40}\b")
PR_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/pull/\d+")
ISSUE_URL_RE = re.compile(r"https://github\.com/[^/\s]+/[^/\s]+/issues/\d+")
WORKTREE_RE = re.compile(r"(?:/[^\s]+/)?\.claude/worktrees/[a-zA-Z0-9_-]+")
TMP_PATH_RE = re.compile(r"(?:/tmp|/var/tmp)/[a-zA-Z0-9_.-]+")
NUM_FLAG_RE = re.compile(r"(--(?:pr-head|pr|issue|project|number|port)\s+)\d+")


def normalize_command(cmd: str) -> str:
    """Normalize variable parameters in a command string for pattern matching."""
    if not cmd:
        return ""
    text = cmd.strip()
    text = PR_URL_RE.sub("<PR_URL>", text)
    text = ISSUE_URL_RE.sub("<ISSUE_URL>", text)
    text = WORKTREE_RE.sub("<WORKTREE_PATH>", text)
    text = TMP_PATH_RE.sub("<TMP_PATH>", text)
    text = NUM_FLAG_RE.sub(r"\g<1><NUM>", text)
    text = SHA_RE.sub("<SHA>", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_session_log(path: Path) -> dict:
    """Extract ordered tool and command operations from a session log file."""
    session_id = path.stem
    step = "unknown"
    parts = path.stem.split("-")
    if len(parts) >= 2 and parts[0] == "session":
        step = parts[1]

    operations = []
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    except OSError:
        return {"session_id": session_id, "step": step, "path": str(path), "operations": []}

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Support OpenCode event stream JSON lines
        if stripped.startswith("{") and stripped.endswith("}"):
            try:
                event = json.loads(stripped)
            except json.JSONDecodeError:
                event = {}
            if event.get("sessionID") and session_id == path.stem:
                session_id = event["sessionID"]
            part = event.get("part") or {}
            ev_type = event.get("type")
            if ev_type == "tool" or part.get("type") == "tool":
                tool_name = part.get("name") or part.get("tool") or event.get("name") or "tool"
                tool_in = (part.get("state") or {}).get("input") or {}
                cmd = tool_in.get("command") or tool_in.get("cmd") or ""
                if cmd:
                    norm = normalize_command(cmd)
                    if norm and (not operations or operations[-1] != norm):
                        operations.append(norm)
                elif tool_name in ("write", "edit", "read", "view"):
                    file_path = tool_in.get("filePath") or tool_in.get("path") or ""
                    norm_path = TMP_PATH_RE.sub("<TMP_PATH>", file_path)
                    entry = f"{tool_name} {norm_path}".strip()
                    if not operations or operations[-1] != entry:
                        operations.append(entry)
        # Support plain text runner logs like: [turn 1] Tool: bash cmd
        elif "[turn " in stripped and "Tool: " in stripped:
            tool_part = stripped.split("Tool: ", 1)[-1].strip()
            for prefix in ("bash ", "exec ", "shell "):
                if tool_part.startswith(prefix):
                    tool_part = tool_part[len(prefix):].strip()
                    break
            norm = normalize_command(tool_part)
            if norm and (not operations or operations[-1] != norm):
                operations.append(norm)

    return {"session_id": session_id, "step": step, "path": str(path), "operations": operations}


def find_session_logs(dirs=None, last=30) -> list[Path]:
    """Locate recent session log files across candidate log directories."""
    candidate_dirs = []
    if dirs:
        candidate_dirs.extend(Path(d) for d in dirs)
    else:
        # Default ghflow runner notes location
        state_notes = Path.home() / ".local/state/ghflow/notes"
        if state_notes.is_dir():
            candidate_dirs.extend(sorted(state_notes.glob("runner-*"), reverse=True)[:5])
        # Local checkout candidate locations
        for rel in (".claude/sessions", "docs/dev-sessions", ".ghflow/sessions"):
            p = Path.cwd() / rel
            if p.is_dir():
                candidate_dirs.append(p)

    all_logs = []
    for d in candidate_dirs:
        if d.is_dir():
            all_logs.extend(d.glob("session-*.log"))
            all_logs.extend(d.glob("**/session-*.log"))

    # Sort newest first by mtime
    all_logs = sorted(set(all_logs), key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)
    return all_logs[:last]


def mine_patterns(sessions: list[dict], min_strikes=3, min_length=2, max_length=5) -> list[dict]:
    """Mine recurring operation subsequences across distinct sessions."""
    # Map normalized tuple sequence -> set of distinct session indices
    sequence_sessions = defaultdict(set)
    sequence_first_seen = {}

    for idx, sess in enumerate(sessions):
        ops = sess.get("operations") or []
        n = len(ops)
        seen_in_this_session = set()
        for length in range(min_length, min(max_length + 1, n + 1)):
            for i in range(n - length + 1):
                seq = tuple(ops[i:i + length])
                if seq not in seen_in_this_session:
                    seen_in_this_session.add(seq)
                    sequence_sessions[seq].add(idx)
                    if seq not in sequence_first_seen:
                        sequence_first_seen[seq] = i

    candidates = [
        {"sequence": list(seq), "session_indices": sorted(indices), "strike_count": len(indices)}
        for seq, indices in sequence_sessions.items()
        if len(indices) >= min_strikes
    ]

    # Sort by strike count descending, then sequence length descending
    candidates.sort(key=lambda c: (c["strike_count"], len(c["sequence"])), reverse=True)

    # Prune sub-sequences that appear in the exact same sessions as a longer sequence
    pruned = []
    for cand in candidates:
        seq_str = " \n ".join(cand["sequence"])
        cand_sessions = set(cand["session_indices"])
        dominated = False
        for kept in pruned:
            kept_str = " \n ".join(kept["sequence"])
            kept_sessions = set(kept["session_indices"])
            if seq_str in kept_str and cand_sessions.issubset(kept_sessions):
                dominated = True
                break
        if not dominated:
            pruned.append(cand)

    # Attach evidence
    patterns = []
    for cand in pruned:
        evidence = []
        for idx in cand["session_indices"]:
            s = sessions[idx]
            evidence.append({
                "session_id": s.get("session_id") or Path(s.get("path", "")).stem,
                "step": s.get("step", "unknown"),
                "path": s.get("path", ""),
            })
        patterns.append({
            "strike_count": cand["strike_count"],
            "sequence": cand["sequence"],
            "evidence": evidence,
        })

    return patterns


def format_markdown_report(patterns: list[dict], scanned_count: int) -> str:
    """Format mined patterns as a readable Markdown report."""
    if not patterns:
        return f"Scanned {scanned_count} session log(s). No repeated operation patterns hit the strike threshold."

    lines = [
        f"# Toil Audit Report ({len(patterns)} pattern(s) across {scanned_count} session(s))\n"
    ]
    for idx, pat in enumerate(patterns, start=1):
        seq = pat["sequence"]
        first_op = seq[0].split()[0] if seq else "toil"
        last_op = seq[-1].split()[0] if seq else "pattern"
        name = f"{first_op} to {last_op} sequence"

        lines.append(f"### Pattern {idx}: {name}")
        lines.append(f"- **Strike Count**: {pat['strike_count']} occurrences")
        lines.append("- **Evidence**:")
        for ev in pat["evidence"][:5]:
            lines.append(f"  - Session `{ev['session_id']}` (step: `{ev['step']}`)")
        if len(pat["evidence"]) > 5:
            lines.append(f"  - ... and {len(pat['evidence']) - 5} more session(s)")
        lines.append("- **The Repeated Sequence**:")
        lines.append("  ```bash")
        for op in seq:
            lines.append(f"  {op}")
        lines.append("  ```\n")

    return "\n".join(lines).strip()


def audit_toil(dirs=None, last=30, min_strikes=3, min_length=2) -> tuple[dict, int]:
    """Execute the toil audit over located session logs."""
    logs = find_session_logs(dirs=dirs, last=last)
    if not logs:
        return {"scanned": 0, "patterns": []}, 0

    sessions = [parse_session_log(p) for p in logs]
    patterns = mine_patterns(sessions, min_strikes=min_strikes, min_length=min_length)
    result = {
        "scanned": len(sessions),
        "patterns": patterns,
    }
    return result, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", action="append", default=[], help="directory to scan for session logs")
    parser.add_argument("--last", type=int, default=30, help="maximum session logs to analyze (default: 30)")
    parser.add_argument("--min-strikes", type=int, default=3, help="minimum distinct sessions required (default: 3)")
    parser.add_argument("--min-length", type=int, default=2, help="minimum sequence length (default: 2)")
    parser.add_argument("--json", action="store_true", help="output structured JSON instead of Markdown")
    args = parser.parse_args(argv)

    result, status = audit_toil(dirs=args.dir, last=args.last, min_strikes=args.min_strikes, min_length=args.min_length)
    if args.json:
        json.dump(result, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        report = format_markdown_report(result.get("patterns") or [], result.get("scanned", 0))
        sys.stdout.write(report + "\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
