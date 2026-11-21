"""Tests for scripts/bundle_skill.py programmatic bundling."""

from pathlib import Path
import tempfile
import unittest

import bundle_skill


class BundleSkillTests(unittest.TestCase):
    def test_bundle_builder_content(self):
        content = bundle_skill.bundle_builder()
        self.assertIn("name: ghflow-build-slim", content)
        self.assertIn("make check", content)
        self.assertIn("tags find", content)
        self.assertIn("tags brief", content)
        self.assertIn("address-pr-review", content)
        self.assertIn("ABSOLUTE_SKILL_DIRECTORY", content)
        self.assertNotIn("triage-issues", content)
        self.assertNotIn("burndown-ready-queue", content)

    def test_bundle_reviewer_content(self):
        content = bundle_skill.bundle_reviewer()
        self.assertIn("name: ghflow-review-slim", content)
        self.assertIn("review verdict", content)
        self.assertIn("ghflow-review head=SHA", content)
        self.assertIn("make check", content)
        self.assertIn("No blocking findings", content)
        self.assertNotIn("implement-issue", content)
        self.assertNotIn("burndown-ready-queue", content)

    def test_check_bundles_detects_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # When bundles don't exist -> reports missing
            errors = bundle_skill.check_bundles(root)
            self.assertEqual(len(errors), 2)
            self.assertTrue(any("missing" in e for e in errors))

            # When bundles are written -> reports no errors
            bundle_skill.write_bundles(root)
            errors = bundle_skill.check_bundles(root)
            self.assertEqual(errors, [])

            # When bundle is modified -> reports drift
            p = root / "skills" / "build-slim" / "SKILL.md"
            p.write_text("modified content", encoding="utf-8")
            errors = bundle_skill.check_bundles(root)
            self.assertEqual(len(errors), 1)
            self.assertIn("out of date", errors[0])


if __name__ == "__main__":
    unittest.main()
