"""Tests for the session telemetry parser, especially the compact-tags signal."""

import json
import tempfile
import unittest
from pathlib import Path

import session


def _write_session(directory, command):
    log = Path(directory) / "session.log"
    events = [
        {"type": "step_start", "part": {"type": "step-start"}},
        {
            "type": "tool_use",
            "part": {
                "type": "tool",
                "tool": "shell",
                "state": {"input": {"command": command}},
            },
        },
        {
            "type": "step_finish",
            "part": {
                "type": "step-finish",
                "tokens": {"input": 100, "output": 10, "reasoning": 0},
                "stop": "stop",
            },
        },
    ]
    log.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return log


def _write_tokens_session(directory, turns, name="session.log"):
    log = Path(directory) / name
    events = []
    for tokens in turns:
        events.append({"type": "step_start", "part": {"type": "step-start"}})
        events.append({
            "type": "step_finish",
            "part": {"type": "step-finish", "tokens": tokens, "stop": "stop"},
        })
    log.write_text("\n".join(json.dumps(event) for event in events) + "\n")
    return log


class CachedContextTests(unittest.TestCase):
    """A provider's cached prompt tokens belong in the context reading."""

    def test_context_includes_cache_read_and_write(self):
        tokens = {"input": 100, "output": 10, "reasoning": 0,
                  "cache": {"read": 115000, "write": 2000}}
        with tempfile.TemporaryDirectory() as tmp:
            log = _write_tokens_session(tmp, [tokens], name="session-cached.log")
            parsed = session.parse_session_log(log)
            self.assertEqual(parsed["current_context_tokens"], 117100)
            summary, _ = session.session_summary(log)
            self.assertIn("117.1k", summary["rendered"])
            debrief, _ = session.session_debrief(tmp)
            self.assertIn("117.1k", debrief["table"])

    def test_last_turn_uses_its_own_cache(self):
        first = {"input": 100, "output": 10, "reasoning": 0,
                 "cache": {"read": 115000, "write": 0}}
        last = {"input": 500, "output": 5, "reasoning": 0}
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_tokens_session(tmp, [first, last]))
        self.assertEqual(parsed["current_context_tokens"], 500)

    def test_missing_cache_is_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_session(tmp, "true"))
        self.assertEqual(parsed["current_context_tokens"], 100)


class TagsSignalTests(unittest.TestCase):
    """The tags signal must see the command, not its truncated summary."""

    def test_long_cd_prefix_still_counts_tags_outline(self):
        command = (
            "cd /very/long/worktree/path/that/exceeds/the/truncation/limit/and/more "
            '&& python3 "$GHFLOW_CLI" tags outline tests/test_skills.py'
        )
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_session(tmp, command))
        self.assertEqual(parsed["tool_signals"].get("tags"), 1)

    def test_tags_brief_counts(self):
        command = "cd /x && python3 cli tags brief Foo"
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_session(tmp, command))
        self.assertEqual(parsed["tool_signals"].get("tags"), 1)

    def test_tags_find_counts(self):
        command = "cd /x && python3 cli tags find Foo --refs"
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_session(tmp, command))
        self.assertEqual(parsed["tool_signals"].get("tags"), 1)

    def test_unrelated_tags_command_does_not_count(self):
        command = "cd /x && python3 cli tags --help"
        with tempfile.TemporaryDirectory() as tmp:
            parsed = session.parse_session_log(_write_session(tmp, command))
        self.assertEqual(parsed["tool_signals"].get("tags", 0), 0)


if __name__ == "__main__":
    unittest.main()
