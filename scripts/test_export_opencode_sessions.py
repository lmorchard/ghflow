"""Export a session tree through a fake opencode command."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/export-opencode-sessions.py"

FAKE_OPENCODE = """#!/bin/sh
case "$1 $2" in
  "session list") cat "$FAKE_DIR/list.json" ;;
  "export "*) f="$FAKE_DIR/$2.json"; [ -f "$f" ] || { echo "no session $2" >&2; exit 1; }; cat "$f" ;;
  *) echo "unexpected: $*" >&2; exit 2 ;;
esac
"""


def task_part(description, child):
    return {"type": "tool", "tool": "task",
            "state": {"input": {"description": description},
                      "metadata": {"sessionId": child, "parentSessionId": "ses_root"}}}


def session(session_id, title, parent=None, parts=()):
    return {"info": {"id": session_id, "title": title, "parentID": parent,
                     "time": {"created": 1791829787355, "updated": 1791845517555}},
            "messages": [{"info": {"role": "assistant"}, "parts": list(parts)}]}


class ExportSessionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fake = Path(self.tmp.name) / "fake"
        self.fake.mkdir()
        exe = self.fake / "opencode"
        exe.write_text(FAKE_OPENCODE)
        exe.chmod(0o755)
        self.write("list.json", [
            {"id": "ses_root", "title": "Unattended burndown 1"},
            {"id": "ses_other", "title": "Unattended burndown 2"},
        ])
        self.write("ses_root.json", session("ses_root", "Unattended burndown 1", parts=[
            task_part("Implement", "ses_worker"),
            task_part("Review", "ses_reviewer"),
            task_part("Corrections", "ses_worker"),
        ]))
        self.write("ses_worker.json", session("ses_worker", "Implement", "ses_root"))
        self.write("ses_reviewer.json", session("ses_reviewer", "Review", "ses_root", parts=[
            task_part("Nested check", "ses_nested"),
        ]))
        self.write("ses_nested.json", session("ses_nested", "Nested check", "ses_reviewer"))
        self.out = Path(self.tmp.name) / "out"

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name, data):
        (self.fake / name).write_text(json.dumps(data))

    def run_script(self, *args):
        env = dict(os.environ, PATH=f"{self.fake}:{os.environ['PATH']}", FAKE_DIR=str(self.fake))
        return subprocess.run([str(SCRIPT), *args, "--out", str(self.out)],
                              text=True, capture_output=True, env=env)

    def test_exports_root_and_every_descendant_once(self):
        result = self.run_script("ses_root")
        self.assertEqual(result.returncode, 0, result.stderr)
        files = sorted(p.name for p in self.out.iterdir())
        self.assertEqual(files, ["index.md", "session-ses_nested.json", "session-ses_reviewer.json",
                                 "session-ses_root.json", "session-ses_worker.json"])
        index = (self.out / "index.md").read_text()
        self.assertIn("| `ses_root` | `` | Unattended burndown 1 |", index)
        self.assertIn("| `ses_worker` | `ses_root` | Implement |", index)
        self.assertIn("- Corrections → `ses_worker`", index)
        self.assertEqual(result.stdout.count("ses_worker"), 1)

    def test_resolves_a_unique_title(self):
        result = self.run_script("burndown 1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.out / "session-ses_root.json").exists())

    def test_refuses_an_ambiguous_title(self):
        result = self.run_script("Unattended burndown")
        self.assertEqual(result.returncode, 1)
        self.assertIn("2 session titles contain", result.stderr)
        self.assertIn("ses_other", result.stderr)
        self.assertFalse(self.out.exists())

    def test_fails_on_a_missing_child(self):
        (self.fake / "ses_nested.json").unlink()
        result = self.run_script("ses_root")
        self.assertEqual(result.returncode, 1)
        self.assertIn("no session ses_nested", result.stderr)
        self.assertFalse((self.out / "index.md").exists())


if __name__ == "__main__":
    unittest.main()
