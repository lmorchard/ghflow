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
