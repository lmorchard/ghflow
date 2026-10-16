"""Summarize synthetic OpenCode 1.x and 2.x exports."""
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import trial_stats

SKILL = "/home/u/.agents/skills/ghflow/references/"


def v1_tool(tool, state_input, time=None, metadata=None):
    state = {"status": "completed", "input": state_input}
    if time:
        state["time"] = time
    if metadata:
        state["metadata"] = metadata
    return {"type": "tool", "tool": tool, "state": state}


def v2_tool(name, state_input, time=None, metadata=None):
    part = {"type": "tool", "name": name, "state": {"status": "completed", "input": state_input}}
    if time:
        part["time"] = time
    if metadata:
        part["state"]["metadata"] = metadata
    return part


def v1_session():
    return {"info": {"id": "ses_a", "title": "Implement #1", "parentID": "ses_root",
                     "time": {"created": 1_000_000, "updated": 1_000_000 + 30 * 60000}},
            "messages": [
                {"info": {"role": "user", "time": {"created": 1_000_000}}, "parts": [{"type": "text", "text": "go"}]},
                {"info": {"role": "assistant", "tokens": {"input": 100, "output": 40, "reasoning": 10, "cache": {"read": 900, "write": 0}}},
                 "parts": [
                     v1_tool("read", {"filePath": SKILL + "tasks/implement-issue.md"}),
                     v1_tool("read", {"filePath": SKILL + "shared/evidence.md"}),
                     v1_tool("read", {"filePath": "/home/u/.agents/skills/ghflow/SKILL.md"}),
                     v1_tool("bash", {"command": 'python3 "$GHFLOW_CLI" exec -- git worktree add .claude/worktrees/x'}),
                     v1_tool("read", {"filePath": SKILL + "tasks/submit-pr.md"}),
                     v1_tool("read", {"filePath": "/repo/src/app.py"}),
                     v1_tool("bash", {"command": "git commit --amend --no-edit && git push --force-with-lease"}),
                     v1_tool("bash", {"command": "make check"}),
                     {"type": "text", "text": "Model ollama/qwen3-coder:30b is configured."},
                 ]},
            ]}


def v2_session():
    return {"info": {"id": "ses_root", "title": "Unattended burndown",
                     "time": {"created": 500_000, "updated": 500_000 + 90 * 60000}},
            "messages": [
                {"type": "assistant", "tokens": {"input": 50, "output": 20, "reasoning": 0, "cache": {"read": 2000, "write": 10}},
                 "content": [
                     v2_tool("shell", {"command": "date"}),
                     v2_tool("read", {"path": SKILL + "tasks/burndown-ready-queue.md"}),
                     v2_tool("subagent", {"description": "Implement #1", "prompt": "x" * 120},
                             time={"created": 1_000_000, "ran": 1_000_100, "completed": 1_000_000 + 30 * 60000},
                             metadata={"sessionID": "ses_a"}),
                 ]},
            ]}


class TrialStatsTests(unittest.TestCase):
    def test_v1_worker_counts(self):
        stats = trial_stats.session_stats(v1_session(), watch=("ollama/qwen3-coder:30b",))
        self.assertEqual(stats["minutes"], 30.0)
        self.assertEqual((stats["turns"], stats["output_tokens"], stats["max_context"]), (1, 50, 1000))
        self.assertEqual(stats["reference_reads"], ["tasks/implement-issue.md", "shared/evidence.md", "tasks/submit-pr.md"])
        self.assertEqual(stats["references_before_worktree"], 2)
        self.assertEqual(stats["other_reads"], ["/repo/src/app.py"])
        self.assertEqual((stats["amends"], stats["force_pushes"]), (1, 1))
        self.assertEqual(stats["shell"], {"ghflow": 1, "git": 1, "make": 1})
        self.assertEqual(stats["watch"]["ollama/qwen3-coder:30b"], 1)

    def test_v2_coordinator_dispatch_timeline(self):
        stats = trial_stats.session_stats(v2_session())
        self.assertEqual(stats["max_context"], 2060)
        self.assertEqual(stats["shell"], {"date": 1})
        self.assertIsNone(stats["references_before_worktree"])
        (dispatch,) = stats["dispatches"]
        self.assertEqual((dispatch["minutes"], dispatch["prompt_chars"], dispatch["child"]), (30.0, 120, "ses_a"))

    def test_main_orders_sessions_by_start_and_renders_tables(self):
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, "session-ses_a.json").write_text(json.dumps(v1_session()))
            Path(directory, "session-ses_root.json").write_text(json.dumps(v2_session()))
            out = io.StringIO()
            with redirect_stdout(out):
                status = trial_stats.main([directory])
        self.assertEqual(status, 0)
        text = out.getvalue()
        self.assertLess(text.index("| Unattended burndown |"), text.index("| Implement #1 |"))
        self.assertIn("Dispatches from Unattended burndown:", text)

    def test_empty_directory_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(trial_stats.main([directory]), 1)


if __name__ == "__main__":
    unittest.main()
