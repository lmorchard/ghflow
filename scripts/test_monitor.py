"""Unit tests for the deterministic run monitor scripts/monitor.py."""
import json
import tempfile
import unittest
from pathlib import Path

import monitor

FIXTURE = Path(__file__).parent / "fixtures" / "weekend-2026-11-21.json"


def healthy_facts():
    return {
        "identity": {"login": "MokaGnome", "ready": True},
        "checkout": {"branch": "main", "head": "a", "dirty": False},
        "repository": {"local_default_head": "a", "origin_default_head": "a"},
        "skill_source": {"head": "a", "up_to_date": True},
        "base_ci": {"commit": "a", "summary": "green",
                    "checks": [{"name": "check", "state": "passed"}]},
        "project_facts": {"present": True, "origin": {"present": True, "stale_sources": []}},
    }


class PreflightTests(unittest.TestCase):
    def test_stops_when_the_gh_login_differs_from_the_configured_identity(self):
        running = monitor.Monitor(".", write=False)
        running.preflight(healthy_facts(),
                          identity={"login": "MokaGnome", "ready": True},
                          exec_login="lmorchard", lock={"pid": 1})
        self.assertIsNotNone(running.stopped)
        self.assertIn("gh api user", running.stopped)

    def test_stops_when_base_ci_is_red(self):
        facts = healthy_facts()
        facts["base_ci"]["summary"] = "failing"
        running = monitor.Monitor(".", write=False)
        running.preflight(facts, identity={"login": "MokaGnome", "ready": True},
                          exec_login="MokaGnome", lock={"pid": 1})
        self.assertIn("base_ci", running.stopped)

    def test_flags_stale_facts_and_a_dirty_checkout_without_stopping(self):
        facts = healthy_facts()
        facts["checkout"]["dirty"] = 2
        facts["project_facts"]["origin"]["stale_sources"] = [{"path": "AGENTS.md"}]
        running = monitor.Monitor(".", write=False)
        running.preflight(facts, identity={"login": "MokaGnome", "ready": True},
                          exec_login="MokaGnome", lock={"pid": 1})
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["facts"]["state"], monitor.FAIL)
        self.assertEqual(names["checkout"]["state"], monitor.FAIL)
        self.assertIsNone(running.stopped)

    def test_reports_both_local_models(self):
        running = monitor.Monitor(".", write=False)
        running.preflight(healthy_facts(), identity={"login": "MokaGnome", "ready": True},
                          exec_login="MokaGnome", lock={"pid": 1},
                          model="lmstudio/qwen", model_available=True,
                          review_model="lmstudio/flint", review_available=True)
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["model"]["state"], monitor.PASS)
        self.assertEqual(names["review_model"]["state"], monitor.PASS)
        self.assertIn("lmstudio/flint", names["review_model"]["message"])

    def test_selection_flags_a_missing_required_label(self):
        running = monitor.Monitor(".", write=False)
        running.selection([{"number": 7, "labels": ["triage:ready"]},
                           {"number": 8, "labels": ["triage:needs-attention"]}],
                          required_labels=["triage:ready"])
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["selection"]["state"], monitor.FAIL)
        self.assertEqual(names["selection"]["evidence"]["problems"][0]["issue"], 8)


class SessionTests(unittest.TestCase):
    def test_flags_idle_and_context_over_the_limits(self):
        running = monitor.Monitor(".", write=False)
        running.session_sample("implement-issue", "https://github.com/o/r/issues/1", "ses_x",
                               alive=True, last_event_age=1000, context_tokens=120000,
                               turns=10, age=100,
                               limits={"step_idle_timeout": 900, "session_timeout": 5400,
                                       "max_turns": 150, "context_warn_tokens": 100000,
                                       "max_context_tokens": 0})
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["session_idle"]["state"], monitor.FAIL)
        self.assertEqual(names["session_context"]["state"], monitor.FAIL)
        self.assertIsNone(running.stopped)

    def test_handoff_model_mismatch_is_an_alert(self):
        with tempfile.TemporaryDirectory() as tmp:
            handoff = Path(tmp) / "handoff.md"
            handoff.write_text("Review plan: model lmstudio/other\n", encoding="utf-8")
            running = monitor.Monitor(tmp, write=False)
            running.handoff_model("review-changes", handoff, "lmstudio/run")
            names = {entry["name"]: entry for entry in running.checks}
            self.assertEqual(names["handoff_model"]["state"], monitor.FAIL)


class StepTests(unittest.TestCase):
    def test_missing_checks_and_a_draft_boundary_are_distinct_alerts(self):
        running = monitor.Monitor(".", write=False)
        state = {
            "issue": "https://github.com/o/r/issues/1",
            "pr": {"url": "https://github.com/o/r/pull/2", "head": "abc", "is_draft": False},
            "ci": "missing",
            "checks": [{"name": "check", "state": "missing"}],
            "review_verdicts": [{"head": "abc", "verdict": "clean"}],
        }
        running.after_step("submit-pr", state, worktree={"dirty": 0})
        running.phase_end("issue", issue=state["issue"], step="submit-pr", state=state)
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["checks"]["state"], monitor.FAIL)
        self.assertEqual(names["published"]["state"], monitor.PASS)
        self.assertNotIn("draft_at_boundary", names)

        draft = {"issue": "https://github.com/o/r/issues/3",
                 "pr": {"url": "https://github.com/o/r/pull/4", "head": "def", "is_draft": True}}
        running.phase_end("issue", issue=draft["issue"], step="implement-issue", state=draft)
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["draft_at_boundary"]["state"], monitor.FAIL)

    def test_worktree_dirt_is_an_alert(self):
        running = monitor.Monitor(".", write=False)
        running.after_step("implement-issue",
                           {"issue": "https://github.com/o/r/issues/1",
                            "pr": {"url": "u", "head": "abc"}},
                           worktree={"path": "/tmp/wt", "dirty": 2})
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["worktree"]["state"], monitor.FAIL)


class FinalTests(unittest.TestCase):
    def test_summary_coverage_names_a_missing_processed_issue(self):
        running = monitor.Monitor(".", write=False)
        running.finish(records=[{"issue": "https://github.com/o/r/issues/1", "endpoint": "DONE"}],
                       selection=[{"number": 1}], states=[])
        running.summary_coverage([{"issue": "o/r#2"}])
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["summary_coverage"]["state"], monitor.FAIL)
        self.assertEqual(names["summary_coverage"]["evidence"]["missing"], [1])

    def test_finish_counts_drafts_parked_and_not_started(self):
        running = monitor.Monitor(".", write=False)
        running.finish(
            records=[{"issue": "https://github.com/o/r/issues/1", "endpoint": "time-park"},
                     {"issue": "https://github.com/o/r/issues/2", "endpoint": "DONE"}],
            selection=[{"number": 1}, {"number": 2}, {"number": 3}],
            states=[
                {"issue": "https://github.com/o/r/issues/1",
                 "pr": {"url": "u", "is_draft": True}},
                {"issue": "https://github.com/o/r/issues/2",
                 "pr": {"url": "v", "is_draft": False, "state": "OPEN"}},
                {"issue": "https://github.com/o/r/issues/3", "started": False, "pr": {}},
            ])
        self.assertEqual(running.counts["selected"], 3)
        self.assertEqual(running.counts["parked"], 1)
        self.assertEqual(running.counts["draft"], 1)
        self.assertEqual(running.counts["open"], 1)
        self.assertEqual(running.counts["not_started"], 1)
        self.assertEqual(running.counts["done"], 1)

    def test_throughput_regression_is_an_alert(self):
        running = monitor.Monitor(".", write=False)
        running.finish(phase_throughput=[{"name": "early", "hours_per_done": 1.15},
                                         {"name": "late", "hours_per_done": 1.9}])
        names = {entry["name"]: entry for entry in running.checks}
        self.assertEqual(names["throughput"]["state"], monitor.FAIL)
        self.assertEqual(names["throughput"]["evidence"]["late"], 1.9)


class ReportTests(unittest.TestCase):
    def test_write_creates_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            running = monitor.Monitor(tmp)
            running.preflight(healthy_facts(),
                              identity={"login": "MokaGnome", "ready": True},
                              exec_login="MokaGnome", lock={"pid": 1})
            path = running.write(force=True)
            self.assertTrue(Path(path).is_file())
            self.assertTrue((Path(tmp) / monitor.MARKDOWN_NAME).is_file())
            report = json.loads(Path(path).read_text(encoding="utf-8"))
            self.assertEqual(report["schema"], monitor.SCHEMA)
            self.assertTrue(report["checks"])
            self.assertIn("alerts", report)

    def test_status_line_names_the_counts_and_alerts(self):
        running = monitor.Monitor(".", write=False)
        running.counts = {"open": 1, "merged": 0, "parked": 2, "draft": 1}
        running.add("checks", "post-step", monitor.ALERT, monitor.FAIL, "missing")
        line = running.status_line()
        self.assertIn("alerts=1", line)
        self.assertIn("counts=open:1", line)


class WeekendReplayTests(unittest.TestCase):
    def test_replay_reproduces_the_findings_the_coordinator_made_by_hand(self):
        fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
        report = monitor.replay(fixture)
        alerts = report["alerts"]
        by_name = {}
        for alert in alerts:
            by_name.setdefault(alert["name"], []).append(alert)

        self.assertIsNone(report["stopped"])
        self.assertEqual(len(by_name["draft_at_boundary"]), 2)
        self.assertIn("facts", by_name)
        self.assertIn("checks", by_name)
        self.assertIn("issue_not_started", by_name)
        self.assertIn("throughput", by_name)
        self.assertEqual(
            {alert["evidence"]["issue"] for alert in by_name["draft_at_boundary"]},
            {"https://github.com/lmorchard/decafclaw/issues/1378",
             "https://github.com/lmorchard/decafclaw/issues/1405"})
        self.assertIn("1707", by_name["checks"][0]["evidence"]["pr"])
        self.assertEqual(by_name["issue_not_started"][0]["evidence"]["issue"], 1379)
        self.assertEqual(by_name["throughput"][0]["evidence"]["early"], 1.15)
        self.assertEqual(by_name["throughput"][0]["evidence"]["late"], 1.9)
        self.assertEqual(report["counts"]["selected"], 4)
        self.assertEqual(report["counts"]["draft"], 2)


if __name__ == "__main__":
    unittest.main()
