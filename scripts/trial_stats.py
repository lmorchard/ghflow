#!/usr/bin/env python3
"""Summarize an exported OpenCode session tree for a trial record.

Reads the session-*.json files that export-opencode-sessions.py writes, in the
OpenCode 1.x or 2.x schema, and reports per-session times, output tokens,
largest context, reference reads, shell command categories, amends and force
pushes, and the coordinator's dispatch timeline. It reads files only.

Usage: python3 scripts/trial_stats.py EXPORT_DIR [--watch TEXT ...] [--json]
"""

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

DISPATCH_TOOLS = ("task", "subagent")
SHELL_TOOLS = ("bash", "shell")
REFERENCE = re.compile(r"/references/(?:tasks|shared)/[^/]+\.md$|/references/cli\.md$")
SKILL_FILE = re.compile(r"/skills/[^/]+/")
WORKTREE = re.compile(r"\bworktree (?:add|create)\b")
AMEND = re.compile(r"\bcommit\b[^|;&]*--amend\b")
FORCE = re.compile(r"\bpush\b[^|;&]*(?:--force\b|--force-with-lease\b|\s-f\b)")
SHELL_KINDS = (
    ("ghflow", re.compile(r"GHFLOW_CLI|ghflow\.py")),
    ("gh", re.compile(r"(?:^|[;&|(]\s*|\s)gh\s")),
    ("git", re.compile(r"(?:^|[;&|(]\s*|\s)git\s")),
    ("make", re.compile(r"(?:^|[;&|(]\s*|\s)(?:make|uv run|pytest|npm)\b")),
    ("date", re.compile(r"(?:^|[;&|(]\s*|\s)date\b")),
)


def message_parts(message):
    """Return a message's parts: `parts` in OpenCode 1.x, `content` in 2.x."""
    parts = message.get("parts")
    if parts is None:
        parts = message.get("content")
    return parts if isinstance(parts, list) else []


def message_info(message):
    """Return the message metadata: `info` in 1.x, the message itself in 2.x."""
    return message.get("info") if isinstance(message.get("info"), dict) else message


def tool_name(part):
    return str(part.get("tool") or part.get("name") or "").lower()


def tool_input(part):
    return (part.get("state") or {}).get("input") or {}


def span(time_dict):
    """Return (start_ms, end_ms) from a 1.x {start, end}, a 2.x {created, completed}, or a session {created, updated} time."""
    time_dict = time_dict or {}
    return (time_dict.get("start") or time_dict.get("created"),
            time_dict.get("end") or time_dict.get("completed") or time_dict.get("updated"))


def local(ms):
    return datetime.fromtimestamp(ms / 1000).strftime("%H:%M") if ms else ""


def minutes(start, end):
    return round((end - start) / 60000, 1) if start and end else None


def shell_kind(command):
    for kind, pattern in SHELL_KINDS:
        if pattern.search(command):
            return kind
    return "other"


def session_stats(data, watch=()):
    info = data.get("info") or {}
    created, updated = span(info.get("time"))
    stats = {"id": info.get("id"), "title": info.get("title", ""), "parent": info.get("parentID") or "",
             "start": local(created), "end": local(updated), "minutes": minutes(created, updated),
             "turns": 0, "output_tokens": 0, "max_context": 0, "reference_reads": [], "references_before_worktree": None,
             "other_reads": [], "shell": {}, "amends": 0, "force_pushes": 0, "dispatches": [],
             "watch": {text: 0 for text in watch}}
    worktree_seen = False
    for message in data.get("messages", []):
        meta = message_info(message)
        role = meta.get("role") or meta.get("type")
        if role == "assistant":
            stats["turns"] += 1
            tokens = meta.get("tokens") or {}
            cache = tokens.get("cache") or {}
            stats["output_tokens"] += (tokens.get("output") or 0) + (tokens.get("reasoning") or 0)
            context = (tokens.get("input") or 0) + (cache.get("read") or 0) + (cache.get("write") or 0)
            stats["max_context"] = max(stats["max_context"], context)
        for part in message_parts(message):
            if watch and part.get("type") in ("text", "reasoning", "tool"):
                blob = part.get("text") or json.dumps(tool_input(part))
                for text in watch:
                    stats["watch"][text] += blob.count(text)
            if part.get("type") != "tool":
                continue
            name, args = tool_name(part), tool_input(part)
            if name == "read":
                path = str(args.get("filePath") or args.get("path") or "")
                if REFERENCE.search(path):
                    stats["reference_reads"].append(path.split("/references/")[-1])
                elif not SKILL_FILE.search(path):
                    stats["other_reads"].append(path)
            elif name in SHELL_TOOLS:
                command = str(args.get("command") or "")
                kind = shell_kind(command)
                stats["shell"][kind] = stats["shell"].get(kind, 0) + 1
                stats["amends"] += bool(AMEND.search(command))
                stats["force_pushes"] += bool(FORCE.search(command))
                if not worktree_seen and WORKTREE.search(command):
                    worktree_seen = True
                    stats["references_before_worktree"] = len(stats["reference_reads"])
            elif name in DISPATCH_TOOLS:
                state = part.get("state") or {}
                start, end = span(state.get("time") or part.get("time"))
                metadata = state.get("metadata") or {}
                stats["dispatches"].append({"description": args.get("description", ""), "start": local(start), "end": local(end),
                                            "minutes": minutes(start, end), "prompt_chars": len(str(args.get("prompt") or "")),
                                            "child": metadata.get("sessionID") or metadata.get("sessionId") or ""})
    return stats


def load_exports(directory):
    sessions = []
    for path in sorted(Path(directory).glob("session-*.json")):
        sessions.append(json.loads(path.read_text()))
    sessions.sort(key=lambda d: span((d.get("info") or {}).get("time"))[0] or 0)
    return sessions


def render(all_stats, watch=()):
    lines = ["| Session | Start | End | Minutes | Turns | Output tokens | Max context | Refs | Refs before worktree | Other reads | Amends | Force pushes |",
             "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for s in all_stats:
        before = "" if s["references_before_worktree"] is None else s["references_before_worktree"]
        lines.append(f"| {s['title']} | {s['start']} | {s['end']} | {s['minutes']} | {s['turns']} | {s['output_tokens']:,} | "
                     f"{s['max_context']:,} | {len(s['reference_reads'])} | {before} | {len(s['other_reads'])} | {s['amends']} | {s['force_pushes']} |")
    kinds = sorted({k for s in all_stats for k in s["shell"]})
    lines += ["", "| Session | " + " | ".join(kinds) + " |", "| --- |" + " ---: |" * len(kinds)]
    for s in all_stats:
        lines.append(f"| {s['title']} | " + " | ".join(str(s["shell"].get(k, 0)) for k in kinds) + " |")
    if watch:
        lines += ["", "| Session | " + " | ".join(f"`{w}`" for w in watch) + " |", "| --- |" + " ---: |" * len(watch)]
        for s in all_stats:
            lines.append(f"| {s['title']} | " + " | ".join(str(s["watch"][w]) for w in watch) + " |")
    for s in all_stats:
        if s["dispatches"]:
            lines += ["", f"Dispatches from {s['title']}:", "", "| Start | End | Minutes | Prompt chars | Description |",
                      "| --- | --- | ---: | ---: | --- |"]
            for d in s["dispatches"]:
                lines.append(f"| {d['start']} | {d['end']} | {d['minutes']} | {d['prompt_chars']:,} | {d['description']} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("directory", help="directory of session-*.json exports")
    parser.add_argument("--watch", action="append", default=[], metavar="TEXT",
                        help="count mentions of TEXT in each session, such as a configured default model")
    parser.add_argument("--json", action="store_true", help="print JSON instead of Markdown tables")
    args = parser.parse_args(argv)
    sessions = load_exports(args.directory)
    if not sessions:
        sys.stderr.write(f"No session-*.json files in {args.directory}\n")
        return 1
    all_stats = [session_stats(data, args.watch) for data in sessions]
    if args.json:
        json.dump(all_stats, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render(all_stats, args.watch))
    return 0


if __name__ == "__main__":
    sys.exit(main())
