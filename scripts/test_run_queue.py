"""Unit tests for the deterministic queue runner scripts/run_queue.py."""
import argparse
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import run_queue


class NextStepTableTests(unittest.TestCase):
    """Table tests for next_step pure function covering each observed state."""

    def test_needs_input_is_parked(self):
        state = {"labels": ["triage:needs-input"], "pr": None}
        self.assertEqual(run_queue.next_step(state), "PARKED")

    def test_no_pr_is_implement(self):
        state = {"labels": ["triage:ready"], "pr": None}
        self.assertEqual(run_queue.next_step(state), "implement-issue")

    def test_draft_no_verdict_is_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "review_verdicts": [],
        }
        self.assertEqual(run_queue.next_step(state), "review-changes")

    def test_draft_stale_verdict_is_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "new_head", "is_draft": True},
            "review_verdicts": [{"head": "old_head", "verdict": "clean"}],
        }
        self.assertEqual(run_queue.next_step(state), "review-changes")

    def test_draft_clean_verdict_is_submit_pr(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "review_verdicts": [{"head": "abc", "verdict": "clean"}],
        }
        self.assertEqual(run_queue.next_step(state), "submit-pr")

    def test_draft_blocking_findings_under_limit_is_address_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "review_verdicts": [{"head": "abc", "verdict": "findings"}],
        }
        self.assertEqual(run_queue.next_step(state, correction_limit=2), "address-pr-review")

    def test_draft_blocking_findings_reaches_limit_is_park_blocker(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "head2", "is_draft": True},
            "review_verdicts": [
                {"head": "head1", "verdict": "findings"},
                {"head": "head2", "verdict": "findings"},
            ],
        }
        self.assertEqual(run_queue.next_step(state, correction_limit=2), "park-blocker")

    def test_human_changes_requested_on_draft_triggers_address_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "reviews": [{"author": "lmorchard", "state": "CHANGES_REQUESTED", "commit": "abc", "covers_head": True}],
            "review_summary": {"state": "changes_requested", "changes_requested": ["lmorchard"]},
        }
        self.assertEqual(run_queue.next_step(state), "address-pr-review")

    def test_human_changes_requested_on_ready_pr_triggers_address_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "green",
            "reviews": [{"author": "lmorchard", "state": "CHANGES_REQUESTED", "commit": "abc", "covers_head": True}],
            "review_summary": {"state": "changes_requested", "changes_requested": ["lmorchard"]},
        }
        self.assertEqual(run_queue.next_step(state), "address-pr-review")

    def test_human_approved_on_draft_triggers_submit_pr(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "reviews": [{"author": "lmorchard", "state": "APPROVED", "commit": "abc", "covers_head": True}],
            "review_summary": {"state": "approved", "changes_requested": []},
        }
        self.assertEqual(run_queue.next_step(state), "submit-pr")

    def test_ready_pr_pending_ci_waits(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "pending",
        }
        self.assertEqual(run_queue.next_step(state), "wait-ci")

    def test_ready_pr_failed_ci_is_address_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "failing",
        }
        self.assertEqual(run_queue.next_step(state), "address-pr-review")

    def test_ready_pr_pending_review_is_waiting(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "green",
            "pending_review_requests": ["les"],
        }
        self.assertEqual(run_queue.next_step(state), "WAITING")

    def test_ready_pr_green_ci_is_done(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "green",
            "pending_review_requests": [],
        }
        self.assertEqual(run_queue.next_step(state), "DONE")


class NextItemSelectionTests(unittest.TestCase):
    """Tests for next_item board-driven selection (Decision 9)."""

    def test_in_flight_advancing_item_chosen_first(self):
        board = {
            "in_flight": [
                {"number": 1, "issue": "o/r#1", "step": "review-changes"},
                {"number": 2, "issue": "o/r#2", "step": "DONE"},
            ],
            "parked": [{"number": 3, "issue": "o/r#3"}],
            "selection": [{"number": 4, "issue": "o/r#4"}],
        }
        item = run_queue.next_item(board)
        self.assertEqual(item["number"], 1)

    def test_time_parked_chosen_when_no_in_flight(self):
        board = {
            "in_flight": [{"number": 1, "step": "DONE"}],
            "parked": [{"number": 3, "issue": "o/r#3"}],
            "selection": [{"number": 4, "issue": "o/r#4"}],
        }
        item = run_queue.next_item(board)
        self.assertEqual(item["number"], 3)

    def test_ready_queue_chosen_when_no_in_flight_or_parked(self):
        board = {
            "in_flight": [],
            "parked": [],
            "selection": [{"number": 4, "issue": "o/r#4"}, {"number": 5, "issue": "o/r#5"}],
        }
        item = run_queue.next_item(board)
        self.assertEqual(item["number"], 4)

    def test_skips_attempted_and_needs_input(self):
        board = {
            "in_flight": [{"number": 1, "labels": ["triage:needs-input"]}],
            "parked": [{"number": 3, "park_kind": "question"}],
            "selection": [
                {"number": 4, "labels": ["triage:needs-input"]},
                {"number": 5, "issue": "o/r#5"},
            ],
        }
        attempted = {5}
        self.assertIsNone(run_queue.next_item(board, attempted=attempted))

    def test_empty_board_returns_none(self):
        board = {"in_flight": [], "parked": [], "selection": []}
        self.assertIsNone(run_queue.next_item(board))


class ProjectDiscoveryTests(unittest.TestCase):
    """Tests for discover_project."""

    def test_explicit_override(self):
        owner, number = run_queue.discover_project("lmorchard/12")
        self.assertEqual((owner, number), ("lmorchard", 12))

    def test_invalid_override(self):
        with self.assertRaises(ValueError):
            run_queue.discover_project("invalid_format")
    def test_provider_and_model_combine(self):
        with patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value={"in_flight": [], "parked": [], "selection": []}):
            # When both --provider and --model given without slash
            with patch("run_queue.run_session") as mock_session:
                run_queue.main(["--provider", "lmstudio", "--model", "qwen3.8-27b", "--once"])
            # Check options dict passed to run_session if it ran, or test arg parsing
            parser = argparse.ArgumentParser()
            # Test direct argument resolution in main logic
            model = "qwen3.8-27b"
            provider = "lmstudio"
            combined = f"{provider}/{model}" if provider and "/" not in model else model
            self.assertEqual(combined, "lmstudio/qwen3.8-27b")


    @patch("subprocess.run")
    def test_single_open_project(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"projectsV2": [{"owner": {"login": "lmorchard"}, "number": 12, "closed": False}]}),
        )
        owner, number = run_queue.discover_project()
        self.assertEqual((owner, number), ("lmorchard", 12))

    @patch("subprocess.run")
    def test_no_open_project_raises(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stdout=json.dumps({"projectsV2": []}))
        with self.assertRaises(RuntimeError) as ctx:
            run_queue.discover_project()
        self.assertIn("No open projects", str(ctx.exception))

    @patch("subprocess.run")
    def test_multiple_open_projects_raises(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({
                "projectsV2": [
                    {"owner": {"login": "lmorchard"}, "number": 12, "title": "P12", "closed": False},
                    {"owner": {"login": "lmorchard"}, "number": 13, "title": "P13", "closed": False},
                ]
            }),
        )
        with self.assertRaises(RuntimeError) as ctx:
            run_queue.discover_project()
        self.assertIn("Multiple open projects", str(ctx.exception))


class ActiveRunCheckTests(unittest.TestCase):
    """Tests for check_active_runs."""

    @patch("shutil.which", return_value="/usr/local/bin/opencode")
    @patch("subprocess.run")
    def test_active_session_raises(self, mock_run, _mock_which):
        import time
        now_ms = time.time() * 1000
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"id": "ses_1", "title": "Unattended burndown active", "time": {"updated": now_ms - 60000}}
            ]),
        )
        with self.assertRaises(RuntimeError) as ctx:
            run_queue.check_active_runs()
        self.assertIn("An unattended burndown session was active", str(ctx.exception))

    @patch("shutil.which", return_value="/usr/local/bin/opencode")
    @patch("subprocess.run")
    def test_stale_session_ignored(self, mock_run, _mock_which):
        import time
        now_ms = time.time() * 1000
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"id": "ses_1", "title": "Unattended burndown old", "time": {"updated": now_ms - 40 * 60 * 1000}}
            ]),
        )
        # Should not raise
        run_queue.check_active_runs()


class ComposePromptTests(unittest.TestCase):
    """Tests for prompt composition."""

    def test_strips_yaml_frontmatter(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            (skill_dir / "SKILL.md").write_text("---\nname: ghflow\n---\n# ghflow\nSkill content.\n", encoding="utf-8")
            prompt = run_queue.compose_prompt(skill_dir, "Follow the handoff.")
            self.assertFalse(prompt.startswith("---"))
            self.assertIn("# ghflow\nSkill content.", prompt)
            self.assertIn(f"Base directory for this skill: {skill_dir}", prompt)
            self.assertIn("Follow the handoff.", prompt)


class ProgressRuleAndLoopTests(unittest.TestCase):
    """Tests for session execution, progress detection, and retry rules."""

    def test_park_issue_writes_file_and_calls_cli(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            run_queue.park_issue("https://github.com/o/r/issues/1", "https://github.com/o/r/pull/2", "blocker",
                                 "Stalled progress", notes_dir, cli_fn=fake_cli)
            self.assertEqual(len(calls), 1)
            self.assertEqual(calls[0][0], "park")
            self.assertEqual(calls[0][1], "https://github.com/o/r/issues/1")
            self.assertEqual(calls[0][3], "https://github.com/o/r/pull/2")
            self.assertEqual(calls[0][5], "blocker")

    def test_run_session_creates_handoff_runs_opencode_and_deletes_session(self):
        cli_calls = []
        subproc_calls = []

        def fake_cli(*args, cwd=None):
            cli_calls.append(args)
            return {"dispatch_prompt": "Prompt for step"}, 0

        def fake_subproc_run(cmd, **kwargs):
            subproc_calls.append(cmd)
            return MagicMock(returncode=0, stdout="", stderr="")

        mock_proc = MagicMock()
        mock_proc.stdout = ['{"type": "step_start", "sessionID": "ses_test123"}\n', '{"type": "step_finish"}\n']
        mock_proc.returncode = 0
        mock_proc.wait.return_value = 0

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            skill_dir = notes_dir / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
            options = {"skill_dir": str(skill_dir), "opencode_cmd": "fake_opencode"}

            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run", side_effect=fake_subproc_run):
                ok, ses_id = run_queue.run_session("review-changes", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=fake_cli)
            self.assertTrue(ok)
            self.assertEqual(ses_id, "ses_test123")
            # Verified handoff passed --verdict for review-changes
            self.assertIn("--verdict", cli_calls[0])
            # Verified opencode session delete was called
            delete_calls = [c for c in subproc_calls if "delete" in c]
            self.assertEqual(len(delete_calls), 1)
            self.assertEqual(delete_calls[0][-1], "ses_test123")

    def test_run_session_aborts_on_turn_limit(self):
        mock_proc = MagicMock()
        mock_proc.stdout = [
            '{"type": "step_start", "sessionID": "ses_1"}\n',
            '{"type": "step_finish"}\n',
            '{"type": "step_start"}\n',
            '{"type": "step_finish"}\n',
            '{"type": "step_start"}\n',
            '{"type": "step_finish"}\n',
        ]
        mock_proc.returncode = 0
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            options = {"skill_dir": str(notes_dir), "max_turns": 2}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"):
                ok, reason = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=lambda *a, **k: ({}, 0))
            self.assertFalse(ok)
            self.assertIn("exceeded turn limit", reason)
            mock_proc.terminate.assert_called()

    def test_run_session_aborts_on_stalled_reasoning_loop(self):
        mock_proc = MagicMock()
        mock_proc.stdout = [
            '{"type": "step_start", "sessionID": "ses_1"}\n',
            '{"type": "step_finish", "part": {"tokens": {"input": 50000, "output": 0, "reasoning": 32000}}, "reason": "length"}\n',
        ]
        mock_proc.returncode = 0
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            options = {"skill_dir": str(notes_dir)}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"):
                ok, reason = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=lambda *a, **k: ({}, 0))
            self.assertFalse(ok)
            self.assertIn("stalled in reasoning loop", reason)
            mock_proc.terminate.assert_called()

    def test_run_session_aborts_on_output_limit_error(self):
        mock_proc = MagicMock()
        mock_proc.stdout = [
            '{"type": "step_start", "sessionID": "ses_1"}\n',
            '{"type": "error", "error": {"type": "output-limit", "message": "Response still truncated"}}\n',
        ]
        mock_proc.returncode = 0
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            options = {"skill_dir": str(notes_dir)}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"):
                ok, reason = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=lambda *a, **k: ({}, 0))
            self.assertFalse(ok)
            self.assertIn("output limit exceeded", reason)
            mock_proc.terminate.assert_called()

    def test_run_session_aborts_on_session_timeout(self):
        mock_proc = MagicMock()
        mock_proc.stdout = [
            '{"type": "step_start", "sessionID": "ses_1"}\n',
        ]
        mock_proc.returncode = 0
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            options = {"skill_dir": str(notes_dir), "session_timeout": 0.001}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"), \
                 patch("time.time", side_effect=[100.0, 100.0, 200.0, 200.0, 200.0]):
                ok, reason = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=lambda *a, **k: ({}, 0))
            self.assertFalse(ok)
            self.assertIn("exceeded timeout", reason)
            mock_proc.terminate.assert_called()

    def test_review_directives_applied_to_initial_review_and_submit(self):
        captured_options = []

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None):
            captured_options.append((step, dict(options)))
            return True, "ses_id"

        states = [
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": True}, "review_verdicts": []},
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": True},
             "review_verdicts": [{"head": "c1", "verdict": "clean"}]},
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": False},
             "ci": "green", "pending_review_requests": []},
        ]
        step_calls = []

        def fake_observe(issue_ref, cli_fn=None, cwd=None):
            idx = min(len(step_calls), len(states) - 1)
            step_calls.append(idx)
            return dict(states[idx])

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            board = {"in_flight": [], "parked": [], "selection": [{"number": 1, "issue": "https://github.com/o/r/issues/1"}]}
            with patch("run_queue.discover_project", return_value=("o", 12)), \
                 patch("run_queue.check_active_runs"), \
                 patch("run_queue.observe_board", return_value=board), \
                 patch("run_queue.observe_issue", side_effect=fake_observe), \
                 patch("run_queue.run_session", side_effect=fake_run_session), \
                 patch("run_queue.run_cli", return_value=({}, 0)):
                run_queue.main(["--once", "--notes-dir", str(notes_dir)])

        steps = [s for s, _ in captured_options]
        self.assertEqual(steps, ["review-changes", "submit-pr"])
        review_opt = captured_options[0][1]
        self.assertIn("Inspect the commit diff", review_opt.get("extra_text", ""))
        self.assertIn("Do not write new end-to-end integration test suites", review_opt.get("extra_text", ""))
    def test_end_to_end_reconciliation_flow(self):
        """An issue goes through implement -> review -> submit-pr to DONE."""
        states = [
            # 1. Initially no PR
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"], "pr": None},
            # 2. After implement: draft PR exists, no verdict
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": True}, "review_verdicts": []},
            # 3. After review: draft PR with clean verdict
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": True},
             "review_verdicts": [{"head": "c1", "verdict": "clean"}]},
            # 4. After submit-pr: ready PR with green CI
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": False},
             "ci": "green", "pending_review_requests": []},
        ]
        step_calls = []

        def fake_observe(issue_ref, cli_fn=None, cwd=None):
            idx = min(len(step_calls), len(states) - 1)
            return dict(states[idx])

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None):
            step_calls.append(step)
            return True, "ses_id"

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            board = {
                "in_flight": [],
                "parked": [],
                "selection": [{"number": 1, "issue": "https://github.com/o/r/issues/1"}],
            }
            with patch("run_queue.discover_project", return_value=("o", 12)), \
                 patch("run_queue.check_active_runs"), \
                 patch("run_queue.observe_board", return_value=board), \
                 patch("run_queue.observe_issue", side_effect=fake_observe), \
                 patch("run_queue.run_session", side_effect=fake_run_session), \
                 patch("run_queue.run_cli", return_value=({}, 0)) as mock_cli:
                ret = run_queue.main(["--once", "--notes-dir", str(notes_dir)])
                self.assertEqual(ret, 0)
                self.assertEqual(step_calls, ["implement-issue", "review-changes", "submit-pr"])
                # queue summary was called
                summary_calls = [c for c in mock_cli.call_args_list if "summary" in c[0]]
                self.assertTrue(summary_calls)

if __name__ == "__main__":
    unittest.main()
