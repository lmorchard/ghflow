"""Tests for the doc checks in check.py."""

import subprocess
import tempfile
import unittest
from pathlib import Path

from check import check_bare_gh_writes


class BareGhWriteLintTests(unittest.TestCase):
    def lint(self, files):
        """Write files into a throwaway git repo and run the identity lint on it."""
        root = Path(tempfile.mkdtemp(prefix="ghflow-lint-"))
        for name, text in files.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        def run(*args):
            subprocess.run(args, cwd=root, capture_output=True, text=True, check=True)
        run("git", "init", "-q")
        run("git", "add", ".")
        run("git", "-c", "user.email=t@example", "-c", "user.name=t", "commit", "-qm", "docs")
        return check_bare_gh_writes(root)

    def test_flags_a_bare_write_instruction(self):
        # The real past mistake: merge-pr.md told the agent to run a bare write.
        errors = self.lint({"references/tasks/merge-pr.md":
                            "Merge with `gh pr merge --match-head-commit SHA`.\n"})
        self.assertEqual(len(errors), 1)
        self.assertIn("references/tasks/merge-pr.md:1", errors[0])

    def test_accepts_exec_wrapped_and_cli_commands(self):
        errors = self.lint({
            "references/tasks/a.md": "Run `ghflow exec -- gh pr merge 7`.\n",
            "references/tasks/b.md": 'Run `python3 "$GHFLOW_CLI" pr merge 7`.\n',
            "references/tasks/c.md": 'Create with `python3 "$GHFLOW_CLI" exec -- gh issue create`.\n',
        })
        self.assertEqual(errors, [])

    def test_flags_a_bare_write_on_a_line_that_mentions_the_cli(self):
        errors = self.lint({
            "references/tasks/d.md": 'Set GHFLOW_CLI, then run `gh pr merge 7`.\n',
        })
        self.assertEqual(len(errors), 1)
        self.assertIn("references/tasks/d.md:1", errors[0])

    def test_flags_a_bare_write_after_an_exec_prefix(self):
        errors = self.lint({
            "references/tasks/e.md": "Run `ghflow exec -- git push`, then `gh pr merge 7`.\n",
        })
        self.assertEqual(len(errors), 1)
        self.assertIn("references/tasks/e.md:1", errors[0])

    def test_flags_a_bare_write_next_to_a_wrapped_write(self):
        errors = self.lint({
            "references/tasks/f.md": 'Run `python3 "$GHFLOW_CLI" exec -- gh api user` and `gh pr merge 7`.\n',
        })
        self.assertEqual(len(errors), 1)
        self.assertIn("references/tasks/f.md:1", errors[0])

    def test_honors_the_allow_marker(self):
        errors = self.lint({"docs/dev/g.md":
                            "Do not use `gh pr create --dry-run`. <!-- allow-bare-gh: forbidden command -->\n"})
        self.assertEqual(errors, [])

    def test_reads_are_not_flagged(self):
        errors = self.lint({"references/tasks/r.md":
                            "Confirm with `gh api user` and read with `gh issue list --repo O/R`.\n"})
        self.assertEqual(errors, [])

    def test_flags_writing_api_methods(self):
        for method in ("PUT", "POST", "DELETE"):
            with self.subTest(method=method):
                errors = self.lint({"references/tasks/u.md": f"Update with `gh api -X {method} repos/O/R/x`.\n"})
                self.assertEqual(len(errors), 1)

    def test_skips_run_records_and_fixtures(self):
        errors = self.lint({
            "evals/results/record.md": "The agent ran `gh pr merge 7`.\n",
            "docs/research/trial.md": "Then `gh issue close 5` followed.\n",
            "evals/scenarios/fixture.md": "Situation with `gh pr edit 7`.\n",
        })
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
