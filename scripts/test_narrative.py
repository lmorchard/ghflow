"""Unit tests for scripts/narrative.py."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import narrative


class FakeCli:
    def __init__(self, code=0, out=None):
        self.code = code
        self.out = {"discussion": {"url": "https://github.com/o/r/discussions/3"}} if out is None else out
        self.calls = []
        self.texts = []

    def __call__(self, *args, cwd=None):
        self.calls.append((args, cwd))
        if "--body-file" in args:
            self.texts.append(Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8"))
        if "--text" in args:
            self.texts.append(Path(args[args.index("--text") + 1]).read_text(encoding="utf-8"))
        return self.out, self.code


class SummaryTests(unittest.TestCase):
    def test_excerpt_keeps_the_tail(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("old\n" + "x" * 50, encoding="utf-8")
            excerpt = narrative.session_excerpt(path, limit=20)
        self.assertEqual(len(excerpt), 20)
        self.assertTrue(excerpt.endswith("x"))

    def test_text_events_are_joined(self):
        stdout = "\n".join([
            json.dumps({"type": "step_start"}),
            json.dumps({"type": "text", "part": {"type": "text", "text": "- Changed the CLI."}}),
            json.dumps({"type": "text", "part": {"type": "text", "text": "- Tests pass."}}),
            "not json",
        ])
        self.assertEqual(narrative.parse_text_events(stdout), "- Changed the CLI.\n- Tests pass.")

    def test_model_summary_uses_the_session_tail(self):
        calls = []

        def run(cmd, **kwargs):
            calls.append((cmd, kwargs))
            return SimpleNamespace(returncode=0, stderr="",
                                   stdout=json.dumps({"type": "text",
                                                      "part": {"type": "text", "text": "- Found it."}}))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("tool output the model should read", encoding="utf-8")
            summary, source = narrative.summarize_session(
                "implement-issue", "https://github.com/o/r/issues/1", True, "ses_1", path,
                {"opencode_cmd": "fake", "model": "m"}, run=run, print_fn=lambda *a: None)
        self.assertEqual((summary, source), ("- Found it.", "model"))
        cmd = calls[0][0]
        self.assertIn("--model", cmd)
        self.assertIn("tool output the model should read", cmd[-1])

    def test_nul_bytes_are_dropped_from_the_excerpt(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("keep\x00this", encoding="utf-8")
            excerpt = narrative.session_excerpt(path)
        self.assertEqual(excerpt, "keepthis")

    def test_spawn_failure_falls_back_to_facts(self):
        def run(cmd, **kwargs):
            raise ValueError("embedded null byte")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("tool output", encoding="utf-8")
            summary, source = narrative.summarize_session(
                "implement-issue", "https://github.com/o/r/issues/1", True, "ses_1", path,
                {"opencode_cmd": "fake"}, run=run, print_fn=lambda *a: None)
        self.assertEqual(source, "facts")

    def test_summary_session_is_deleted(self):
        calls = []

        def run(cmd, **kwargs):
            calls.append(cmd)
            if cmd[1:2] == ["session"]:
                return SimpleNamespace(returncode=0, stdout="", stderr="")
            return SimpleNamespace(returncode=0, stderr="", stdout="\n".join([
                json.dumps({"type": "step_start", "sessionID": "ses_9"}),
                json.dumps({"type": "text", "part": {"type": "text", "text": "- Done."}}),
            ]))

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("tool output", encoding="utf-8")
            summary, source = narrative.summarize_session(
                "implement-issue", "https://github.com/o/r/issues/1", True, "ses_1", path,
                {"opencode_cmd": "fake"}, run=run, print_fn=lambda *a: None)
        self.assertEqual((summary, source), ("- Done.", "model"))
        self.assertIn(["fake", "session", "delete", "ses_9"], calls)

    def test_model_failure_falls_back_to_facts(self):
        def run(cmd, **kwargs):
            raise subprocess.TimeoutExpired(cmd="fake", timeout=1)

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "session.log"
            path.write_text("tool output", encoding="utf-8")
            summary, source = narrative.summarize_session(
                "review-changes", "https://github.com/o/r/issues/1", False, "timed out", path,
                {"opencode_cmd": "fake"}, run=run, print_fn=lambda *a: None)
        self.assertEqual(source, "facts")
        self.assertIn("review-changes", summary)
        self.assertIn("timed out", summary)

    def test_empty_log_needs_no_model_call(self):
        def run(cmd, **kwargs):
            raise AssertionError("the model must not run without a log")

        summary, source = narrative.summarize_session(
            "submit-pr", "https://github.com/o/r/issues/1", True, "ses_1", "",
            {"opencode_cmd": "fake"}, run=run, print_fn=lambda *a: None)
        self.assertEqual(source, "facts")
        self.assertIn("succeeded", summary)


class RunNotebookTests(unittest.TestCase):
    def test_start_step_and_finish_append_notes(self):
        fake = FakeCli()
        notebook = narrative.RunNotebook(fake, category="lab-notebook",
                                         title="Run notebook 2026-11-16",
                                         print_fn=lambda *a: None)
        notebook.start(target="project o/12", model="m", hours=2, notes_dir="/tmp/notes")
        notebook.step("implement-issue", "https://github.com/o/r/issues/1", "- Started.",
                      pr_url="https://github.com/o/r/pull/1", head="abc")
        notebook.finish(["https://github.com/o/r/issues/1"], [])
        self.assertEqual(len(fake.calls), 3)
        for args, _ in fake.calls:
            self.assertEqual(args[:2], ("discussion", "post"))
            self.assertIn("--category", args)
            self.assertIn("lab-notebook", args)
            self.assertIn("--title", args)
        self.assertIn("Run start", fake.texts[0])
        self.assertIn("implement-issue", fake.texts[1])
        self.assertIn("https://github.com/o/r/pull/1", fake.texts[1])
        self.assertIn("Run end", fake.texts[2])

    def test_unavailable_notebook_stops_posting(self):
        fake = FakeCli(code=3, out={"available": False, "reason": "Discussions are disabled."})
        notebook = narrative.RunNotebook(fake, print_fn=lambda *a: None)
        notebook.start(target="project o/12")
        notebook.step("implement-issue", "https://github.com/o/r/issues/1", "- Started.")
        self.assertFalse(notebook.available)
        self.assertIn("disabled", notebook.unavailable_reason)
        self.assertEqual(len(fake.calls), 1)

    def test_disabled_notebook_posts_nothing(self):
        fake = FakeCli()
        notebook = narrative.RunNotebook(fake, enabled=False, print_fn=lambda *a: None)
        notebook.start(target="project o/12")
        self.assertEqual(fake.calls, [])

    def test_failed_post_keeps_the_notebook_available(self):
        fake = FakeCli(code=1, out={"errors": [{"part": "write", "error": "boom"}]})
        notebook = narrative.RunNotebook(fake, print_fn=lambda *a: None)
        notebook.start(target="project o/12")
        self.assertTrue(notebook.available)


class IssueCheckpointTests(unittest.TestCase):
    def test_checkpoint_is_posted(self):
        fake = FakeCli()
        out = narrative.post_issue_checkpoint(fake, "https://github.com/o/r/issues/1",
                                              "**Work started**", print_fn=lambda *a: None)
        self.assertEqual(out, fake.out)
        args, _ = fake.calls[0]
        self.assertEqual(args[:3], ("issue", "comment", "https://github.com/o/r/issues/1"))
        self.assertIn("Work started", fake.texts[0])

    def test_checkpoint_failure_does_not_raise(self):
        fake = FakeCli(code=1, out={"errors": [{"part": "write", "error": "boom"}]})
        out = narrative.post_issue_checkpoint(fake, "https://github.com/o/r/issues/1", "text",
                                              print_fn=lambda *a: None)
        self.assertIsNone(out)


if __name__ == "__main__":
    unittest.main()
