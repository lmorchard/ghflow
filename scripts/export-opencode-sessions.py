#!/usr/bin/env python3
"""Export an OpenCode session and every subagent session it dispatched.

OpenCode 1.x writes one session with `opencode export SESSION_ID`; 2.x with
`opencode session export SESSION_ID`. A coordinator's dispatch calls (`task` in
1.x, `subagent` in 2.x) name their child sessions in the tool part metadata, so
this script follows them and writes the whole tree into one directory with an
index. Run it from the project checkout the sessions belong to.
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


class ExportError(Exception):
    """OpenCode returned no usable session data."""


def run_opencode(args, stdout=None):
    """Run opencode; with stdout=None return its output, else stream it to that file object.

    `opencode export` truncates output above about 64 KB when stdout is a pipe,
    so exports go straight to a file.
    """
    try:
        result = subprocess.run(["opencode", *args], text=True, stdout=stdout or subprocess.PIPE,
                                stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        raise ExportError("opencode is not on PATH")
    except subprocess.CalledProcessError as error:
        raise ExportError(f"opencode {' '.join(args)} failed: {error.stderr.strip()}")
    return result.stdout


EXPORT_COMMANDS = (["session", "export"], ["export"])


def export_session(session_id, out_dir):
    """Write one session export to disk and return the parsed JSON.

    Tries the 2.x command first and falls back to the 1.x command.
    """
    path = out_dir / f"session-{session_id}.json"
    last_error = None
    for command in EXPORT_COMMANDS:
        try:
            with path.open("w") as handle:
                run_opencode([*command, session_id], stdout=handle)
            break
        except ExportError as error:
            last_error = error
    else:
        path.unlink(missing_ok=True)
        raise last_error
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as error:
        raise ExportError(f"export of {session_id} is not valid JSON: {error}")
    if not isinstance(data, dict) or data.get("info", {}).get("id") != session_id:
        raise ExportError(f"export of {session_id} does not describe that session")
    return data


DISPATCH_TOOLS = ("task", "subagent")


def message_parts(message):
    """Return a message's parts: `parts` in OpenCode 1.x, `content` in 2.x."""
    parts = message.get("parts")
    if parts is None:
        parts = message.get("content")
    return parts if isinstance(parts, list) else []


def task_calls(data):
    """Return (description, child_id) for each dispatch tool call."""
    calls = []
    for message in data.get("messages", []):
        for part in message_parts(message):
            name = str(part.get("tool") or part.get("name") or "").lower()
            if part.get("type") != "tool" or name not in DISPATCH_TOOLS:
                continue
            state = part.get("state") or {}
            metadata = state.get("metadata") or {}
            description = (state.get("input") or {}).get("description", "")
            calls.append((description, metadata.get("sessionId") or metadata.get("sessionID")))
    return calls


def child_session_ids(data):
    """Return the child session IDs named by dispatch tool calls, in first-seen order."""
    children = []
    for _, child in task_calls(data):
        if child and child not in children:
            children.append(child)
    return children


def pick_session(sessions, query):
    """Return the one session whose title contains query, or raise with the matches."""
    if query.startswith("ses_"):
        return query
    matches = [s for s in sessions if query.lower() in str(s.get("title", "")).lower()]
    if len(matches) == 1:
        return matches[0]["id"]
    if not matches:
        raise ExportError(f"no session title contains {query!r}")
    listing = "\n".join(f"  {s['id']}  {s.get('title', '')}" for s in matches)
    raise ExportError(f"{len(matches)} session titles contain {query!r}; pass an ID:\n{listing}")


def resolve_session(query):
    if query.startswith("ses_"):
        return query
    text = run_opencode(["session", "list", "--format", "json"])
    try:
        sessions = json.loads(text)
    except json.JSONDecodeError as error:
        raise ExportError(f"session list is not valid JSON: {error}")
    return pick_session(sessions, query)


def local_time(epoch_ms):
    if not epoch_ms:
        return ""
    return datetime.fromtimestamp(epoch_ms / 1000).strftime("%Y-%m-%d %H:%M")


def index_rows(exports):
    """Return index rows (id, parent, title, created, updated, messages, task calls)."""
    rows = []
    for session_id, data in exports:
        info = data.get("info", {})
        time = info.get("time") or {}
        rows.append({
            "id": session_id,
            "parent": info.get("parentID") or "",
            "title": info.get("title", ""),
            "created": local_time(time.get("created")),
            "updated": local_time(time.get("updated")),
            "messages": len(data.get("messages", [])),
            "task_calls": len(task_calls(data)),
        })
    return rows


def render_index(rows, exports):
    lines = ["# Exported OpenCode sessions", "",
             "| Session | Parent | Title | Created | Updated | Messages | Task calls | File |",
             "| --- | --- | --- | --- | --- | ---: | ---: | --- |"]
    for row in rows:
        lines.append(
            f"| `{row['id']}` | `{row['parent']}` | {row['title']} | {row['created']} | "
            f"{row['updated']} | {row['messages']} | {row['task_calls']} | "
            f"`session-{row['id']}.json` |")
    lines.append("")
    lines.append("## Task calls")
    lines.append("")
    for session_id, data in exports:
        calls = task_calls(data)
        if not calls:
            continue
        lines.append(f"From `{session_id}`:")
        lines.append("")
        for description, child in calls:
            lines.append(f"- {description or '(no description)'} → `{child or 'unknown'}`")
        lines.append("")
    return "\n".join(lines)


def export_tree(root_id, out_dir):
    out_dir.mkdir(parents=True, exist_ok=True)
    exports = []
    queue = [root_id]
    seen = set()
    while queue:
        session_id = queue.pop(0)
        if session_id in seen:
            continue
        seen.add(session_id)
        data = export_session(session_id, out_dir)
        exports.append((session_id, data))
        queue.extend(child for child in child_session_ids(data) if child not in seen)
    rows = index_rows(exports)
    (out_dir / "index.md").write_text(render_index(rows, exports))
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("session", help="session ID (ses_...) or a unique part of the session title")
    parser.add_argument("--out", default="opencode-sessions",
                        help="directory for session-ID.json files and index.md (default: opencode-sessions)")
    args = parser.parse_args(argv)
    try:
        root_id = resolve_session(args.session)
        rows = export_tree(root_id, Path(args.out))
    except ExportError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    for row in rows:
        print(f"{row['id']}\t{row['parent'] or '-'}\t{row['messages']} messages\t{row['title']}")
    print(f"wrote {len(rows)} sessions and index.md to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
