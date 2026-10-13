"""Launch composition checks for unattended-burndown.sh through fake agent commands."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts/unattended-burndown.sh"

# Records every argument on its own line, then exits with FAKE_STATUS.
FAKE_OPENCODE = """#!/bin/sh
for a in "$@"; do printf '%s\\n' "$a"; done > "$FAKE_ARGS"
exit "${FAKE_STATUS:-0}"
"""
# Drops caffeinate's own flag and runs the wrapped command.
FAKE_CAFFEINATE = """#!/bin/sh
shift
exec "$@"
"""
SKILL = """---
name: ghflow
description: test skill
---

# ghflow

Entry skill body.
"""


class UnattendedBurndownTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.bin = base / "bin"
        self.bin.mkdir()
        for name, text in (("opencode", FAKE_OPENCODE), ("caffeinate", FAKE_CAFFEINATE)):
            exe = self.bin / name
            exe.write_text(text)
            exe.chmod(0o755)
        self.skill = base / "skill"
        self.skill.mkdir()
        (self.skill / "SKILL.md").write_text(SKILL)
        self.repo = base / "repo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=self.repo, check=True)
        subprocess.run(["git", "remote", "add", "origin", "git@github.com:o/r.git"],
                       cwd=self.repo, check=True)
        self.args_file = base / "args.txt"
        self.log = base / "run.log"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, *extra, status=0):
        env = dict(os.environ, PATH=f"{self.bin}:{os.environ['PATH']}",
                   FAKE_ARGS=str(self.args_file), FAKE_STATUS=str(status))
        return subprocess.run(
            ["sh", str(SCRIPT), "--owner", "o", "--project", "6", "--agent", "opencode",
             "--skill-dir", str(self.skill), "--log", str(self.log), *extra],
            cwd=self.repo, text=True, capture_output=True, env=env)

    def test_message_omits_frontmatter_and_carries_the_request(self):
        result = self.run_script("--model", "p/m", "--same-model-exception")
        self.assertEqual(result.returncode, 0, result.stderr)
        args = self.args_file.read_text().split("\n")
        self.assertEqual(args[:5], ["run", "--auto", "--format", "json", "--title"])
        self.assertEqual(args[6:8], ["--model", "p/m"])
        message = "\n".join(args[8:]).rstrip("\n")
        self.assertTrue(message.startswith("# ghflow"), message[:80])
        self.assertNotIn("name: ghflow", message)
        self.assertIn("Entry skill body.", message)
        self.assertIn(f"Base directory for this skill: {self.skill}", message)
        self.assertIn("deliver the Ready queue of project 6 owned by o for o/r", message)
        self.assertIn("same local model for implementation and review", message)
        self.assertIn("finished at", result.stdout)

    def test_reports_a_failed_launch(self):
        result = self.run_script(status=3)
        self.assertEqual(result.returncode, 3)
        self.assertIn("exit 3", result.stdout)
        self.assertIn("see", result.stderr)

    def test_dry_run_launches_nothing(self):
        result = self.run_script("--dry-run")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.args_file.exists())
        self.assertIn("--- request ---", result.stdout)


if __name__ == "__main__":
    unittest.main()
