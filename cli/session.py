"""Session log inspection, tailing, summary, and debriefing."""

from collections import Counter
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple


DEFAULT_LOG_DIRS = [
    Path.home() / ".local" / "state" / "ghflow" / "notes",
    Path(".ghflow") / "notes",
    Path("."),
]


def find_latest_session_log(base_dir: Optional[Path | str] = None) -> Optional[Path]:
    """Find the most recently modified session log file."""
    search_dirs: List[Path] = []
    if base_dir:
        search_dirs.append(Path(base_dir))
    else:
        search_dirs.extend(DEFAULT_LOG_DIRS)

    candidates: List[Path] = []
    for d in search_dirs:
        if d.is_file() and d.name.endswith(".log"):
            return d
        if d.is_dir():
            candidates.extend(d.glob("session-*.log"))
            candidates.extend(d.glob("**/session-*.log"))

    if not candidates:
        return None

    return max(candidates, key=lambda p: p.stat().st_mtime)


def parse_session_log(log_path: Path | str) -> Dict[str, Any]:
    """Parse an OpenCode JSON-stream session log into structured turn and token telemetry."""
    path = Path(log_path)
    if not path.is_file():
        return {
            "error": f"Log file not found: {path}",
            "turns": [],
            "total_turns": 0,
        }

    session_id = None
    turns: List[Dict[str, Any]] = []
    current_turn: Optional[Dict[str, Any]] = None
    abort_reason: Optional[str] = None

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                ev = json.loads(line)
            except Exception:
                continue

            tp = ev.get("type")
            sid = ev.get("sessionID")
            if sid and not session_id:
                session_id = sid
            if tp == "runner_abort":
                abort_reason = ev.get("reason") or (ev.get("part") or {}).get("reason")
                continue

            part = ev.get("part", {})
            part_type = part.get("type")

            if tp == "step_start" or part_type == "step-start":
                if current_turn:
                    turns.append(current_turn)
                current_turn = {
                    "turn": len(turns) + 1,
                    "session_id": sid or session_id,
                    "tools": [],
                    "text": "",
                    "tokens": {"input": 0, "output": 0, "reasoning": 0},
                    "stop": None,
                }
            elif tp == "text" or part_type == "text":
                text_content = part.get("text", "")
                if current_turn and text_content and not current_turn["text"]:
                    current_turn["text"] = text_content.strip()
            elif tp == "tool_use" or part_type == "tool":
                tool_name = part.get("tool") or part.get("tool_name")
                state = part.get("state", {})
                inp = state.get("input", {})
                summary = ""
                command = ""
                if tool_name == "shell":
                    command = inp.get("command", "") or ""
                    summary = command
                elif tool_name in ("read", "write", "patch", "edit"):
                    summary = inp.get("path", "")
                elif tool_name == "grep":
                    summary = f"{inp.get('pattern', '')} in {inp.get('path', '')}"
                elif inp:
                    summary = str(next(iter(inp.values()))) if isinstance(inp, dict) else str(inp)

                if current_turn and tool_name:
                    current_turn["tools"].append({
                        "tool": tool_name,
                        "summary": summary[:120],
                        "command": command,
                    })
            elif tp == "step_finish" or part_type == "step-finish":
                if current_turn:
                    toks = part.get("tokens", {})
                    cache = toks.get("cache") or {}
                    current_turn["tokens"] = {
                        "input": toks.get("input", 0),
                        "cache_read": cache.get("read", 0) or 0,
                        "cache_write": cache.get("write", 0) or 0,
                        "output": toks.get("output", 0),
                        "reasoning": toks.get("reasoning", 0),
                    }
                    current_turn["stop"] = part.get("stop") or part.get("reason")

    if current_turn:
        turns.append(current_turn)

    total_output = sum(t["tokens"]["output"] for t in turns)
    total_reasoning = sum(t["tokens"]["reasoning"] for t in turns)
    peak_reasoning = max((t["tokens"]["reasoning"] for t in turns), default=0)

    tool_counts = Counter()
    tool_signals = Counter()
    for turn in turns:
        for tool in turn.get("tools") or []:
            name = tool.get("tool") or "unknown"
            tool_counts[name] += 1
            if name == "shell":
                command = (tool.get("command") or tool.get("summary") or "").lower()
                if re.search(r"\btags\s+(find|outline|brief)\b", command):
                    tool_signals["tags"] += 1
                if re.search(r"\b(grep|rg)\b", command):
                    tool_signals["grep"] += 1
                if command.lstrip().startswith("cd ") and ".claude/worktrees" in command:
                    tool_signals["cd_worktree"] += 1
                if "ghflow" in command and " gate" in command:
                    tool_signals["ghflow_gate"] += 1
                if re.search(r"\bmake\s+test\b", command):
                    tool_signals["make_test"] += 1
                if re.search(r"\bmake\s+check\b", command):
                    tool_signals["make_check"] += 1
            elif name == "grep":
                tool_signals["grep"] += 1

    def turn_context(tokens):
        return (int(tokens.get("input") or 0)
                + int(tokens.get("cache_read") or 0)
                + int(tokens.get("cache_write") or 0))

    finished_turns = [t for t in turns if t.get("stop") is not None or turn_context(t["tokens"]) > 0]
    current_context = (turn_context(finished_turns[-1]["tokens"]) if finished_turns
                       else turn_context(turns[-1]["tokens"]) if turns else 0)

    last_turn = turns[-1] if turns else None
    last_stop = last_turn.get("stop") if last_turn else None

    import subprocess
    import time
    age_seconds = time.time() - path.stat().st_mtime
    is_alive = False
    try:
        # The long-lived `opencode serve` process is not a session. Match only a
        # real `opencode run` worker.
        proc = subprocess.run(["pgrep", "-f", "opencode run"], capture_output=True, text=True)
        is_alive = proc.returncode == 0
    except Exception:
        pass

    if last_stop in ("stop", "end_turn"):
        status = "completed"
    elif abort_reason:
        status = f"aborted ({abort_reason})"
    elif peak_reasoning >= 30000 and last_stop != "stop":
        status = "stalled (reasoning loop)"
    elif (age_seconds < 900 or is_alive) and last_stop is None:
        status = "running"
    else:
        status = "finished" if last_stop else "aborted"

    return {
        "log_path": str(path),
        "session_id": session_id,
        "status": status,
        "total_turns": len(turns),
        "current_context_tokens": current_context,
        "total_output_tokens": total_output,
        "total_reasoning_tokens": total_reasoning,
        "peak_reasoning_tokens": peak_reasoning,
        "tool_counts": dict(tool_counts),
        "tool_signals": dict(tool_signals),
        "last_turn": last_turn,
        "turns": turns,
    }


def format_tokens(n: int) -> str:
    """Format token count with k/M suffix."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


def session_tail(log_path: Optional[Path | str] = None, count: int = 5) -> Tuple[Dict[str, Any], int]:
    """Format the latest N turns of an OpenCode session log."""
    target = log_path or find_latest_session_log()
    if not target:
        return {"error": "No session log found."}, 1

    parsed = parse_session_log(target)
    if "error" in parsed:
        return parsed, 1

    turns = parsed["turns"][-count:] if count > 0 else parsed["turns"]
    lines: List[str] = [
        f"Session: {parsed['session_id']} ({parsed['status']}, {parsed['total_turns']} turns total)",
        f"Log:     {parsed['log_path']}",
        "-" * 60,
    ]

    for t in turns:
        toks = t["tokens"]
        tool_strs = [f"{tool['tool']}: {tool['summary']}" for tool in t["tools"]]
        tools_desc = "; ".join(tool_strs) if tool_strs else "(no tool calls)"
        lines.append(f"[Turn {t['turn']}] {tools_desc}")
        lines.append(f"         in={format_tokens(toks['input'])} "
                     f"cache={format_tokens(toks.get('cache_read', 0))}+{format_tokens(toks.get('cache_write', 0))} "
                     f"out={format_tokens(toks['output'])} reasoning={format_tokens(toks['reasoning'])}")
        if t["text"]:
            first_line = t["text"].splitlines()[0][:90]
            lines.append(f"         thought: {first_line}")

    rendered = "\n".join(lines)
    return {
        "success": True,
        "session_id": parsed["session_id"],
        "status": parsed["status"],
        "total_turns": parsed["total_turns"],
        "log_path": parsed["log_path"],
        "turns": turns,
        "rendered": rendered,
    }, 0


def session_summary(log_path: Optional[Path | str] = None) -> Tuple[Dict[str, Any], int]:
    """Format a compact rollup summary of an OpenCode session log."""
    target = log_path or find_latest_session_log()
    if not target:
        return {"error": "No session log found."}, 1

    parsed = parse_session_log(target)
    if "error" in parsed:
        return parsed, 1

    last_turn = parsed.get("last_turn") or {}
    last_tools = [f"{t['tool']}: {t['summary']}" for t in last_turn.get("tools", [])]
    last_tool_desc = "; ".join(last_tools) if last_tools else "none"

    lines: List[str] = [
        f"Session:        {parsed['session_id']}",
        f"Log:            {parsed['log_path']}",
        f"Status:         {parsed['status']} (Turn {parsed['total_turns']})",
        f"Context Window: {format_tokens(parsed['current_context_tokens'])} tokens",
        f"Output Tokens:  {format_tokens(parsed['total_output_tokens'])} tokens",
        f"Reasoning:      {format_tokens(parsed['total_reasoning_tokens'])} tokens (peak turn: {format_tokens(parsed['peak_reasoning_tokens'])})",
        f"Last Action:    {last_tool_desc}",
    ]
    if last_turn.get("text"):
        lines.append(f"Last Thought:   {last_turn['text'].splitlines()[0][:100]}")

    rendered = "\n".join(lines)
    return {
        "success": True,
        "session_id": parsed["session_id"],
        "status": parsed["status"],
        "total_turns": parsed["total_turns"],
        "current_context_tokens": parsed["current_context_tokens"],
        "total_output_tokens": parsed["total_output_tokens"],
        "total_reasoning_tokens": parsed["total_reasoning_tokens"],
        "peak_reasoning_tokens": parsed["peak_reasoning_tokens"],
        "last_action": last_tool_desc,
        "log_path": parsed["log_path"],
        "rendered": rendered,
    }, 0


def session_debrief(dir_path: Optional[Path | str] = None) -> Tuple[Dict[str, Any], int]:
    """Scan session logs in a directory and render a Markdown debrief table."""
    base = Path(dir_path) if dir_path else DEFAULT_LOG_DIRS[0]
    if not base.is_dir():
        # Fall back to checking candidate log dirs
        for d in DEFAULT_LOG_DIRS:
            if d.is_dir():
                base = d
                break

    if not base.is_dir():
        return {"error": f"Log directory not found: {base}"}, 1

    logs = sorted(base.glob("session-*.log"), key=lambda p: p.stat().st_mtime)
    if not logs:
        # Check subdirectories
        logs = sorted(base.glob("**/session-*.log"), key=lambda p: p.stat().st_mtime)

    if not logs:
        return {"error": f"No session-*.log files found in {base}"}, 1

    rows: List[Dict[str, Any]] = []
    for log_file in logs:
        p = parse_session_log(log_file)
        if "error" in p:
            continue
        rows.append({
            "file": log_file.name,
            "session_id": p.get("session_id") or "unknown",
            "status": p.get("status"),
            "turns": p.get("total_turns"),
            "context": p.get("current_context_tokens"),
            "output_tokens": p.get("total_output_tokens"),
            "reasoning_tokens": p.get("total_reasoning_tokens"),
            "peak_reasoning": p.get("peak_reasoning_tokens"),
            "tools": p.get("tool_counts") or {},
            "signals": p.get("tool_signals") or {},
        })

    # Render Markdown table
    header = "| File | Session ID | Status | Turns | Context | Out Tok | Reasoning Tok | Peak R |"
    divider = "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    table_lines = [header, divider]
    for r in rows:
        table_lines.append(
            f"| `{r['file']}` | `{r['session_id'][:12]}...` | {r['status']} | {r['turns']} | "
            f"{format_tokens(r['context'])} | {format_tokens(r['output_tokens'])} | "
            f"{format_tokens(r['reasoning_tokens'])} | {format_tokens(r['peak_reasoning'])} |"
        )
    if rows:
        table_lines.append(
            f"| **Total ({len(rows)})** | | | {sum(r['turns'] for r in rows)} | "
            f"max {format_tokens(max(r['context'] for r in rows))} | "
            f"{format_tokens(sum(r['output_tokens'] for r in rows))} | "
            f"{format_tokens(sum(r['reasoning_tokens'] for r in rows))} | "
            f"max {format_tokens(max(r['peak_reasoning'] for r in rows))} |"
        )

    tool_header = ("| File | Shell | Read | Grep | Edit | Write | Tags | "
                   "cd-worktree | make-test | make-check |")
    tool_divider = ("| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |")
    tool_lines = [tool_header, tool_divider]
    totals = Counter()
    for r in rows:
        tools, signals = r["tools"], r["signals"]
        for key in ("shell", "read", "edit", "write"):
            totals[key] += tools.get(key, 0)
        for key in ("grep", "tags", "cd_worktree", "make_test", "make_check"):
            totals[key] += signals.get(key, 0)
        tool_lines.append(
            f"| `{r['file']}` | {tools.get('shell', 0)} | {tools.get('read', 0)} | "
            f"{signals.get('grep', 0)} | {tools.get('edit', 0)} | {tools.get('write', 0)} | "
            f"{signals.get('tags', 0)} | {signals.get('cd_worktree', 0)} | "
            f"{signals.get('make_test', 0)} | {signals.get('make_check', 0)} |"
        )
    if rows:
        tool_lines.append(
            f"| **Total ({len(rows)})** | {totals['shell']} | {totals['read']} | "
            f"{totals['grep']} | {totals['edit']} | {totals['write']} | "
            f"{totals['tags']} | {totals['cd_worktree']} | "
            f"{totals['make_test']} | {totals['make_check']} |"
        )

    rendered = "\n".join(table_lines)
    return {
        "success": True,
        "directory": str(base),
        "count": len(rows),
        "sessions": rows,
        "table": rendered,
        "tool_table": "\n".join(tool_lines),
        "tool_totals": dict(totals),
    }, 0
