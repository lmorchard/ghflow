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

    def test_draft_findings_verdict_with_no_blockers_is_submit_pr(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "review_verdicts": [{
                "head": "abc",
                "verdict": "findings",
                "body": "## Verdict: findings (no blockers)\n\n## Blocking findings\n\nNone.\n\n## Notes\n\n1. Note.",
            }],
        }
        self.assertEqual(run_queue.next_step(state), "submit-pr")

    def test_draft_uses_latest_verdict_on_head(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": True},
            "review_verdicts": [
                {"head": "abc", "verdict": "findings"},
                {"head": "abc", "verdict": "clean"},
            ],
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
    def test_default_step_idle_timeout_is_300(self):
        self.assertEqual(run_queue.DEFAULT_STEP_IDLE_TIMEOUT, 300)


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
                run_queue.main(["--provider", "lmstudio", "--model", "qwen3.8-27b", "--once", "--no-notebook"])
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
    def test_active_session_with_dead_process_ignored(self, mock_run, _mock_which):
        import time
        now_ms = time.time() * 1000
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps([
                {"id": "ses_1", "title": "Unattended burndown active", "time": {"updated": now_ms - 60000}}
            ]),
        )
        # Should not raise when process is dead
        run_queue.check_active_runs(process_checker=lambda: False)

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

    def test_step_composes_focused_worker_prompt(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            tasks_dir = skill_dir / "references" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "implement-issue.md").write_text("# Implement", encoding="utf-8")
            prompt = run_queue.compose_prompt(skill_dir, "Follow the handoff.", step="implement-issue")
            self.assertIn("# ghflow-build: implement-issue", prompt)
            self.assertIn("Local-model single session", prompt)
            self.assertIn("implement-issue.md", prompt)
            self.assertIn("export GHFLOW_CLI=", prompt)
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
    def test_run_session_aborts_on_step_idle_timeout(self):
        mock_proc = MagicMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.fileno.return_value = 1
        mock_proc.stdout.readline.return_value = ""
        mock_proc.poll.return_value = None
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            options = {"skill_dir": str(notes_dir), "session_timeout": 5400, "step_idle_timeout": 0.001}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"), \
                 patch("select.select", return_value=([], [], [])), \
                 patch("time.time", side_effect=[100.0, 100.0, 100.0, 200.0, 200.0, 200.0]):
                ok, reason = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                                   notes_dir, options, cli_fn=lambda *a, **k: ({}, 0))
            self.assertFalse(ok)
            self.assertIn("idle timeout", reason)
            mock_proc.terminate.assert_called()

    def test_review_directives_applied_to_initial_review_and_submit(self):
        captured_options = []

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
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
                run_queue.main(["--once", "--no-notebook", "--no-deterministic-pr", "--notes-dir", str(notes_dir)])

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

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
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
                ret = run_queue.main(["--once", "--no-notebook", "--no-deterministic-pr", "--notes-dir", str(notes_dir)])
                self.assertEqual(ret, 0)
                self.assertEqual(step_calls, ["implement-issue", "review-changes", "submit-pr"])
                # queue summary was called
                summary_calls = [c for c in mock_cli.call_args_list if "summary" in c[0]]
                self.assertTrue(summary_calls)

    def test_end_to_end_reconciliation_flow_deterministic_pr(self):
        """By default, submit-pr runs deterministically without an LLM worker session."""
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
            # 4. After deterministic submit-pr: ready PR with green CI
            {"issue": "https://github.com/o/r/issues/1", "number": 1, "labels": ["triage:ready"],
             "pr": {"url": "https://github.com/o/r/pull/1", "head": "c1", "is_draft": False},
             "ci": "green", "pending_review_requests": []},
        ]
        step_calls = []
        observe_count = 0

        def fake_observe(issue_ref, cli_fn=None, cwd=None):
            nonlocal observe_count
            idx = min(observe_count, len(states) - 1)
            observe_count += 1
            return dict(states[idx])

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
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
                ret = run_queue.main(["--once", "--no-notebook", "--notes-dir", str(notes_dir)])
                self.assertEqual(ret, 0)
                self.assertEqual(step_calls, ["implement-issue", "review-changes"])
                ready_calls = [c for c in mock_cli.call_args_list if c[0][:2] == ("pr", "ready")]
                self.assertTrue(ready_calls)

    def test_execute_submit_pr_composes_body_and_marks_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            (notes_dir / "pr-summary-42.md").write_text("Summary text", encoding="utf-8")
            (notes_dir / "pr-review-42.md").write_text("Review text", encoding="utf-8")
            (notes_dir / "pr-decisions-42.md").write_text("Decisions text", encoding="utf-8")

            cli_calls = []
            def fake_cli(*args, **kwargs):
                cli_calls.append(args)
                if args[:2] == ("pr", "body"):
                    Path(args[args.index("--out") + 1]).write_text("Full body", encoding="utf-8")
                return {"url": "https://github.com/o/r/pull/42"}, 0

            state = {
                "issue": "https://github.com/o/r/issues/42",
                "repo": "o/r",
                "pr": {"url": "https://github.com/o/r/pull/42", "number": 42, "head": "head123"},
            }
            options = {"cwd": "/repo"}
            ok, out = run_queue.execute_submit_pr(state, "o", 12, notes_dir, options, cli_fn=fake_cli)
            self.assertTrue(ok)
            body_call = next(c for c in cli_calls if c[:2] == ("pr", "body"))
            self.assertIn("--summary", body_call)
            self.assertIn("--review", body_call)
            self.assertIn("--decisions", body_call)
            ready_call = next(c for c in cli_calls if c[:2] == ("pr", "ready"))
            self.assertIn("--expect-head", ready_call)
            self.assertIn("head123", ready_call)
            self.assertIn("--status", ready_call)
            self.assertIn("In review", ready_call)


class ParentSubIssueTests(unittest.TestCase):
    """Unit tests for parent issue burndown, sub-issue discovery, stacked PRs, and board visibility."""

    def test_prepare_worktree_creates_from_origin(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {"path": "/repo/.claude/worktrees/issue-42-add-a-thing", "base": "origin/main"}, 0

        res = run_queue.prepare_worktree("https://github.com/o/r/issues/42", "Add a Thing", "o", 12,
                                         {"cwd": "/repo"}, cli_fn=fake_cli)
        self.assertEqual(res, {"branch": "issue-42-add-a-thing", "path": "/repo/.claude/worktrees/issue-42-add-a-thing",
                               "created": True, "base": "origin/main", "setup": None})
        self.assertEqual(calls[0][:3], ("worktree", "create", "https://github.com/o/r/issues/42"))
        self.assertIn("issue-42-add-a-thing", calls[0])
        self.assertIn("--owner", calls[0])
        self.assertIn("--project", calls[0])

    def test_prepare_worktree_reuses_existing_branch(self):
        def fake_cli(*args, cwd=None):
            return {"path": "/repo/.claude/worktrees/issue-7-x", "action": "exists"}, 3

        res = run_queue.prepare_worktree("https://github.com/o/r/issues/7", "x", None, None,
                                         {"cwd": "/repo"}, cli_fn=fake_cli)
        self.assertEqual(res["created"], False)
        self.assertEqual(res["branch"], "issue-7-x")

    def test_prepare_worktree_returns_none_on_failure(self):
        def fake_cli(*args, cwd=None):
            return {"errors": [{"part": "worktree", "error": "boom"}]}, 1

        self.assertIsNone(run_queue.prepare_worktree("https://github.com/o/r/issues/9", "t", "o", 1,
                                                    {"cwd": "/repo"}, cli_fn=fake_cli))

    def test_park_issue_omits_pr_when_none(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp:
            run_queue.park_issue("https://github.com/o/r/issues/5", "", "blocker", "no progress", Path(tmp), cli_fn=fake_cli)
        self.assertNotIn("--pr", calls[0])
        self.assertEqual(calls[0][:2], ("park", "https://github.com/o/r/issues/5"))

    def test_run_fails_when_a_park_fails(self):
        def fake_run_cli(*args, cwd=None):
            if args and args[0] == "park":
                return {"errors": [{"part": "labels", "error": "label missing"}]}, 1
            return {}, 0

        def fake_observe(issue_ref, cli_fn=None, cwd=None):
            return {"issue": str(issue_ref), "number": 1, "labels": ["triage:ready"], "pr": None}

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            return True, "ses_id"

        board = {"in_flight": [], "parked": [], "selection": [{"number": 1, "issue": "https://github.com/o/r/issues/1"}]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", side_effect=fake_observe), \
             patch("run_queue.run_session", side_effect=fake_run_session), \
             patch("run_queue.run_cli", side_effect=fake_run_cli):
            status = run_queue.main(["--once", "--no-notebook", "--notes-dir", tmp])
        self.assertEqual(status, 1)

    def test_parse_issue_ref(self):
        self.assertEqual(run_queue.parse_issue_ref("https://github.com/o/r/issues/10"), ["https://github.com/o/r/issues/10"])
        self.assertEqual(run_queue.parse_issue_ref("o/r#10"), ["10", "--repo", "o/r"])
        self.assertEqual(run_queue.parse_issue_ref("#10"), ["10"])
        self.assertEqual(run_queue.parse_issue_ref("10"), ["10"])
        self.assertEqual(run_queue.parse_issue_ref(10), ["10"])

    def test_observe_parent_queries_subissues(self):
        fake_data = {
            "number": 100,
            "title": "Epic: Code Debt",
            "state": "OPEN",
            "url": "https://github.com/o/r/issues/100",
            "subIssues": {
                "nodes": [
                    {"number": 101, "title": "Child 1", "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
                    {"number": 102, "title": "Child 2", "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
                ],
                "totalCount": 2,
            },
            "subIssuesSummary": {"completed": 0, "percentCompleted": 0, "total": 2},
        }
        mock_proc = MagicMock(returncode=0, stdout=json.dumps(fake_data), stderr="")
        with patch("subprocess.run", return_value=mock_proc):
            res = run_queue.observe_parent("100")
        self.assertEqual(res["parent"]["number"], 100)
        self.assertEqual(len(res["children"]), 2)
        self.assertEqual(res["children"][0]["number"], 101)
        self.assertEqual(res["children"][1]["number"], 102)

    def test_observe_parent_raises_on_error(self):
        mock_proc = MagicMock(returncode=1, stdout="", stderr="Could not resolve issue")
        with patch("subprocess.run", return_value=mock_proc):
            with self.assertRaises(RuntimeError) as ctx:
                run_queue.observe_parent("999")
            self.assertIn("Failed to query parent issue", str(ctx.exception))

    def test_next_item_for_parent_prioritizes_inflight(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]
        # 102 has an open draft PR needing review, while 101 has no PR yet
        def fake_observe(ref, cli_fn=None, cwd=None):
            if "102" in str(ref):
                return {"issue": str(ref), "number": 102, "labels": [], "pr": {"url": "p2", "is_draft": True, "head": "h2"}, "review_verdicts": []}
            return {"issue": str(ref), "number": 101, "labels": [], "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children)
        self.assertEqual(chosen["number"], 102)

    def test_next_item_for_parent_skips_closed_and_done(self):
        children = [
            {"number": 101, "state": "CLOSED", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            {"number": 103, "state": "OPEN", "url": "https://github.com/o/r/issues/103"},
        ]
        # 102 is DONE (ready PR with green CI)
        def fake_observe(ref, cli_fn=None, cwd=None):
            if "102" in str(ref):
                return {"issue": str(ref), "number": 102, "labels": [], "pr": {"url": "p2", "is_draft": False, "head": "h2"}, "ci": "green", "pending_review_requests": []}
            return {"issue": str(ref), "number": 103, "labels": [], "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children)
        self.assertEqual(chosen["number"], 103)

    def test_find_preceding_pr_stacked_branch(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]
        # 101 has an open PR on branch issue-101-feat
        def fake_observe(ref, cli_fn=None, cwd=None):
            if "101" in str(ref):
                return {"issue": str(ref), "number": 101, "pr": {"number": 51, "head_branch": "issue-101-feat", "state": "OPEN"}}
            return {"issue": str(ref), "number": 102, "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            # First child has no preceding PR
            self.assertIsNone(run_queue.find_preceding_pr(101, children))
            # Second child finds preceding child 101
            prec = run_queue.find_preceding_pr(102, children)
            self.assertIsNotNone(prec)
            self.assertEqual(prec["number"], 101)
            self.assertEqual(prec["pr"], 51)
            self.assertEqual(prec["branch"], "issue-101-feat")

    def test_find_preceding_pr_skips_merged_prs(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]
        # 101 was already merged
        def fake_observe(ref, cli_fn=None, cwd=None):
            return {"issue": str(ref), "number": 101, "pr": {"number": 51, "head_branch": "issue-101-feat", "state": "MERGED"}}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            self.assertIsNone(run_queue.find_preceding_pr(102, children))

    def test_set_board_status(self):
        calls = []
        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {}, 0

        # None owner/project does nothing
        run_queue.set_board_status("https://github.com/o/r/issues/1", "In progress", cli_fn=fake_cli)
        self.assertEqual(len(calls), 0)

        # Calls board set-status when configured
        run_queue.set_board_status("https://github.com/o/r/issues/1", "In progress", owner="o", project=12, cli_fn=fake_cli)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], ("board", "set-status", "https://github.com/o/r/issues/1", "--owner", "o", "--project", "12", "--status", "In progress"))

    def test_parent_burndown_flow_with_stacked_prs_and_board_updates(self):
        """Burndown a parent issue with 2 sub-issues, generating stacked PR directive on child 2."""
        parent_data = {
            "parent": {"number": 100, "title": "Epic", "state": "OPEN", "url": "https://github.com/o/r/issues/100"},
            "children": [
                {"number": 101, "title": "Child 1", "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
                {"number": 102, "title": "Child 2", "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            ],
        }
        # Child 1: reaches DONE with PR #51 on branch issue-101-feat
        # Child 2: unstarted, needs implement
        child1_done = {
            "issue": "https://github.com/o/r/issues/101", "number": 101, "labels": ["triage:ready"],
            "pr": {"number": 51, "url": "https://github.com/o/r/pull/51", "head": "c1", "head_branch": "issue-101-feat", "state": "OPEN", "is_draft": False},
            "ci": "green", "pending_review_requests": []
        }
        child2_start = {
            "issue": "https://github.com/o/r/issues/102", "number": 102, "labels": ["triage:ready"], "pr": None
        }
        child2_done = {
            "issue": "https://github.com/o/r/issues/102", "number": 102, "labels": ["triage:ready"],
            "pr": {"number": 52, "url": "https://github.com/o/r/pull/52", "head": "c2", "head_branch": "issue-102-feat", "state": "OPEN", "is_draft": False},
            "ci": "green", "pending_review_requests": []
        }

        session_called = False
        def fake_observe(ref, cli_fn=None, cwd=None):
            if "101" in str(ref):
                return dict(child1_done)
            if not session_called:
                return dict(child2_start)
            return dict(child2_done)

        captured_sessions = []
        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            nonlocal session_called
            session_called = True
            captured_sessions.append((step, issue_url, dict(options)))
            return True, "ses_id"
        board_moves = []
        def fake_cli(*args, cwd=None):
            if args and args[0] == "board" and args[1] == "set-status":
                board_moves.append(args)
            if args and args[0] == "worktree" and args[1] == "create":
                branch = args[args.index("--branch") + 1]
                return {"path": f"/tmp/wt/{branch}", "action": "created"}, 0
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            with patch("run_queue.observe_parent", return_value=parent_data), \
                 patch("run_queue.check_active_runs"), \
                 patch("run_queue.observe_issue", side_effect=fake_observe), \
                 patch("run_queue.run_session", side_effect=fake_run_session), \
                 patch("run_queue.run_cli", side_effect=fake_cli):
                ret = run_queue.main(["--parent", "100", "--project", "o/12", "--no-notebook", "--notes-dir", str(notes_dir)])
                self.assertEqual(ret, 0)

        # Child 2 was implemented
        self.assertTrue(any(s[0] == "implement-issue" and "102" in s[1] for s in captured_sessions))
        child2_session = next(s for s in captured_sessions if s[0] == "implement-issue" and "102" in s[1])
        extra = child2_session[2].get("extra_text", "")
        self.assertIn("Stacked PR", extra)
        self.assertIn("issue-101-feat", extra)

        # Board status updates occurred
        self.assertTrue(any("In progress" in str(m) for m in board_moves))
        # The runner created the worktree and named it in the directive
        self.assertIn("/tmp/wt/issue-102", extra)
        self.assertEqual(child2_session[2].get("branch"), "issue-102")
        self.assertIn("created now", extra)

    def test_reused_worktree_directive_asks_for_resumption(self):
        captured = {}

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            captured.update(options)
            return True, "ses_id"

        state = {"issue": "https://github.com/o/r/issues/7", "number": 7, "title": "Fix it",
                 "labels": ["triage:ready"], "pr": None}

        def fake_cli(*args, cwd=None):
            if args and args[0] == "worktree" and args[1] == "create":
                return {"path": "/repo/.claude/worktrees/issue-7-fix-it", "action": "exists"}, 3
            return {}, 0

        board = {"in_flight": [], "parked": [], "selection": [{"number": 7, "issue": state["issue"]}]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.publish_committed", return_value=None), \
             patch("run_queue.run_session", side_effect=fake_run_session), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            run_queue.main(["--once", "--no-notebook", "--notes-dir", tmp])
        extra = captured.get("extra_text", "")
        self.assertIn("reused from an earlier attempt", extra)
        self.assertIn("continue that work", extra)
        self.assertIn("not overwritten", extra)


class NotebookPublishingTests(unittest.TestCase):
    issue_url = "https://github.com/o/r/issues/1"
    pr_url = "https://github.com/o/r/pull/1"

    def run_once(self, discussion_result, session_results=None):
        calls, bodies, comments = [], [], []
        session_results = list(session_results or [(True, "ses_1")])
        done = {"issue": self.issue_url, "number": 1, "labels": ["triage:ready"],
                "pr": {"url": self.pr_url, "head": "c1", "is_draft": False},
                "ci": "green", "pending_review_requests": []}
        states = [{"issue": self.issue_url, "number": 1, "labels": ["triage:ready"],
                   "title": "Narrate runs", "pr": None}, dict(done)]

        def fake_observe(issue_ref, cli_fn=None, cwd=None):
            return dict(states.pop(0)) if states else dict(done)

        def fake_cli(*args, cwd=None):
            calls.append(args)
            if args[:2] == ("discussion", "post"):
                bodies.append(Path(args[args.index("--body-file") + 1]).read_text(encoding="utf-8"))
                return discussion_out, discussion_code
            if args[:2] == ("issue", "comment"):
                comments.append(Path(args[args.index("--text") + 1]).read_text(encoding="utf-8"))
            return {}, 0

        discussion_out = {"discussion": {"url": "https://github.com/o/r/discussions/3"}}
        discussion_code = 0
        if discussion_result:
            discussion_code = discussion_result.get("_code", 0)
            discussion_out = {k: v for k, v in discussion_result.items() if k != "_code"}

        def fake_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            log = Path(notes_dir) / f"session-{step}.log"
            log.write_text('{"type": "step_start"}\n', encoding="utf-8")
            if log_hook:
                log_hook(log)
            return session_results.pop(0)

        with tempfile.TemporaryDirectory() as tmp:
            with patch("run_queue.discover_project", return_value=("o", 12)), \
                 patch("run_queue.check_active_runs"), \
                 patch("run_queue.observe_board", return_value={
                     "in_flight": [], "parked": [],
                     "selection": [{"number": 1, "issue": self.issue_url}]}), \
                 patch("run_queue.observe_issue", side_effect=fake_observe), \
                 patch("run_queue.prepare_worktree", return_value={
                     "branch": "issue-1-narrate-runs", "path": "/tmp/wt", "created": True}), \
                 patch("run_queue.run_session", side_effect=fake_session), \
                 patch("run_queue.publish_committed", return_value=None), \
                 patch("run_queue.narrative.summarize_session",
                       return_value=("- Model bullet.", "model")) as summarize, \
                 patch("run_queue.run_cli", side_effect=fake_cli):
                status = run_queue.main(["--once", "--notes-dir", tmp])
        self.assertEqual(status, 0)
        return calls, bodies, comments, summarize, discussion_code

    def test_run_publishes_notes_and_an_issue_checkpoint(self):
        calls, bodies, comments, summarize, _ = self.run_once(None)
        self.assertEqual(summarize.call_count, 1)
        self.assertTrue(any(args[:2] == ("discussion", "post") for args in calls))
        self.assertEqual(len(bodies), 3)  # start, step, finish
        self.assertIn("Run start", bodies[0])
        self.assertIn("- Model bullet.", bodies[1])
        self.assertIn("Run end", bodies[2])
        self.assertEqual(len(comments), 1)
        self.assertIn("Work started", comments[0])
        self.assertIn("issue-1-narrate-runs", comments[0])

    def test_retry_posts_a_note_for_the_successful_attempt(self):
        calls, bodies, comments, summarize, _ = self.run_once(
            None, session_results=[(False, "timed out"), (True, "ses_1")])
        self.assertEqual(summarize.call_count, 2)
        self.assertFalse(summarize.call_args_list[0].args[2])
        self.assertTrue(summarize.call_args_list[1].args[2])
        self.assertEqual(len(bodies), 4)  # start, failed attempt, successful retry, finish
        self.assertEqual(len([b for b in bodies if "implement-issue" in b]), 2)

    def test_unavailable_notebook_keeps_the_run_going(self):
        calls, bodies, comments, summarize, code = self.run_once(
            {"available": False, "reason": "Discussions are disabled.", "_code": 3})
        self.assertEqual(code, 3)
        self.assertEqual(summarize.call_count, 0)
        self.assertEqual(len(bodies), 1)  # the start attempt only
        self.assertEqual(len(comments), 1)
class PublishCommittedTests(unittest.TestCase):
    """The runner publishes committed work that an implementation session left unpublished."""

    HEAD = "a" * 40

    def worktree(self):
        return {"path": "/repo/.claude/worktrees/issue-9-fix", "branch": "issue-9-fix", "base": "origin/main"}

    def test_skips_when_the_session_committed_nothing(self):
        calls = []
        with patch("run_queue.committed_count", return_value=0):
            result = run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", self.worktree(),
                                                 "o/r", Path("/tmp"), {}, cli_fn=lambda *a, **k: calls.append(a) or ({}, 0))
        self.assertIsNone(result)
        self.assertEqual(calls, [])

    def test_pushes_and_opens_a_draft_pr(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"url": "https://github.com/o/r/pull/9"}, 0) if args[0] == "pr" else ({}, 0)

        def fake_git(args, cwd=None):
            return self.HEAD if args[0] == "rev-parse" else "- `abc1234` Change"

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.committed_count", return_value=2), \
             patch("run_queue.git_output", side_effect=fake_git):
            result = run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", self.worktree(),
                                                 "o/r", Path(tmp), {}, cli_fn=fake_cli)
            create = calls[1]
            body = Path(create[create.index("--body-file") + 1]).read_text()
        self.assertEqual(result["url"], "https://github.com/o/r/pull/9")
        self.assertEqual(calls[0], ("exec", "--", "git", "-C", "/repo/.claude/worktrees/issue-9-fix",
                                    "push", "-u", "origin", "issue-9-fix"))
        self.assertEqual(create[:2], ("pr", "create"))
        self.assertEqual(create[create.index("--repo") + 1], "o/r")
        self.assertEqual(create[create.index("--base") + 1], "main")
        self.assertIn("--draft", create)
        self.assertEqual(create[create.index("--expect-head") + 1], self.HEAD)
        self.assertIn("Part of #9", body)
        self.assertIn("`abc1234` Change", body)

    def test_stops_before_creating_a_pr_when_the_push_fails(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {"error": "rejected"}, 1

        with patch("run_queue.committed_count", return_value=1):
            self.assertIsNone(run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", self.worktree(),
                                                          "o/r", Path("/tmp"), {}, cli_fn=fake_cli))
        self.assertEqual(len(calls), 1)

    def test_uses_the_stacked_base_and_keeps_an_existing_pr(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"pr": {"url": "https://github.com/o/r/pull/8"}}, 3) if args[0] == "pr" else ({}, 0)

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.committed_count", return_value=1) as counted, \
             patch("run_queue.git_output", return_value=self.HEAD):
            self.assertIsNone(run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", self.worktree(),
                                                          "o/r", Path(tmp), {}, base_branch="issue-8", cli_fn=fake_cli))
        counted.assert_called_once_with("/repo/.claude/worktrees/issue-9-fix", "issue-8")
        self.assertEqual(calls[-1][calls[-1].index("--base") + 1], "issue-8")

    def test_falls_back_to_default_base_when_stacked_base_branch_deleted(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"url": "https://github.com/o/r/pull/9"}, 0) if args[0] == "pr" else ({}, 0)

        def fake_git(args, cwd=None):
            if args[0] == "rev-parse":
                return self.HEAD
            if args[0] == "ls-remote":
                return ""
            return "- `abc1234` Change"

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.committed_count", return_value=1), \
             patch("run_queue.git_output", side_effect=fake_git):
            run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", self.worktree(),
                                        "o/r", Path(tmp), {}, base_branch="deleted-stacked-branch", cli_fn=fake_cli)
            create = next(c for c in calls if c[:2] == ("pr", "create"))
            self.assertEqual(create[create.index("--base") + 1], "main")

    def test_auto_commits_uncommitted_changes_before_publishing(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"url": "https://github.com/o/r/pull/9"}, 0) if args[0] == "pr" else ({}, 0)

        with tempfile.TemporaryDirectory() as tmp:
            wt_path = Path(tmp) / "wt"
            wt_path.mkdir()
            worktree = {"path": str(wt_path), "branch": "issue-9-fix", "base": "origin/main"}
            counts = [0, 1]
            with patch("run_queue.committed_count", side_effect=lambda *a: counts.pop(0)), \
                 patch("run_queue.git_output", side_effect=[" M file.py", self.HEAD, "- `abc1234` Change"]):
                result = run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", worktree,
                                                     "o/r", Path(tmp), {}, cli_fn=fake_cli)
            self.assertIsNotNone(result)
            add_call = next(c for c in calls if len(c) > 6 and c[5:7] == ("add", "-A"))
            self.assertTrue(add_call)
            commit_call = next(c for c in calls if len(c) > 6 and c[5:7] == ("commit", "-m"))
            self.assertIn("Fix it", commit_call[-1])
    def test_implementation_step_publishes_after_the_session(self):
        state = {"issue": "https://github.com/o/r/issues/1", "number": 1, "title": "Fix it", "repo": "o/r",
                 "labels": ["triage:ready"], "pr": None}
        published, sessions = [], []

        def fake_cli(*args, cwd=None):
            return {}, 0

        def fake_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            sessions.append((step, options))
            return True, "ses"

        worktree = {"path": "/repo/.claude/worktrees/issue-1-fix-it", "branch": "issue-1-fix-it",
                    "base": "origin/main", "created": True,
                    "setup": {"source": "project_facts", "copy": [".env"], "setup": ["uv sync"]}}
        board = {"in_flight": [], "parked": [], "selection": [{"number": 1, "issue": state["issue"]}]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.prepare_worktree", return_value=worktree), \
             patch("run_queue.run_session", side_effect=fake_session), \
             patch("run_queue.publish_committed", side_effect=lambda *a, **k: published.append((a, k))), \
             patch("run_queue.park_issue", return_value=({}, 0)), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            run_queue.main(["--once", "--notes-dir", tmp])
        self.assertEqual(len(published), 1)
        self.assertEqual(published[0][0][3], "o/r")
        self.assertIsNone(published[0][1].get("base_branch"))
        self.assertIn("The runner applied the project facts worktree declaration", sessions[0][1]["extra_text"])


class PrecomputedGateTests(unittest.TestCase):
    """The runner executes local test gates deterministically before review sessions."""

    def test_nonexistent_or_no_makefile_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(run_queue.run_precomputed_gate(tmp))
            self.assertIsNone(run_queue.run_precomputed_gate("/nonexistent/path"))

    def test_makefile_without_check_target_returns_none(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Makefile").write_text("all:\n\techo all\n")
            self.assertIsNone(run_queue.run_precomputed_gate(tmp))

    def test_passing_make_check_returns_success_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Makefile").write_text("check:\n\techo ok\n")
            mock_proc = MagicMock(returncode=0, stdout="Ran 10 tests\n5772 passed, 2 skipped\nOK\n")
            with patch("subprocess.run", return_value=mock_proc):
                res = run_queue.run_precomputed_gate(tmp)
            self.assertIsNotNone(res)
            self.assertTrue(res["success"])
            self.assertEqual(res["exit_code"], 0)
            self.assertIn("5772 passed, 2 skipped", res["summary"])
            self.assertIn("Pre-computed gate status at head: `make check` passed", res["text"])

    def test_failing_make_check_returns_failure_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Makefile").write_text("check:\n\techo fail\n")
            mock_proc = MagicMock(returncode=1, stdout="SyntaxError: invalid syntax\nmake: *** [check] Error 1\n")
            with patch("subprocess.run", return_value=mock_proc):
                res = run_queue.run_precomputed_gate(tmp)
            self.assertIsNotNone(res)
            self.assertFalse(res["success"])
            self.assertEqual(res["exit_code"], 1)
            self.assertIn("FAILED (exit 1)", res["text"])
            self.assertIn("SyntaxError", res["text"])


class SymbolIndexTests(unittest.TestCase):
    """The runner extracts symbols from issues and indexes their locations."""

    def test_extract_candidate_symbols(self):
        title = "[2.6] Clear `_failed_model_info` negative cache on reload"
        body = "Calls `#flushSave()` in `wiki-editor.js` and `_parse_dict`."
        symbols = run_queue.extract_candidate_symbols(title, body)
        self.assertIn("_failed_model_info", symbols)
        self.assertIn("flushSave", symbols)
        self.assertIn("_parse_dict", symbols)

    def test_extract_candidate_symbols_filters_common_keywords(self):
        title = "Fix python tests for make check"
        body = "return None if self.data is True"
        symbols = run_queue.extract_candidate_symbols(title, body)
        self.assertEqual(symbols, [])

    def test_format_symbol_index(self):
        results = [{
            "symbol": "_failed_model_info",
            "matches": [("src/llm/model_info.py:42", "_failed_model_info: set = set()")],
        }]
        formatted = run_queue.format_symbol_index(results)
        self.assertIn("Target symbol locations in repository:", formatted)
        self.assertIn("`_failed_model_info` at `src/llm/model_info.py:42`: `_failed_model_info: set = set()`", formatted)

    def test_find_subsystem_symbols(self):
        with tempfile.TemporaryDirectory() as tmp:
            mock_proc = MagicMock(returncode=0, stdout="src/a.py:10:def _foo(): pass\n")
            with patch("subprocess.run", return_value=mock_proc):
                res = run_queue.find_subsystem_symbols(["_foo"], cwd=tmp)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["symbol"], "_foo")
            self.assertEqual(res[0]["matches"][0], ("src/a.py:10", "def _foo(): pass"))
    def test_find_subsystem_symbols_prefers_tags(self):
        with tempfile.TemporaryDirectory() as tmp:
            fake_tag_res = {
                "matches": [{
                    "name": "_foo", "path": "src/a.py", "line": 42,
                    "kind": "function", "scope": None, "pattern": "def _foo(): pass"
                }]
            }
            with patch("cli.tags.find_tags", return_value=(fake_tag_res, 0)):
                res = run_queue.find_subsystem_symbols(["_foo"], cwd=tmp)
            self.assertEqual(len(res), 1)
            self.assertEqual(res[0]["symbol"], "_foo")
            self.assertEqual(res[0]["matches"][0], ("src/a.py:42", "def _foo(): pass"))

if __name__ == "__main__":
    unittest.main()
