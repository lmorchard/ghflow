#!/usr/bin/env python3
"""Publish the narrative of an unattended run to a GitHub discussion thread.

The runner owns the mechanics. This module starts or reuses the day's thread,
appends a note for each session, and appends the run result. One short model call
condenses a session log; when that call fails, deterministic facts stand in. A
repository without Discussions, a missing category, or a token without
write:discussion leaves the notebook unavailable, and the run continues.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

DEFAULT_CATEGORY = "lab-notebook"
EXCERPT_CHARS = 12000
SUMMARY_TIMEOUT_SECONDS = 240
SUMMARY_MAX_CHARS = 4000


def session_excerpt(log_path, limit=EXCERPT_CHARS):
    """Return the tail of a session log, or an empty string when it cannot be read."""
    try:
        text = Path(log_path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return ""
    text = text.replace("\x00", "")
    return text[-limit:] if len(text) > limit else text


def parse_text_events(stdout):
    """Join the assistant text parts of OpenCode's JSON event stream."""
    parts = []
    for line in (stdout or "").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        part = event.get("part") if isinstance(event.get("part"), dict) else {}
        text = part.get("text")
        if part.get("type") == "text" and isinstance(text, str):
            parts.append(text)
        elif event.get("type") == "text" and isinstance(event.get("text"), str):
            parts.append(event["text"])
    return "\n".join(parts).strip()


def parse_session_id(stdout):
    """Return the first OpenCode session ID in an event stream, or None."""
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    for line in (stdout or "").splitlines():
        try:
            event = json.loads(line)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        if isinstance(event, dict) and isinstance(event.get("sessionID"), str):
            return event["sessionID"]
    return None


def deterministic_summary(step, issue, success, info, pr_url=None, head=None):
    """Describe a finished session without a model call."""
    outcome = "succeeded" if success else f"failed ({info or 'no detail'})"
    bullets = [f"- Step `{step}` {outcome}."]
    if pr_url:
        bullets.append(f"- PR {pr_url}" + (f" at `{head}`." if head else "."))
    return "\n".join(bullets)


def delete_summary_session(run, options, session_id, print_fn=print):
    """Delete one OpenCode session created by the summary call; never raise."""
    try:
        run([options.get("opencode_cmd", "opencode"), "session", "delete", session_id],
            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=30)
    except Exception as error:
        print_fn(f"[notebook] summary session cleanup failed: {error}")


def summary_prompt(step, issue, success, info, excerpt):
    outcome = "succeeded" if success else f"failed ({info or 'no detail'})"
    return (
        "Summarize one unattended delivery step for a short run notebook entry.\n"
        f"Step: {step}\n"
        f"Issue: {issue}\n"
        f"Outcome: {outcome}\n\n"
        "Session output (JSON events, truncated):\n"
        f"{excerpt}\n\n"
        "Write 3 or 4 Markdown bullet points: what was investigated or changed, test "
        "results, and what comes next. Under 100 words. No heading and no code fence."
    )


def summarize_session(step, issue, success, info, log_path, options, run=subprocess.run,
                      print_fn=print):
    """Return (summary, source) for one session.

    ``source`` is "model" for a model-written summary and "facts" for the
    deterministic fallback. A missing or unreadable log, a missing OpenCode, a
    timeout, a nonzero exit, or empty model text all fall back without raising.
    """
    excerpt = session_excerpt(log_path)
    fallback = deterministic_summary(step, issue, success, info)
    if not excerpt:
        return fallback, "facts"
    cmd = [options.get("opencode_cmd", "opencode"), "run", "--auto", "--format", "json",
           "--title", f"Run notebook summary {time.strftime('%Y%m%d-%H%M%S')}"]
    if options.get("model"):
        cmd += ["--model", options["model"]]
    if options.get("standalone"):
        cmd.append("--standalone")
    cmd.append(summary_prompt(step, issue, success, info, excerpt))
    env = dict(os.environ, OPENCODE_DISABLE_AUTOUPDATE="1")
    try:
        proc = run(cmd, capture_output=True, text=True, timeout=SUMMARY_TIMEOUT_SECONDS,
                   cwd=options.get("cwd"), env=env)
    except Exception as error:
        # A spawn failure, a timeout, or a malformed argument must not stop the run.
        print_fn(f"[notebook] summary model call failed: {error}; using facts")
        session_id = parse_session_id(getattr(error, "output", "") or "")
        if session_id:
            delete_summary_session(run, options, session_id, print_fn)
        return fallback, "facts"
    session_id = parse_session_id(proc.stdout)
    if session_id:
        delete_summary_session(run, options, session_id, print_fn)
    if proc.returncode != 0:
        print_fn(f"[notebook] summary model call exited {proc.returncode}; using facts")
        return fallback, "facts"
    text = parse_text_events(proc.stdout)[:SUMMARY_MAX_CHARS].strip()
    if not text:
        print_fn("[notebook] summary model call returned no text; using facts")
        return fallback, "facts"
    return text, "model"


def post_issue_checkpoint(cli_fn, issue, text, cwd=None, print_fn=print):
    """Post a native checkpoint comment on the issue; never raise."""
    tmp = Path(tempfile.mkdtemp(prefix="ghflow-checkpoint-"))
    try:
        path = tmp / "checkpoint.md"
        path.write_text(text, encoding="utf-8")
        out, code = cli_fn("issue", "comment", str(issue), "--text", str(path), cwd=cwd)
    except Exception as error:
        print_fn(f"[notebook] issue checkpoint failed: {error}")
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if code != 0:
        print_fn(f"[notebook] issue checkpoint failed (exit {code}): {out}")
        return None
    return out


class RunNotebook:
    """One run's discussion thread. The first unavailable answer turns it off."""

    def __init__(self, cli_fn, cwd=None, category=DEFAULT_CATEGORY, title=None,
                 enabled=True, print_fn=print):
        self.cli_fn = cli_fn
        self.cwd = cwd
        self.category = category
        self.title = title or f"Run notebook {time.strftime('%Y-%m-%d')}"
        self.enabled = enabled
        self.unavailable_reason = None
        self.discussion = None
        self.print_fn = print_fn

    @property
    def available(self):
        return self.enabled and self.unavailable_reason is None

    def _post(self, body):
        if not self.available:
            return None
        tmp = Path(tempfile.mkdtemp(prefix="ghflow-notebook-"))
        try:
            path = tmp / "note.md"
            path.write_text(body, encoding="utf-8")
            out, code = self.cli_fn("discussion", "post", "--category", self.category,
                                    "--title", self.title, "--body-file", str(path), cwd=self.cwd)
        except Exception as error:
            self.print_fn(f"[notebook] post failed: {error}")
            return None
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        if code == 3 or (isinstance(out, dict) and out.get("available") is False):
            reason = (out or {}).get("reason") if isinstance(out, dict) else None
            self.unavailable_reason = reason or "discussion notebook unavailable"
            self.print_fn(f"[notebook] unavailable: {self.unavailable_reason}")
            return None
        if code != 0 or not isinstance(out, dict):
            self.print_fn(f"[notebook] post failed (exit {code}): {out}")
            return None
        if out.get("discussion"):
            self.discussion = out["discussion"]
        return out

    def start(self, target=None, model=None, hours=None, notes_dir=None):
        lines = [f"## Run start {time.strftime('%H:%M')}", "",
                 "- Runner: `scripts/run_queue.py`"]
        if target:
            lines.append(f"- Target: {target}")
        if model:
            lines.append(f"- Model: `{model}`")
        if hours is not None:
            lines.append(f"- Budget: {hours:g}h")
        if notes_dir:
            lines.append(f"- Local notes: `{notes_dir}`")
        return self._post("\n".join(lines) + "\n")

    def step(self, step, issue, summary, pr_url=None, head=None):
        lines = [f"### {time.strftime('%H:%M')} — `{step}` — {issue}", "",
                 summary.strip(), ""]
        if pr_url:
            lines.append(f"PR: {pr_url}" + (f" at `{head}`" if head else "") + "\n")
        return self._post("\n".join(lines) + "\n")

    def finish(self, delivered, park_failures, stop_reason=None):
        lines = [f"## Run end {time.strftime('%H:%M')}", "",
                 f"- Delivered or reached an endpoint: {len(delivered or [])}"]
        for item in delivered or []:
            lines.append(f"  - {item}")
        if park_failures:
            lines.append(f"- Park attempts failed: {len(park_failures)}")
            for failure in park_failures:
                lines.append(f"  - {failure.get('issue')}: {failure.get('reason')}")
        if stop_reason:
            lines.append(f"- Stopped: {stop_reason}")
        return self._post("\n".join(lines) + "\n")
