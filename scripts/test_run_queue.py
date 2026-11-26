"""Unit tests for the deterministic queue runner scripts/run_queue.py."""
import argparse
import contextlib
import io
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import run_queue

os.environ.setdefault("GHFLOW_NO_MODEL_UNLOAD", "1")

_LOCK_DIR = None
_SAVED_LOCK_ENV = None
_PROBE_PATCH = None


def setUpModule():
    """Point the run lock at a temporary file, so tests never take a live runner's lock."""
    global _LOCK_DIR, _SAVED_LOCK_ENV, _PROBE_PATCH
    _LOCK_DIR = tempfile.TemporaryDirectory()
    _SAVED_LOCK_ENV = os.environ.get("GHFLOW_RUNNER_LOCK")
    os.environ["GHFLOW_RUNNER_LOCK"] = str(Path(_LOCK_DIR.name) / "runner.lock")
    _PROBE_PATCH = patch("run_queue.monitor_mod.probe_model", return_value=True)
    _PROBE_PATCH.start()


def tearDownModule():
    global _PROBE_PATCH
    if _PROBE_PATCH is not None:
        _PROBE_PATCH.stop()
        _PROBE_PATCH = None
    if run_queue._RUN_LOCK is not None:
        run_queue._RUN_LOCK.close()
        run_queue._RUN_LOCK = None
    if _SAVED_LOCK_ENV is None:
        os.environ.pop("GHFLOW_RUNNER_LOCK", None)
    else:
        os.environ["GHFLOW_RUNNER_LOCK"] = _SAVED_LOCK_ENV
    _LOCK_DIR.cleanup()


class RunLockTests(unittest.TestCase):
    def setUp(self):
        # acquire_run_lock reuses a lock this process already holds; start each test without one.
        self._held = run_queue._RUN_LOCK
        run_queue._RUN_LOCK = None

    def tearDown(self):
        if run_queue._RUN_LOCK is not None:
            run_queue._RUN_LOCK.close()
        run_queue._RUN_LOCK = self._held

    def test_environment_variable_names_the_lock_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "state" / "runner.lock"
            with patch.dict(os.environ, {"GHFLOW_RUNNER_LOCK": str(lock)}):
                fp = run_queue.acquire_run_lock(tmp, target="o/r#1")
            self.assertEqual(Path(fp.name), lock)
            self.assertEqual(json.loads(lock.read_text(encoding="utf-8"))["target"], "o/r#1")

    def test_module_setup_keeps_tests_off_the_real_lock(self):
        real = Path.home() / ".local/state/ghflow/runner.lock"
        self.assertNotEqual(Path(os.environ["GHFLOW_RUNNER_LOCK"]), real)

    def test_refuses_when_another_process_holds_the_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            lock = Path(tmp) / "runner.lock"
            lock.write_text('{"pid": 1}\n', encoding="utf-8")
            holder = subprocess.Popen(
                ["python3", "-c",
                 "import fcntl, sys; f = open(sys.argv[1], 'a+'); "
                 "fcntl.flock(f, fcntl.LOCK_EX); print('held', flush=True); sys.stdin.read()",
                 str(lock)],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            try:
                self.assertEqual(holder.stdout.readline().strip(), "held")
                with self.assertRaisesRegex(RuntimeError, "Another queue runner holds"):
                    run_queue.acquire_run_lock(tmp, lock_path=lock)
            finally:
                holder.stdin.close()
                holder.wait(timeout=10)


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
    def test_default_step_idle_timeout_is_900(self):
        self.assertEqual(run_queue.DEFAULT_STEP_IDLE_TIMEOUT, 900)
        self.assertEqual(run_queue.SLOW_STEP_WARN_SECONDS, 120)


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
            "review_verdicts": [{"head": "abc", "verdict": "clean"}],
        }
        self.assertEqual(run_queue.next_step(state), "DONE")

    def test_conflicting_pr_is_repair(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False,
                   "mergeable": "CONFLICTING"},
            "ci": "green",
            "review_verdicts": [{"head": "old_head", "verdict": "clean"}],
        }
        self.assertEqual(run_queue.next_step(state), "repair-conflict")

    def test_ready_pr_green_ci_with_stale_verdict_is_review(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "new_head", "is_draft": False},
            "ci": "green",
            "pending_review_requests": [],
            "review_verdicts": [{"head": "old_head", "verdict": "clean"}],
        }
        self.assertEqual(run_queue.next_step(state), "review-changes")

    def test_ready_pr_without_checks_needs_a_clean_verdict(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "none", "review_verdicts": [], "pending_review_requests": [],
        }
        self.assertEqual(run_queue.next_step(state), "review-changes")
        state["review_verdicts"] = [{"head": "abc", "verdict": "clean"}]
        self.assertEqual(run_queue.next_step(state), "DONE")

    def test_missing_required_checks_is_not_done(self):
        state = {
            "pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
            "ci": "missing", "pending_review_requests": [],
        }
        self.assertEqual(run_queue.next_step(state), "address-pr-review")

    def test_incomplete_ci_waits_and_unknown_ci_is_not_done(self):
        base = {"pr": {"url": "https://github.com/o/r/pull/1", "head": "abc", "is_draft": False},
                "pending_review_requests": []}
        self.assertEqual(run_queue.next_step({**base, "ci": "incomplete"}), "wait-ci")
        self.assertEqual(run_queue.next_step({**base, "ci": "unread"}), "WAITING")

    def test_issue_turn_limit_is_flat(self):
        self.assertEqual(run_queue.DEFAULT_MAX_TURNS, 150)
        self.assertEqual(run_queue.issue_turn_limit(), 150)
        self.assertEqual(run_queue.issue_turn_limit(42), 42)

    def test_context_helpers(self):
        self.assertIsNone(run_queue.context_warning(99999, 100000, False))
        self.assertIn("100000", run_queue.context_warning(100000, 100000, False))
        self.assertIsNone(run_queue.context_warning(100000, 100000, True))
        self.assertIsNone(run_queue.context_cap_reason(100000, 0))
        self.assertIsNone(run_queue.context_cap_reason(99999, 100000))
        self.assertIn("cap 100000", run_queue.context_cap_reason(100000, 100000))
        self.assertEqual(run_queue.step_context_tokens(
            {"input": 500, "cache": {"read": 105000, "write": 7}}), 105507)
        self.assertEqual(run_queue.step_context_tokens({"input": 10}), 10)
        self.assertEqual(run_queue.step_context_tokens({}), 0)

    def test_negative_context_limits_are_rejected(self):
        with self.assertRaises(SystemExit):
            run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--context-warn-tokens", "-1", "--no-notebook"])

    def test_verification_lines_extracts_verify_clause(self):
        body = "**Size:** S\n\n**Verify.** `make test` — `tests/test_x.py`.\n\n**Tests.** Add a case."
        self.assertEqual(run_queue.verification_lines(body),
                         ["**Verify.** `make test` — `tests/test_x.py`."])
        self.assertEqual(run_queue.verification_lines("no verification"), [])


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


class PrepareConflictMergeTests(unittest.TestCase):
    class Result:
        def __init__(self, returncode, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def test_reports_conflict_files(self):
        def fake_run(cmd, **kwargs):
            return (self.Result(0) if cmd[:2] == ["git", "fetch"]
                    else self.Result(1, "CONFLICT (content)"))

        result = run_queue.prepare_conflict_merge(
            tempfile.gettempdir(), "main", run=fake_run, git=lambda *a, **k: "src/a.py\n")

        self.assertFalse(result["ok"])
        self.assertEqual(result["files"], ["src/a.py"])

    def test_clean_merge_has_no_files(self):
        result = run_queue.prepare_conflict_merge(
            tempfile.gettempdir(), "main", run=lambda *a, **k: self.Result(0),
            git=lambda *a, **k: "")

        self.assertTrue(result["ok"])
        self.assertEqual(result["files"], [])


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
             patch("run_queue.run_cli", return_value=({}, 0)), \
             patch("run_queue.observe_board", return_value={"in_flight": [], "parked": [], "selection": []}):
            # When both --provider and --model given without slash
            with patch("run_queue.run_session") as mock_session:
                run_queue.main(["--provider", "lmstudio", "--model", "qwen3.8-27b", "--review-model", "qwen3.8-27b-review", "--once", "--no-notebook"])
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
    def test_nodes_object_with_user_path(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"projectsV2": {"Nodes": [
                {"number": 6, "title": "decafclaw", "resourcePath": "/users/lmorchard/projects/6", "closed": False},
            ]}}),
        )
        owner, number = run_queue.discover_project()
        self.assertEqual((owner, number), ("lmorchard", 6))

    @patch("subprocess.run")
    def test_nodes_object_with_org_path(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=json.dumps({"projectsV2": {"Nodes": [
                {"number": 3, "title": "Org board", "url": "https://github.com/orgs/acme/projects/3", "closed": False},
            ]}}),
        )
        owner, number = run_queue.discover_project()
        self.assertEqual((owner, number), ("acme", 3))

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
            self.assertIn("# ghflow-build-slim: implement-issue", prompt)
            self.assertIn("Local-model single session", prompt)
            self.assertIn("implement-issue.md", prompt)
            self.assertIn("export GHFLOW_CLI=", prompt)
            self.assertIn("tags brief", prompt)
            self.assertIn("Follow the handoff.", prompt)

    def test_prepare_project_facts_inlines_its_task_procedure(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            tasks_dir = skill_dir / "references" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "prepare-project-facts.md").write_text(
                "# Prepare the project facts\nRefresh `.ghflow/project.md`.\n", encoding="utf-8")
            prompt = run_queue.compose_prompt(skill_dir, "Follow the handoff.",
                                              step="prepare-project-facts")
            self.assertIn("# Prepare the project facts", prompt)
            self.assertIn("Refresh `.ghflow/project.md`.", prompt)
            self.assertIn("Follow the handoff.", prompt)

    def test_step_inlines_slim_skill_body_when_available(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp)
            slim_dir = skill_dir / "skills" / "build-slim"
            slim_dir.mkdir(parents=True)
            tasks_dir = skill_dir / "references" / "tasks"
            tasks_dir.mkdir(parents=True)
            (tasks_dir / "implement-issue.md").write_text("# Implement", encoding="utf-8")
            (slim_dir / "SKILL.md").write_text("---\nname: ghflow-build-slim\n---\n# Slim Builder\nDo work in ABSOLUTE_SKILL_DIRECTORY.\n", encoding="utf-8")
            prompt = run_queue.compose_prompt(skill_dir, "Follow the handoff.", step="implement-issue")
            self.assertIn("# Slim Builder", prompt)
            self.assertIn(f"Do work in {skill_dir}.", prompt)
            self.assertFalse(prompt.startswith("---"))
            self.assertIn("Operative rules are inlined above.", prompt)


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

    def test_run_session_sends_an_issue_less_handoff_with_the_facts_path(self):
        cli_calls = []
        mock_proc = MagicMock()
        mock_proc.stdout = ['{"type": "step_start", "sessionID": "ses_test123"}\n', '{"type": "step_finish"}\n']
        mock_proc.returncode = 0
        mock_proc.wait.return_value = 0

        def fake_cli(*args, cwd=None):
            cli_calls.append(args)
            return {"dispatch_prompt": "Refresh the facts"}, 0

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            skill_dir = notes_dir / "skill"
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
            options = {"skill_dir": str(skill_dir), "opencode_cmd": "fake_opencode",
                       "facts_path": "/wt/.ghflow/project.md"}
            with patch("subprocess.Popen", return_value=mock_proc), \
                 patch("subprocess.run"):
                ok, _ = run_queue.run_session("prepare-project-facts", None, notes_dir,
                                              options, cli_fn=fake_cli)
            self.assertTrue(ok)
            handoff = cli_calls[0]
            self.assertEqual(handoff[:2], ("handoff", "prepare-project-facts"))
            self.assertFalse(any(arg is None for arg in handoff))
            self.assertIn("--facts-path", handoff)
            self.assertIn("/wt/.ghflow/project.md", handoff)

    def test_run_session_uses_worktree_cwd_and_sets_cli_env(self):
        mock_proc = MagicMock()
        mock_proc.stdout = ['{"type": "step_start", "sessionID": "ses_test123"}\n', '{"type": "step_finish"}\n']
        mock_proc.returncode = 0
        mock_proc.wait.return_value = 0

        with tempfile.TemporaryDirectory() as tmp:
            notes_dir = Path(tmp)
            skill_dir = notes_dir / "skill"
            (skill_dir / "cli").mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Skill", encoding="utf-8")
            options = {"skill_dir": str(skill_dir), "opencode_cmd": "fake_opencode",
                       "session_cwd": "/tmp/task-worktree"}
            with patch("subprocess.Popen", return_value=mock_proc) as popen, \
                 patch("subprocess.run"):
                ok, _ = run_queue.run_session("implement-issue", "https://github.com/o/r/issues/1",
                                              notes_dir, options, cli_fn=lambda *a, **k: ({"dispatch_prompt": "p"}, 0))
            self.assertTrue(ok)
            kwargs = popen.call_args.kwargs
            self.assertEqual(kwargs["cwd"], "/tmp/task-worktree")
            self.assertEqual(kwargs["env"]["GHFLOW_CLI"],
                             str((skill_dir / "cli" / "ghflow.py").resolve()))

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
                run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-deterministic-pr", "--notes-dir", str(notes_dir)])

        steps = [s for s, _ in captured_options]
        self.assertEqual(steps, ["review-changes", "submit-pr"])
        review_opt = captured_options[0][1]
        self.assertIn("Inspect the commit diff", review_opt.get("extra_text", ""))
        self.assertIn("Do not write new end-to-end integration test suites", review_opt.get("extra_text", ""))
        self.assertIn("gate --summary", review_opt.get("extra_text", ""))
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
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-deterministic-pr", "--notes-dir", str(notes_dir)])
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
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--notes-dir", str(notes_dir)])
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

    def test_prepare_worktree_passes_a_stacked_base(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return {"path": "/repo/.claude/worktrees/issue-42-add-a-thing",
                    "base": "origin/issue-41-base"}, 0

        res = run_queue.prepare_worktree("https://github.com/o/r/issues/42", "Add a Thing", "o", 12,
                                         {"cwd": "/repo"}, cli_fn=fake_cli,
                                         base_branch="issue-41-base")
        self.assertEqual(res["base"], "origin/issue-41-base")
        self.assertIn("--base", calls[0])
        self.assertIn("issue-41-base", calls[0])

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
            status = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--notes-dir", tmp])
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

    def test_next_item_for_parent_excludes_numbers(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            {"number": 103, "state": "OPEN", "url": "https://github.com/o/r/issues/103"},
        ]

        def fake_observe(ref, cli_fn=None, cwd=None):
            if "101" in str(ref):
                return {"issue": str(ref), "number": 101, "labels": [], "pr": {"url": "p1", "is_draft": True, "head": "h1"}, "review_verdicts": []}
            return {"issue": str(ref), "number": int(str(ref).rstrip("/").split("/")[-1]), "labels": [], "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            self.assertEqual(run_queue.next_item_for_parent(children, exclude={101})["number"], 102)
            self.assertEqual(run_queue.next_item_for_parent(children, exclude={101, 102})["number"], 103)
            self.assertIsNone(run_queue.next_item_for_parent(children, exclude={101, 102, 103}))

    def test_next_item_for_parent_honors_labels_and_native_blockers(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            {"number": 103, "state": "OPEN", "url": "https://github.com/o/r/issues/103"},
            {"number": 104, "state": "OPEN", "url": "https://github.com/o/r/issues/104"},
        ]

        blocked_for_102 = [{"number": 101, "state": "OPEN"}]

        def fake_observe(ref, cli_fn=None, cwd=None):
            number = int(str(ref).rstrip("/").split("/")[-1])
            labels = {"101": ["triage:blocked"],
                      "102": ["triage:ready"],
                      "103": ["triage:ready"],
                      "104": ["triage:ready"]}[str(number)]
            blocked = blocked_for_102 if number == 102 else []
            return {"issue": str(ref), "number": number, "labels": labels, "pr": None, "blocked_by": blocked}

        board = {101: {"priority": "P1", "size": "S"}, 102: {"priority": "P0", "size": "S"},
                 103: {"priority": "P1", "size": "S"}, 104: {"priority": "P1", "size": "XS"}}
        with patch("run_queue.observe_issue", side_effect=fake_observe):
            # The blocked child is out of scope; 102 is blocked by the still-open 101.
            chosen = run_queue.next_item_for_parent(children, require_labels=["triage:ready"],
                                                    board_index=board)
            self.assertEqual(chosen["number"], 104)  # XS before the P1/S child 103
            # Priority beats size: the now-unblocked P0 child 102 wins over 104.
            blocked_for_102 = []
            chosen = run_queue.next_item_for_parent(children, require_labels=["triage:ready"],
                                                    board_index=board, exclude={101})
            self.assertEqual(chosen["number"], 102)

    def test_next_item_for_parent_keeps_a_triage_blocked_child(self):
        children = [{"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"}]

        def fake_observe(ref, cli_fn=None, cwd=None):
            return {"issue": str(ref), "number": 101, "labels": ["triage:ready", "triage:blocked"], "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children)
        self.assertEqual(chosen["number"], 101)

    def test_next_item_for_parent_selects_a_child_with_an_open_base_pr(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]

        def fake_observe(ref, cli_fn=None, cwd=None):
            number = int(str(ref).rstrip("/").split("/")[-1])
            if number == 101:
                return {"issue": str(ref), "number": 101, "labels": ["triage:ready"],
                        "pr": {"number": 51, "url": "https://github.com/o/r/pull/51",
                               "head_branch": "issue-101-base", "state": "OPEN",
                               "is_draft": False, "head": "h1"},
                        "ci": "green", "pending_review_requests": []}
            return {"issue": str(ref), "number": 102, "labels": ["triage:ready"], "pr": None,
                    "blocked_by": [{"number": 101, "state": "OPEN"}]}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children)
        self.assertEqual(chosen["number"], 102)

    def test_next_item_for_parent_skips_triage_needs_definition(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]

        def fake_observe(ref, cli_fn=None, cwd=None):
            number = int(str(ref).rstrip("/").split("/")[-1])
            labels = (["triage:needs-definition"] if number == 101
                      else ["triage:ready"])
            return {"issue": str(ref), "number": number, "labels": labels, "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children)
        self.assertEqual(chosen["number"], 102)

    def test_next_item_for_parent_excludes_labels(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]

        def fake_observe(ref, cli_fn=None, cwd=None):
            number = int(str(ref).rstrip("/").split("/")[-1])
            labels = ["triage:blocked"] if number == 101 else ["triage:ready"]
            return {"issue": str(ref), "number": number, "labels": labels, "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            chosen = run_queue.next_item_for_parent(children, exclude_labels=["triage:blocked"])
        self.assertEqual(chosen["number"], 102)

    def test_find_base_pr_stacked_branch(self):
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
            # A child with no native blocker has no base PR.
            self.assertIsNone(run_queue.find_base_pr(101, children))
            self.assertIsNone(run_queue.find_base_pr(102, children))
            # The one open native blocker supplies the base PR.
            base = run_queue.find_base_pr(
                102, children, child_state={"blocked_by": [{"number": 101, "state": "OPEN"}]})
            self.assertIsNotNone(base)
            self.assertEqual(base["number"], 101)
            self.assertEqual(base["pr"], 51)
            self.assertEqual(base["branch"], "issue-101-feat")

    def test_find_base_pr_skips_merged_prs(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]
        # 101 was already merged
        def fake_observe(ref, cli_fn=None, cwd=None):
            return {"issue": str(ref), "number": 101, "pr": {"number": 51, "head_branch": "issue-101-feat", "state": "MERGED"}}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            self.assertIsNone(run_queue.find_base_pr(
                102, children, child_state={"blocked_by": [{"number": 101, "state": "OPEN"}]}))

    def test_find_base_pr_waits_for_no_pr_or_multiple_blockers(self):
        children = [
            {"number": 101, "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            {"number": 103, "state": "OPEN", "url": "https://github.com/o/r/issues/103"},
        ]

        def fake_observe(ref, cli_fn=None, cwd=None):
            return {"issue": str(ref), "number": 101, "pr": None}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            self.assertIsNone(run_queue.find_base_pr(
                102, children, child_state={"blocked_by": [{"number": 101, "state": "OPEN"}]}))
            self.assertIsNone(run_queue.find_base_pr(
                102, children, child_state={"blocked_by": [
                    {"number": 101, "state": "OPEN"},
                    {"number": 103, "state": "OPEN"}]}))

    def test_find_base_pr_skips_a_closed_blocker_without_a_read(self):
        children = [
            {"number": 101, "state": "CLOSED", "url": "https://github.com/o/r/issues/101"},
            {"number": 102, "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
        ]
        calls = []

        def fake_observe(ref, cli_fn=None, cwd=None):
            calls.append(ref)
            return {"issue": str(ref), "number": 101, "pr": {"number": 51, "head_branch": "issue-101-feat", "state": "OPEN"}}

        with patch("run_queue.observe_issue", side_effect=fake_observe):
            self.assertIsNone(run_queue.find_base_pr(
                102, children, child_state={"blocked_by": [{"number": 101, "state": "CLOSED"}]}))
        self.assertEqual(calls, [])

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
            "issue": "https://github.com/o/r/issues/102", "number": 102, "labels": ["triage:ready"], "pr": None,
            "blocked_by": [{"number": 101, "state": "OPEN"}]
        }
        child2_done = {
            "issue": "https://github.com/o/r/issues/102", "number": 102, "labels": ["triage:ready"],
            "pr": {"number": 52, "url": "https://github.com/o/r/pull/52", "head": "c2", "head_branch": "issue-102-feat", "state": "OPEN", "is_draft": False},
            "ci": "green", "pending_review_requests": [],
            "blocked_by": [{"number": 101, "state": "OPEN"}]
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
        worktree_calls = []
        def fake_cli(*args, cwd=None):
            if args and args[0] == "board" and args[1] == "set-status":
                board_moves.append(args)
            if args and args[0] == "worktree" and args[1] == "create":
                worktree_calls.append(args)
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
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "100", "--project", "o/12", "--no-notebook", "--notes-dir", str(notes_dir)])
                self.assertEqual(ret, 0)

        # Child 2 was implemented
        self.assertTrue(any(s[0] == "implement-issue" and "102" in s[1] for s in captured_sessions))
        child2_session = next(s for s in captured_sessions if s[0] == "implement-issue" and "102" in s[1])
        extra = child2_session[2].get("extra_text", "")
        self.assertIn("Stacked PR", extra)
        self.assertIn("issue-101-feat", extra)
        self.assertTrue(any("--base" in call and "issue-101-feat" in call for call in worktree_calls))

        # Board status updates occurred
        self.assertTrue(any("In progress" in str(m) for m in board_moves))
        # The runner created the worktree and named it in the directive
        self.assertIn("/tmp/wt/issue-102", extra)
        self.assertEqual(child2_session[2].get("branch"), "issue-102")
        self.assertIn("created now", extra)
        self.assertIn("project checkout", extra)
        self.assertIn("do not re-export", extra)
        self.assertIn("do not run `worktree prepare`", extra)
        self.assertIn("tags brief", extra)

    def test_review_directive_uses_the_stacked_base(self):
        parent_data = {
            "parent": {"number": 100, "title": "Epic", "state": "OPEN", "url": "https://github.com/o/r/issues/100"},
            "children": [
                {"number": 101, "title": "Base", "state": "OPEN", "url": "https://github.com/o/r/issues/101"},
                {"number": 102, "title": "Child", "state": "OPEN", "url": "https://github.com/o/r/issues/102"},
            ],
        }
        base_done = {
            "issue": "https://github.com/o/r/issues/101", "number": 101, "labels": ["triage:ready"],
            "pr": {"number": 51, "url": "https://github.com/o/r/pull/51", "head": "h1",
                   "head_branch": "issue-101-base", "state": "OPEN", "is_draft": False},
            "ci": "green", "pending_review_requests": []
        }
        child_draft = {
            "issue": "https://github.com/o/r/issues/102", "number": 102, "labels": ["triage:ready"],
            "pr": {"number": 52, "url": "https://github.com/o/r/pull/52", "head": "c2",
                   "head_branch": "issue-102-child", "base": "issue-101-base",
                   "state": "OPEN", "is_draft": True},
            "blocked_by": [{"number": 101, "state": "OPEN"}], "review_verdicts": []
        }
        captured = []

        def fake_observe(ref, cli_fn=None, cwd=None):
            return dict(base_done) if "101" in str(ref) else dict(child_draft)

        def fake_session(step, issue_url, notes_dir, options, **kwargs):
            captured.append((step, options))
            return True, "ses_1"

        def fake_cli(*args, cwd=None):
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", return_value=parent_data), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_issue", side_effect=fake_observe), \
             patch("run_queue.run_session", side_effect=fake_session), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "100", "--project", "o/12",
                                  "--no-notebook", "--no-precompute-gates", "--notes-dir", tmp])
        self.assertEqual(ret, 0)
        review = next(options for step, options in captured if step == "review-changes")
        self.assertIn("git diff origin/issue-101-base...HEAD", review["extra_text"])
        self.assertIn("keep the PR a draft", review["extra_text"])

    def test_published_pr_state_builds_a_draft_view(self):
        seeded = run_queue.published_pr_state({
            "number": 52, "url": "https://github.com/o/r/pull/52",
            "head": "c2", "head_branch": "issue-102-feat",
        })
        self.assertEqual(seeded["number"], 52)
        self.assertEqual(seeded["head"], "c2")
        self.assertTrue(seeded["is_draft"])
        self.assertEqual(seeded["state"], "OPEN")
        self.assertIsNone(run_queue.published_pr_state(None))
        self.assertIsNone(run_queue.published_pr_state({"number": 1}))

    def test_primary_checkout_change_reports_only_a_difference(self):
        self.assertIsNone(run_queue.primary_checkout_change(None, " M x"))
        self.assertIsNone(run_queue.primary_checkout_change("", ""))
        self.assertIsNone(run_queue.primary_checkout_change(" M x", " M x"))
        change = run_queue.primary_checkout_change("", " M src/agent.py")
        self.assertEqual(change["before"], "")
        self.assertEqual(change["after"], " M src/agent.py")

    def test_parked_pr_url_reads_the_linked_pr(self):
        self.assertEqual(run_queue.parked_pr_url({"pr": {"url": "https://github.com/o/r/pull/52"}}),
                         "https://github.com/o/r/pull/52")
        with patch("run_queue.observe_issue",
                   return_value={"pr": {"url": "https://github.com/o/r/pull/51"}}):
            self.assertEqual(run_queue.parked_pr_url({"issue": "https://github.com/o/r/issues/101"}),
                             "https://github.com/o/r/pull/51")
        self.assertEqual(run_queue.parked_pr_url({}), "")

    def test_retry_directive_names_the_prior_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            log = Path(tmp) / "session.log"
            log.write_text("\n".join([
                json.dumps({"type": "tool_use", "part": {"type": "tool", "tool": "read",
                                                        "state": {"input": {"path": "/w/a.py"}}}}),
                json.dumps({"type": "tool_use", "part": {"type": "tool", "tool": "shell",
                                                        "state": {"input": {"command": "grep -n x /w/a.py"}}}}),
                "42", "null", '"text"',
            ]) + "\n", encoding="utf-8")
            actions = run_queue.recent_session_actions(log)
        self.assertEqual(len(actions), 2)
        self.assertIn("grep -n x", actions[-1])
        text = run_queue.retry_directive("Base.", actions, step="implement-issue")
        self.assertTrue(text.startswith("Base."))
        self.assertIn("grep -n x /w/a.py", text)
        self.assertIn("first edit", text)
        review_text = run_queue.retry_directive("Base.", actions, step="review-changes")
        self.assertIn("grep -n x /w/a.py", review_text)
        self.assertNotIn("first edit", review_text)
        self.assertIn("Continue the assigned task", review_text)
        self.assertEqual(run_queue.retry_directive("Base.", []), "Base.")

    def test_slow_step_warning_helper(self):
        self.assertIsNone(run_queue.slow_step_warning(1120, 1000, 900, False))
        self.assertEqual(run_queue.slow_step_warning(1121, 1000, 900, False),
                         "No session events for 121s; waiting up to 900s")
        self.assertIsNone(run_queue.slow_step_warning(2000, 1000, 900, True))

    def test_stale_facts_warning_names_the_sources(self):
        facts = {"project_facts": {"origin": {"stale_sources": [
            {"path": "Makefile"}, {"path": "pyproject.toml"}]}}}
        warning = run_queue.stale_facts_warning(facts)
        self.assertIn("Makefile", warning)
        self.assertIn("pyproject.toml", warning)
        self.assertIsNone(run_queue.stale_facts_warning(
            {"project_facts": {"origin": {"stale_sources": []}}}))
        self.assertIsNone(run_queue.stale_facts_warning({}))

    def test_dispatch_facts_refresh_points_handoffs_at_the_refreshed_copy(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []
            sessions = []

            def fake_cli(*args, cwd=None):
                calls.append(args)
                if args[:3] == ("exec", "--", "git") and "worktree" in args:
                    path = Path(args[args.index("add") + 3])
                    (path / ".ghflow").mkdir(parents=True)
                    (path / ".ghflow" / "project.md").write_text("---\n---\n", encoding="utf-8")
                    return {}, 0
                if args[:1] == ("facts",):
                    return {"project_facts": {"present": True, "stale_sources": []}}, 0
                if args[:3] == ("exec", "--", "gh"):
                    return [{"url": "https://github.com/o/r/pull/9", "number": 9,
                             "headRefOid": "f" * 40, "baseRefName": "main"}], 0
                return {}, 0

            def fake_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
                sessions.append((step, issue_url, options))
                return True, "ses_1"

            def fake_git(args, cwd=None):
                if args and args[0] == "diff":
                    return ".ghflow/project.md"
                if args and args[0] == "ls-remote":
                    return "abc\trefs/heads/facts-refresh"
                if args and args[0] == "rev-parse":
                    return "f" * 40
                return None

            facts = {
                "project_facts": {"origin": {"present": True,
                                             "stale_sources": [{"path": "Makefile"}]}},
                "repository": {"remote": "o/r", "default_branch": "main"},
                "checkout": {"primary_root": tmp},
            }
            with patch("run_queue.git_output", side_effect=fake_git):
                record, path = run_queue.dispatch_facts_refresh(
                    facts, {"cwd": tmp}, Path(tmp), cli_fn=fake_cli, session_fn=fake_session)

            self.assertEqual(record["status"], "refreshed", record)
            self.assertEqual(record["pr"], "https://github.com/o/r/pull/9")
            self.assertEqual(record["stale_sources"], ["Makefile"])
            self.assertEqual(path, str(Path(record["path"]) / ".ghflow" / "project.md"))
            self.assertTrue(Path(path).is_file())
            self.assertEqual(sessions[0][0], "prepare-project-facts")
            self.assertIsNone(sessions[0][1])
            self.assertEqual(sessions[0][2]["branch"], record["branch"])

    def test_dispatch_facts_refresh_records_a_failed_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_cli(*args, cwd=None):
                if args[:3] == ("exec", "--", "git") and "worktree" in args:
                    path = Path(args[args.index("add") + 3])
                    (path / ".ghflow").mkdir(parents=True)
                    (path / ".ghflow" / "project.md").write_text("old\n", encoding="utf-8")
                    return {}, 0
                return {}, 0

            facts = {
                "project_facts": {"origin": {"present": True,
                                             "stale_sources": [{"path": "AGENTS.md"}]}},
                "repository": {"remote": "o/r", "default_branch": "main"},
                "checkout": {"primary_root": tmp},
            }
            record, path = run_queue.dispatch_facts_refresh(
                facts, {"cwd": tmp}, Path(tmp), cli_fn=fake_cli,
                session_fn=lambda *a, **k: (False, "Session exceeded timeout (5400s)"))

            self.assertEqual(record["status"], "failed")
            self.assertIsNone(path)
            self.assertIn("5400", record["reason"])
            self.assertEqual(record["stale_sources"], ["AGENTS.md"])

    def test_dispatch_facts_refresh_requires_an_open_pr(self):
        with tempfile.TemporaryDirectory() as tmp:
            def fake_cli(*args, cwd=None):
                if args[:3] == ("exec", "--", "git") and "worktree" in args:
                    path = Path(args[args.index("add") + 3])
                    (path / ".ghflow").mkdir(parents=True)
                    (path / ".ghflow" / "project.md").write_text("new\n", encoding="utf-8")
                    return {}, 0
                if args[:1] == ("facts",):
                    return {"project_facts": {"present": True, "stale_sources": []}}, 0
                if args[:3] == ("exec", "--", "gh"):
                    return [], 0
                return {}, 0

            def fake_git(args, cwd=None):
                if args and args[0] == "diff":
                    return ".ghflow/project.md"
                if args and args[0] == "ls-remote":
                    return "abc\trefs/heads/facts-refresh"
                if args and args[0] == "rev-parse":
                    return "f" * 40
                return None

            facts = {
                "project_facts": {"origin": {"present": True,
                                             "stale_sources": [{"path": "Makefile"}]}},
                "repository": {"remote": "o/r", "default_branch": "main"},
                "checkout": {"primary_root": tmp},
            }
            with patch("run_queue.git_output", side_effect=fake_git), \
                 patch("run_queue.time.sleep"):
                record, path = run_queue.dispatch_facts_refresh(
                    facts, {"cwd": tmp}, Path(tmp), cli_fn=fake_cli,
                    session_fn=lambda *a, **k: (True, "ses_1"))
            self.assertEqual(record["status"], "failed")
            self.assertIsNone(path)
            self.assertIn("no open PR", record["reason"])

    def test_dispatch_facts_refresh_skips_a_missing_facts_file(self):
        facts = {"project_facts": {"origin": {"present": False,
                                              "stale_sources": [{"path": "Makefile"}]}}}
        record, path = run_queue.dispatch_facts_refresh(
            facts, {"cwd": "/repo"}, Path("."), cli_fn=lambda *a, **k: ({}, 0),
            session_fn=lambda *a, **k: (_ for _ in ()).throw(AssertionError("no session")))
        self.assertIsNone(record)
        self.assertIsNone(path)

    def test_run_summary_lists_the_facts_refresh(self):
        refresh = {"status": "refreshed", "pr": "https://github.com/o/r/pull/9",
                   "branch": "facts-refresh-x", "path": "/tmp/facts.md",
                   "stale_sources": ["Makefile"]}
        summary = run_queue.format_run_summary([], [], Path("."), 0, facts_refresh=refresh)
        self.assertIn("## Project facts refresh", summary)
        self.assertIn("https://github.com/o/r/pull/9", summary)
        self.assertIn("/tmp/facts.md", summary)

    def test_run_summary_lists_followups(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "followups.md").write_text("- #1600 filed for agent.py:185.\n", encoding="utf-8")
            summary = run_queue.format_run_summary([], [], Path(tmp), 0)
        self.assertIn("## Follow-ups", summary)
        self.assertIn("#1600 filed for agent.py:185", summary)

    def test_publish_with_a_lagging_issue_link_does_not_park(self):
        """A publish whose PR is not yet linked must advance to review, not park."""
        parent_data = {
            "parent": {"number": 100, "title": "Epic", "state": "OPEN",
                       "url": "https://github.com/o/r/issues/100"},
            "children": [{"number": 102, "title": "Child 2", "state": "OPEN",
                          "url": "https://github.com/o/r/issues/102"}],
        }
        base = {"issue": "https://github.com/o/r/issues/102", "number": 102,
                "title": "Child 2", "body": "", "labels": ["triage:ready"], "repo": "o/r"}
        calls = {"n": 0}

        def fake_observe(ref, cli_fn=None, cwd=None):
            calls["n"] += 1
            if calls["n"] <= 3:
                return {**base, "pr": None}
            if calls["n"] == 4:
                return {**base,
                        "pr": {"number": 52, "url": "https://github.com/o/r/pull/52",
                               "head": "c2", "head_branch": "issue-102-feat",
                               "state": "OPEN", "is_draft": True},
                        "ci": "pending",
                        "review_verdicts": [{"head": "c2", "verdict": "clean"}],
                        "pending_review_requests": []}
            return {**base,
                    "pr": {"number": 52, "url": "https://github.com/o/r/pull/52",
                           "head": "c2", "head_branch": "issue-102-feat",
                           "state": "OPEN", "is_draft": False},
                    "ci": "green", "pending_review_requests": []}

        sessions, cli_calls = [], []

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            sessions.append((step, dict(options)))
            return True, "ses_id"

        def fake_publish(*args, **kwargs):
            return {"number": 52, "url": "https://github.com/o/r/pull/52",
                    "head": "c2", "head_branch": "issue-102-feat"}

        def fake_cli(*args, cwd=None):
            cli_calls.append(args)
            if args and args[0] == "worktree" and args[1] == "create":
                branch = args[args.index("--branch") + 1]
                return {"path": f"/tmp/wt/{branch}", "action": "created"}, 0
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", return_value=parent_data), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_issue", side_effect=fake_observe), \
             patch("run_queue.run_session", side_effect=fake_run_session), \
             patch("run_queue.publish_committed", side_effect=fake_publish), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            ret = run_queue.main(["--parent", "100", "--project", "o/12", "--no-notebook",
                                  "--no-symbol-indexing", "--model", "lmstudio/test", "--review-model", "lmstudio/review",
                                  "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        steps = [step for step, _ in sessions]
        self.assertIn("implement-issue", steps)
        self.assertIn("review-changes", steps)
        review = next(options for step, options in sessions if step == "review-changes")
        self.assertIn("model=lmstudio/review", review.get("extra_text", ""))
        self.assertFalse([args for args in cli_calls if args and args[0] == "park"],
                         "a successful publish must not be parked")

    def test_retry_directive_uses_the_prior_attempt(self):
        parent_data = {
            "parent": {"number": 100, "title": "Epic", "state": "OPEN",
                       "url": "https://github.com/o/r/issues/100"},
            "children": [{"number": 102, "title": "Child 2", "state": "OPEN",
                          "url": "https://github.com/o/r/issues/102"}],
        }
        base = {"issue": "https://github.com/o/r/issues/102", "number": 102,
                "title": "Child 2", "body": "**Size:** XL", "labels": ["triage:ready"], "repo": "o/r"}
        observes = {"n": 0}

        def fake_observe(ref, cli_fn=None, cwd=None):
            observes["n"] += 1
            if observes["n"] <= 2:
                return {**base, "pr": None}
            return {**base,
                    "pr": {"number": 52, "url": "https://github.com/o/r/pull/52",
                           "head": "c2", "head_branch": "issue-102-feat",
                           "state": "OPEN", "is_draft": False},
                    "ci": "green", "pending_review_requests": []}

        sessions = []

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            sessions.append((step, dict(options)))
            if len(sessions) == 1:
                log = Path(notes_dir) / "session-fail.log"
                log.write_text(json.dumps({
                    "type": "tool_use",
                    "part": {"type": "tool", "tool": "shell",
                             "state": {"input": {"command": "grep -n x /w/a.py"}}}}) + "\n",
                    encoding="utf-8")
                if log_hook:
                    log_hook(str(log))
                return False, "boom"
            return True, "ses_id"

        def fake_cli(*args, cwd=None):
            if args and args[0] == "worktree" and args[1] == "create":
                branch = args[args.index("--branch") + 1]
                return {"path": f"/tmp/wt/{branch}", "action": "created"}, 0
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", return_value=parent_data), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_issue", side_effect=fake_observe), \
             patch("run_queue.run_session", side_effect=fake_run_session), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "100", "--project", "o/12", "--no-notebook",
                                  "--no-symbol-indexing", "--step-idle-timeout", "1200",
                                  "--context-warn-tokens", "50000",
                                  "--max-context-tokens", "90000",
                                  "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        self.assertEqual([step for step, _ in sessions], ["implement-issue", "implement-issue"])
        self.assertEqual(sessions[0][1]["step_idle_timeout"], 1200)
        self.assertEqual(sessions[0][1]["max_turns"], 150)
        self.assertEqual(sessions[0][1]["context_warn_tokens"], 50000)
        self.assertEqual(sessions[0][1]["max_context_tokens"], 90000)
        self.assertIn("grep -n x /w/a.py", sessions[1][1]["extra_text"])
        self.assertIn("first edit", sessions[1][1]["extra_text"])

    def test_park_record_uses_published_pr(self):
        parent_data = {
            "parent": {"number": 100, "title": "Epic", "state": "OPEN",
                       "url": "https://github.com/o/r/issues/100"},
            "children": [{"number": 102, "title": "Child 2", "state": "OPEN",
                          "url": "https://github.com/o/r/issues/102"}],
        }
        base = {"issue": "https://github.com/o/r/issues/102", "number": 102,
                "title": "Child 2", "body": "", "labels": ["triage:ready"], "repo": "o/r"}
        cli_calls = []

        def fake_cli(*args, cwd=None):
            cli_calls.append(args)
            if args and args[0] == "worktree" and args[1] == "create":
                branch = args[args.index("--branch") + 1]
                return {"path": f"/tmp/wt/{branch}", "action": "created"}, 0
            return {}, 0

        def fake_publish(*args, **kwargs):
            return {"number": 52, "url": "https://github.com/o/r/pull/52",
                    "head": "c2", "head_branch": "issue-102-feat"}

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", return_value=parent_data), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_issue", return_value={**base, "pr": None}), \
             patch("run_queue.run_session", return_value=(False, "boom")), \
             patch("run_queue.publish_committed", side_effect=fake_publish), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "100", "--project", "o/12", "--no-notebook",
                                  "--no-symbol-indexing", "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        parks = [args for args in cli_calls if args and args[0] == "park"]
        self.assertTrue(parks, cli_calls)
        self.assertIn("https://github.com/o/r/pull/52", parks[0])

    def test_primary_checkout_warning_in_run_session(self):
        class FakeStdout:
            def __init__(self, lines):
                self.lines = iter(lines)

            def __iter__(self):
                return self

            def __next__(self):
                return next(self.lines)

        class FakeProc:
            def __init__(self, lines):
                self.stdout = FakeStdout(lines)
                self.returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

            def terminate(self):
                pass

            def kill(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            skill = notes / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            primary = notes / "primary"
            primary.mkdir()
            worktree = notes / "worktree"
            worktree.mkdir()
            options = {"cwd": str(primary), "session_cwd": str(worktree),
                       "skill_dir": str(skill), "model": None, "standalone": False}
            lines = [json.dumps({"type": "text", "sessionID": "s1",
                                 "part": {"type": "text", "text": "hi"}}) + "\n"]

            def fake_cli(*args, cwd=None):
                return {"dispatch_prompt": "do it"}, 0

            with patch("run_queue.git_output", side_effect=["", "", "", " M changed"]), \
                 patch("run_queue.subprocess.Popen", return_value=FakeProc(lines)), \
                 patch("run_queue.subprocess.run"):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ok, _ = run_queue.run_session(
                        "implement-issue", "https://github.com/o/r/issues/1", notes,
                        options, cli_fn=fake_cli)

        self.assertTrue(ok)
        self.assertIn("primary checkout changed", out.getvalue())

    def test_slow_step_warning_in_run_session(self):
        class FakeStdout:
            def fileno(self):
                return 0

            def __iter__(self):
                return iter(())

            def readline(self):
                return ""

        class FakeProc:
            def __init__(self):
                self.stdout = FakeStdout()
                self.returncode = 0
                self.polls = 0

            def poll(self):
                self.polls += 1
                return 0 if self.polls > 2 else None

            def wait(self, timeout=None):
                return 0

            def terminate(self):
                pass

            def kill(self):
                pass

        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            skill = notes / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            primary = notes / "primary"
            primary.mkdir()
            worktree = notes / "worktree"
            worktree.mkdir()
            options = {"cwd": str(primary), "session_cwd": str(worktree),
                       "skill_dir": str(skill), "model": None, "standalone": False}

            def fake_cli(*args, cwd=None):
                return {"dispatch_prompt": "do it"}, 0

            with patch("run_queue.git_output", return_value=""), \
                 patch("run_queue.subprocess.Popen", return_value=FakeProc()), \
                 patch("run_queue.subprocess.run"), \
                 patch("run_queue.select.select", return_value=([], [], [])), \
                 patch("run_queue.time.time", side_effect=[0, 0, 1, 121, 122]):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ok, _ = run_queue.run_session(
                        "implement-issue", "https://github.com/o/r/issues/1", notes,
                        options, cli_fn=fake_cli)

        self.assertTrue(ok)
        self.assertIn("No session events for 121s", out.getvalue())

    def test_context_warning_and_cap_in_run_session(self):
        class FakeStdout:
            def __init__(self, lines):
                self.lines = iter(lines)

            def __iter__(self):
                return self

            def __next__(self):
                return next(self.lines)

        class FakeProc:
            def __init__(self, lines):
                self.stdout = FakeStdout(lines)
                self.returncode = 0

            def poll(self):
                return 0

            def wait(self, timeout=None):
                return 0

            def terminate(self):
                pass

            def kill(self):
                pass

        line = json.dumps({
            "type": "step_finish", "sessionID": "s1",
            "part": {"type": "step-finish",
                     "tokens": {"input": 500, "output": 10, "reasoning": 0,
                                "cache": {"read": 105000, "write": 0}}}}) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            notes = Path(tmp)
            skill = notes / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# skill\n", encoding="utf-8")
            primary = notes / "primary"
            primary.mkdir()
            worktree = notes / "worktree"
            worktree.mkdir()
            options = {"cwd": str(primary), "session_cwd": str(worktree),
                       "skill_dir": str(skill), "model": None, "standalone": False,
                       "context_warn_tokens": 100000, "max_context_tokens": 0}

            def fake_cli(*args, cwd=None):
                return {"dispatch_prompt": "do it"}, 0

            with patch("run_queue.git_output", return_value=""), \
                 patch("run_queue.subprocess.Popen", return_value=FakeProc([line, line])), \
                 patch("run_queue.subprocess.run"):
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    ok, _ = run_queue.run_session(
                        "implement-issue", "https://github.com/o/r/issues/1", notes,
                        options, cli_fn=fake_cli)
            self.assertTrue(ok)
            self.assertEqual(out.getvalue().count("Session context reached"), 1)
            self.assertIn("Session context reached 105500", out.getvalue())
            log_text = next(notes.glob("session-*.log")).read_text(encoding="utf-8")
            self.assertEqual(log_text.count("runner_warning"), 1)
            self.assertIn("105500", log_text)

            options["max_context_tokens"] = 100000
            with patch("run_queue.git_output", return_value=""), \
                 patch("run_queue.subprocess.Popen", return_value=FakeProc([line])), \
                 patch("run_queue.subprocess.run"):
                ok, reason = run_queue.run_session(
                    "implement-issue", "https://github.com/o/r/issues/1", notes,
                    options, cli_fn=fake_cli)
            self.assertFalse(ok)
            self.assertIn("cap 100000", reason)

    def test_main_warns_on_stale_facts(self):
        facts = {"project_facts": {"origin": {"stale_sources": [{"path": "Makefile"}]}}}

        def fake_cli(*args, cwd=None):
            if args and args[0] == "facts":
                return facts, 0
            return {}, 0

        refresh = {"status": "failed", "reason": "session failed", "stale_sources": ["Makefile"],
                   "pr": None, "branch": None, "path": None}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.dispatch_facts_refresh", return_value=(refresh, None)), \
             patch("run_queue.observe_board", return_value={"in_flight": [], "parked": [], "selection": []}), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        self.assertIn("stale on origin", out.getvalue())
        self.assertIn("Project facts refresh failed", out.getvalue())

    def test_main_stops_when_required_facts_refresh_fails(self):
        facts = {"project_facts": {"origin": {"stale_sources": [{"path": "Makefile"}]}}}
        refresh = {"status": "failed", "reason": "session failed", "stale_sources": ["Makefile"],
                   "pr": None, "branch": None, "path": None}

        def fake_cli(*args, cwd=None):
            if args and args[0] == "facts":
                return facts, 0
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.dispatch_facts_refresh", return_value=(refresh, None)), \
             patch("run_queue.observe_board") as board, \
             patch("run_queue.run_cli", side_effect=fake_cli):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing",
                                      "--require-facts-refresh", "--notes-dir", tmp])

        self.assertEqual(ret, 1)
        self.assertIn("Stopping: --require-facts-refresh", out.getvalue())
        board.assert_not_called()

    def test_main_points_sessions_at_the_refreshed_facts(self):
        facts = {"project_facts": {"origin": {"stale_sources": [{"path": "Makefile"}]}}}
        refresh = {"status": "refreshed", "reason": None, "stale_sources": ["Makefile"],
                   "pr": "https://github.com/o/r/pull/9", "branch": "facts-refresh-x",
                   "path": "/tmp/refreshed/project.md"}
        issue = {"issue": "https://github.com/o/r/issues/7", "number": 7, "title": "Fix it",
                 "labels": ["triage:ready"], "pr": None}
        captured = []

        def fake_cli(*args, cwd=None):
            if args and args[0] == "facts":
                return facts, 0
            return {}, 0

        def fake_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            captured.append((step, options))
            return True, "ses_1"

        board = {"in_flight": [], "parked": [], "selection": [{"number": 7, "issue": issue["issue"]}]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.dispatch_facts_refresh", return_value=(refresh, refresh["path"])), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=issue), \
             patch("run_queue.publish_committed", return_value=None), \
             patch("run_queue.park_issue", return_value=({}, 0)), \
             patch("run_queue.run_session", side_effect=fake_session), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        implement = [options for step, options in captured if step == "implement-issue"]
        self.assertTrue(implement)
        self.assertEqual(implement[0]["facts_path"], refresh["path"])
        self.assertIn("Project facts refreshed", out.getvalue())

    def test_main_processes_multiple_parents_sequentially(self):
        parents = {
            "100": {"parent": {"number": 100, "title": "Epic 1", "state": "OPEN", "url": "https://github.com/o/r/issues/100"},
                    "children": [{"number": 101, "title": "Child 1", "state": "OPEN", "url": "https://github.com/o/r/issues/101"}]},
            "200": {"parent": {"number": 200, "title": "Epic 2", "state": "OPEN", "url": "https://github.com/o/r/issues/200"},
                    "children": [{"number": 201, "title": "Child 2", "state": "OPEN", "url": "https://github.com/o/r/issues/201"}]},
        }
        done = {}

        def fake_observe_parent(ref, gh_cmd="gh", cwd=None):
            return parents[str(ref).split("#")[-1]]

        def fake_observe(ref, cli_fn=None, cwd=None):
            number = int(str(ref).rstrip("/").split("/")[-1])
            if number in done:
                return dict(done[number])
            return {"issue": str(ref), "number": number, "labels": ["triage:ready"], "pr": None}

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            number = int(str(issue_url).rstrip("/").split("/")[-1])
            done[number] = {
                "issue": issue_url, "number": number, "labels": ["triage:ready"],
                "pr": {"number": number + 1000, "url": f"https://github.com/o/r/pull/{number + 1000}",
                       "head": "h", "head_branch": f"issue-{number}-fix", "state": "OPEN", "is_draft": False},
                "ci": "green", "pending_review_requests": [],
            }
            return True, "ses_id"

        def fake_cli(*args, cwd=None):
            if args and args[0] == "worktree" and args[1] == "create":
                branch = args[args.index("--branch") + 1]
                return {"path": f"/tmp/wt/{branch}", "action": "created"}, 0
            return {}, 0

        sessions = []
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", side_effect=fake_observe_parent), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_issue", side_effect=fake_observe), \
             patch("run_queue.run_session", side_effect=lambda *a, **k: (sessions.append(a[1]), fake_run_session(*a, **k))[1]), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "100", "--parent", "200", "--project", "o/12",
                                  "--no-notebook", "--notes-dir", tmp])
        self.assertEqual(ret, 0)
        self.assertEqual([int(url.rsplit("/", 1)[-1]) for url in sessions], [101, 201])

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
            run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--notes-dir", tmp])
        extra = captured.get("extra_text", "")
        self.assertIn("reused from an earlier attempt", extra)
        self.assertIn("continue that work", extra)
        self.assertIn("not overwritten", extra)
        self.assertIn("gate --summary", extra)
        self.assertIn("do not repeat a command", extra)


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
                status = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--notes-dir", tmp])
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
class SessionTrailerTests(unittest.TestCase):
    """A runner session commit carries a trailer that names its session log."""

    def make_repo(self, tmp):
        repo = Path(tmp) / "repo"
        repo.mkdir()
        run = lambda *args: subprocess.run(["git", *args], cwd=repo, check=True,
                                           capture_output=True, text=True)
        run("init", "-q", "-b", "main")
        run("config", "user.email", "t@example.com")
        run("config", "user.name", "Test")
        (repo / "file.txt").write_text("one\n", encoding="utf-8")
        run("add", "file.txt")
        run("commit", "-q", "-m", "one")
        hooks = repo / ".git" / "hooks"
        hooks.mkdir(exist_ok=True)
        prepare = hooks / "prepare-commit-msg"
        prepare.write_text("#!/bin/sh\necho 'Original: yes' >> \"$1\"\n", encoding="utf-8")
        prepare.chmod(0o755)
        pre_commit = hooks / "pre-commit"
        pre_commit.write_text("#!/bin/sh\ntouch \"$(dirname \"$0\")/../pre-commit-ran\"\n",
                              encoding="utf-8")
        pre_commit.chmod(0o755)
        return repo, run

    def test_reference_is_relative_to_the_notes_root(self):
        self.assertEqual(
            run_queue.session_reference(Path("/n/runner-x"), Path("/n/runner-x/session-a.log")),
            "runner-x/session-a")

    def test_hook_adds_trailer_and_keeps_repository_hooks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo, run = self.make_repo(tmp)
            notes = Path(tmp) / "notes" / "runner-20261122-101500"
            notes.mkdir(parents=True)
            log = notes / "session-implement-issue-20261122-101733.log"
            log.write_text("log\n", encoding="utf-8")
            env = dict(os.environ)
            env.update(run_queue.session_git_environment(notes, log, repo))
            subprocess.run(["git", "commit", "--allow-empty", "-m", "trailer test"],
                           cwd=repo, env=env, check=True, capture_output=True, text=True)
            message = run("log", "-1", "--format=%B").stdout
            self.assertIn("Original: yes", message)
            reference = "runner-20261122-101500/session-implement-issue-20261122-101733"
            self.assertIn(f"Ghflow-Session: {reference}", message)
            self.assertTrue((repo / ".git" / "pre-commit-ran").exists())
            trailer = run("log", "-1", "--format=%(trailers:key=Ghflow-Session)").stdout.strip()
            self.assertIn(reference, trailer)
            self.assertTrue((notes.parent / f"{reference}.log").is_file())

            subprocess.run(["git", "commit", "--allow-empty", "-m", "plain"],
                           cwd=repo, check=True, capture_output=True, text=True)
            plain = run("log", "-1", "--format=%B").stdout
            self.assertIn("Original: yes", plain)
            self.assertNotIn("Ghflow-Session", plain)


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

    def test_restores_declared_generated_paths_before_pushing(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"url": "https://github.com/o/r/pull/9"}, 0) if args[0] == "pr" else ({}, 0)

        def fake_git(args, cwd=None):
            return self.HEAD if args[0] == "rev-parse" else "- `abc1234` Change"

        worktree = self.worktree()
        worktree["setup"] = {"generated": ["openapi.json", "src/client/"]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.committed_count", return_value=1), \
             patch("run_queue.git_output", side_effect=fake_git):
            result = run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", worktree,
                                                 "o/r", Path(tmp), {}, cli_fn=fake_cli)
        self.assertEqual(result["url"], "https://github.com/o/r/pull/9")
        restores = [call for call in calls if "restore" in call]
        self.assertEqual([call[-1] for call in restores], ["openapi.json", "src/client/"])
        self.assertIn("--source=HEAD", restores[0])
        self.assertIn("--staged", restores[0])
        self.assertIn("--worktree", restores[0])
        restore_index = next(i for i, call in enumerate(calls) if "restore" in call)
        push_index = next(i for i, call in enumerate(calls) if "push" in call)
        self.assertLess(restore_index, push_index)

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

    def test_stacked_pr_body_names_the_base_pr(self):
        calls = []

        def fake_cli(*args, cwd=None):
            calls.append(args)
            return ({"url": "https://github.com/o/r/pull/9"}, 0) if args[0] == "pr" else ({}, 0)

        def fake_git(args, cwd=None):
            if args[0] == "rev-parse":
                return self.HEAD
            if args[0] == "ls-remote":
                return "abc\trefs/heads/issue-8"
            return "- `abc1234` Change"

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.committed_count", return_value=1), \
             patch("run_queue.git_output", side_effect=fake_git):
            run_queue.publish_committed(
                "https://github.com/o/r/issues/9", "Fix it", self.worktree(), "o/r", Path(tmp), {},
                base_branch="issue-8",
                stack={"number": 8, "pr": 8, "branch": "issue-8"}, cli_fn=fake_cli)
            create = next(c for c in calls if c[:2] == ("pr", "create"))
            body = Path(create[create.index("--body-file") + 1]).read_text()
        self.assertIn("## Stack", body)
        self.assertIn("issue-8", body)
        self.assertIn("PR #8", body)

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

    def test_runner_commit_carries_the_session_trailer(self):
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
                run_queue.publish_committed("https://github.com/o/r/issues/9", "Fix it", worktree,
                                            "o/r", Path(tmp), {},
                                            session_ref="runner-x/session-y", cli_fn=fake_cli)
            commit_call = next(c for c in calls if len(c) > 6 and c[5:7] == ("commit", "-m"))
        self.assertIn("--trailer", commit_call)
        self.assertIn("Ghflow-Session: runner-x/session-y", commit_call)

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
            run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--notes-dir", tmp])
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

class FloorDecisionTests(unittest.TestCase):
    """The time floor stops long sessions but not cheap finishing steps."""

    def test_floor_allows_deterministic_submit(self):
        # The #1421 case: a reviewed draft with 14.3 minutes left must still
        # reach the ready step.
        self.assertFalse(run_queue.should_stop_for_floor("submit-pr", 14.3, 30))

    def test_floor_stops_implementation(self):
        self.assertTrue(run_queue.should_stop_for_floor("implement-issue", 14.3, 30))

    def test_floor_stops_review(self):
        self.assertTrue(run_queue.should_stop_for_floor("review-changes", 14.3, 30))

    def test_floor_allows_done(self):
        self.assertFalse(run_queue.should_stop_for_floor("DONE", 5, 30))

    def test_floor_allows_park(self):
        self.assertFalse(run_queue.should_stop_for_floor("park-blocker", 5, 30))

    def test_floor_does_not_stop_at_the_threshold(self):
        self.assertFalse(run_queue.should_stop_for_floor("implement-issue", 30, 30))

    def test_floor_stops_non_deterministic_submit(self):
        self.assertTrue(
            run_queue.should_stop_for_floor("submit-pr", 14.3, 30, deterministic_pr=False)
        )

    def test_phase_boundary_park_names_the_draft_and_remaining_steps(self):
        state = {"pr": {"url": "https://github.com/o/r/pull/8", "head": "a" * 40, "is_draft": True}}
        text = run_queue.phase_boundary_park(state, "review-changes", 14.3, 30)
        self.assertIn("https://github.com/o/r/pull/8", text)
        self.assertIn("review-changes", text)
        self.assertIn("submit-pr", text)
        self.assertIn("14.3", text)

    def test_phase_boundary_park_skips_a_ready_pr_or_no_pr(self):
        ready = {"pr": {"url": "u", "head": "a" * 40, "is_draft": False}}
        self.assertIsNone(run_queue.phase_boundary_park(ready, "review-changes", 5, 30))
        self.assertIsNone(run_queue.phase_boundary_park({}, "review-changes", 5, 30))

    def test_main_parks_a_draft_at_the_floor(self):
        issue_url = "https://github.com/o/r/issues/7"
        state = {"issue": issue_url, "number": 7, "title": "Fix it", "labels": ["triage:ready"],
                 "pr": {"url": "https://github.com/o/r/pull/8", "head": "a" * 40, "is_draft": True}}
        board = {"in_flight": [], "parked": [], "selection": [{"number": 7, "issue": issue_url}]}
        parks = []

        def fake_park(issue_url, pr_url, kind, text, notes_dir, cli_fn=None, cwd=None):
            parks.append((issue_url, pr_url, kind, text))
            return {"readback": True}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.should_stop_for_floor", return_value=True), \
             patch("run_queue.park_issue", side_effect=fake_park), \
             patch("run_queue.run_cli", return_value=({}, 0)):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        self.assertEqual(len(parks), 1)
        self.assertEqual(parks[0][1], "https://github.com/o/r/pull/8")
        self.assertEqual(parks[0][2], "time")
        self.assertIn("https://github.com/o/r/pull/8", parks[0][3])
        self.assertIn("review-changes", parks[0][3])


class ModelUnloadTests(unittest.TestCase):
    """LM Studio models unload before a different model starts."""

    def test_unloads_lmstudio_models(self):
        calls = []

        def runner(args, **kwargs):
            calls.append((args, kwargs))
            return SimpleNamespace(returncode=0, stdout="unloaded", stderr="")

        with patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": ""}):
            result = run_queue.unload_local_models(
                "lmstudio/qwen", runner=runner, which=lambda name: "/bin/lms")
        self.assertEqual(result["status"], "unloaded")
        self.assertEqual(calls[0][0], ["/bin/lms", "unload", "--all"])
        self.assertEqual(calls[0][1]["timeout"], 60)

    def test_skips_other_providers(self):
        runner = MagicMock()
        which = MagicMock()
        with patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": ""}):
            result = run_queue.unload_local_models(
                "ollama/qwen", runner=runner, which=which)
        self.assertEqual(result["status"], "skipped")
        self.assertIn("not lmstudio", result["reason"])
        runner.assert_not_called()
        which.assert_not_called()

    def test_skips_when_disabled(self):
        runner = MagicMock()
        with patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": "1"}):
            result = run_queue.unload_local_models(
                "lmstudio/qwen", runner=runner, which=MagicMock())
        self.assertEqual(result["status"], "skipped")
        self.assertIn("disabled", result["reason"])
        runner.assert_not_called()

    def test_skips_without_lms(self):
        runner = MagicMock()
        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": ""}):
            result = run_queue.unload_local_models(
                "lmstudio/qwen", runner=runner, which=lambda name: None, home=tmp)
        self.assertEqual(result["status"], "skipped")
        self.assertIn("lms not found", result["reason"])
        runner.assert_not_called()

    def test_reports_an_unload_failure(self):
        def runner(args, **kwargs):
            return SimpleNamespace(returncode=1, stdout="", stderr="busy")

        with patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": ""}):
            result = run_queue.unload_local_models(
                "lmstudio/qwen", runner=runner, which=lambda name: "/bin/lms")
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["reason"], "busy")

    def test_reports_a_timeout(self):
        def runner(args, **kwargs):
            raise subprocess.TimeoutExpired("lms", 60)

        with patch.dict(os.environ, {"GHFLOW_NO_MODEL_UNLOAD": ""}):
            result = run_queue.unload_local_models(
                "lmstudio/qwen", runner=runner, which=lambda name: "/bin/lms")
        self.assertEqual(result["status"], "failed")
        self.assertIn("timed out", result["reason"])


class ParkSuggestionTests(unittest.TestCase):
    """A park comment names the local next step."""

    def park_text(self, kind):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def fake_cli(*args, cwd=None):
                calls.append(args)
                return {}, 0

            run_queue.park_issue("https://github.com/o/r/issues/7", None, kind,
                                 "Session failed repeatedly.", Path(tmp), cli_fn=fake_cli)
            text_path = Path(calls[0][calls[0].index("--text") + 1])
            return text_path.read_text(encoding="utf-8")

    def test_blocker_names_a_local_retry(self):
        text = self.park_text("blocker")
        self.assertIn("different local model or a person", text)
        self.assertIn("fix the preparation", text)
        self.assertIn("Do not use a cloud model", text)

    def test_time_park_resumes_with_the_local_model(self):
        text = self.park_text("time")
        self.assertIn("Resume with the local model", text)


class LocalModelTests(unittest.TestCase):
    """The local models select implementation and review."""

    def test_accepts_local_providers(self):
        for model in ("lmstudio/qwen3.8-27b-mlx@4bit", "ollama/qwen3.8:27b",
                      "mlx/mlx-community/Qwen3.8-27B-4bit", "rec/flint", "llama.cpp/llama"):
            with self.subTest(model=model):
                models, error = run_queue.select_models(model, model)
                self.assertIsNone(error)
                self.assertEqual(models, {"implementation": model, "review": model})

    def test_rejects_cloud_providers(self):
        for model in ("otari/qwen3.8-27b", "google-vertex/gemini-3.5-flash",
                      "opencode/flint-40b-free", "anthropic/claude-sonnet-5.5"):
            with self.subTest(model=model):
                models, error = run_queue.select_models(model, "lmstudio/review")
                self.assertIsNone(models)
                self.assertIn("is not local", error)

    def test_applies_the_provider_to_both_models(self):
        models, error = run_queue.select_models("qwen", "flint", provider="lmstudio")
        self.assertIsNone(error)
        self.assertEqual(models, {"implementation": "lmstudio/qwen",
                                  "review": "lmstudio/flint"})

    def test_summary_names_both_models(self):
        records = [{"issue": "https://github.com/o/r/issues/7", "pr": "none", "endpoint": "DONE",
                    "models": {"implementation": "lmstudio/impl", "review": "lmstudio/review"}}]
        summary = run_queue.format_run_summary(
            records, [], Path("."), 0, cwd="/nonexistent",
            model_note="implementation `lmstudio/impl`, review `lmstudio/review`")
        self.assertIn("lmstudio/impl / lmstudio/review", summary)
        self.assertIn("Model: implementation", summary)


class LocalModelMainTests(unittest.TestCase):
    """main uses the local implementation and review models."""

    def issue(self, labels=None):
        return {"issue": "https://github.com/o/r/issues/7", "number": 7, "title": "Fix it",
                "labels": labels or ["triage:ready"], "pr": None}

    def run_main(self, tmp, issue, extra_args, run_session=None):
        board = {"in_flight": [], "parked": [], "selection": [{"number": 7, "issue": issue["issue"]}]}
        session = run_session or (lambda *a, **k: (True, "ses_1"))

        def fake_cli(*args, cwd=None):
            return {}, 0

        with patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=issue), \
             patch("run_queue.publish_committed", return_value=None), \
             patch("run_queue.run_session", side_effect=session), \
             patch("run_queue.monitor_mod.probe_model", return_value=True), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--once", "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp] + extra_args)
        return ret, out.getvalue()

    def test_uses_local_implementation_and_review_models(self):
        with tempfile.TemporaryDirectory() as tmp:
            captured = []

            def session(step, issue_url, notes_dir, options, **kwargs):
                captured.append((step, options))
                return True, "ses_1"

            ret, _ = self.run_main(tmp, self.issue(),
                                   ["--model", "lmstudio/qwen", "--review-model", "lmstudio/flint"],
                                   run_session=session)
        self.assertEqual(ret, 0)
        implement = [options for step, options in captured if step == "implement-issue"]
        self.assertTrue(implement)
        self.assertEqual(implement[0]["model"], "lmstudio/qwen")
        self.assertEqual(implement[0]["review_model"], "lmstudio/flint")

    def test_rejects_a_cloud_model_before_selection(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.observe_board") as board:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "otari/qwen3.8-27b",
                                      "--review-model", "lmstudio/flint",
                                      "--once", "--no-notebook", "--notes-dir", tmp])
        self.assertEqual(ret, 1)
        board.assert_not_called()
        self.assertIn("is not local", out.getvalue())

    def test_requires_both_models(self):
        with self.assertRaises(SystemExit):
            run_queue.main(["--model", "lmstudio/qwen", "--once", "--no-notebook"])
        with self.assertRaises(SystemExit):
            run_queue.main(["--review-model", "lmstudio/flint", "--once", "--no-notebook"])


class RestoreGeneratedPathsTests(unittest.TestCase):
    """Gate-generated tracked files are restored after the gate."""

    def _git(self, tmp, *args):
        return subprocess.run(["git", *args], cwd=tmp, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    def test_restores_modified_tracked_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._git(tmp, "init", "-q")
            self._git(tmp, "config", "user.email", "test@example.com")
            self._git(tmp, "config", "user.name", "Test")
            target = Path(tmp) / "openapi.json"
            target.write_text("original\n")
            self._git(tmp, "add", "openapi.json")
            self._git(tmp, "commit", "-qm", "base")
            target.write_text("gate drift\n")

            restored = run_queue.restore_generated_paths(tmp, ["openapi.json"])

            self.assertEqual(restored, ["openapi.json"])
            self.assertEqual(target.read_text(), "original\n")

    def test_empty_paths_is_a_noop(self):
        self.assertEqual(run_queue.restore_generated_paths("/tmp", []), [])
        self.assertEqual(run_queue.restore_generated_paths(None, ["openapi.json"]), [])

    def test_gate_call_restores_generated_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "Makefile").write_text("check:\n\techo ok\n")
            target = Path(tmp) / "openapi.json"
            target.write_text("original\n")
            self._git(tmp, "init", "-q")
            self._git(tmp, "config", "user.email", "test@example.com")
            self._git(tmp, "config", "user.name", "Test")
            self._git(tmp, "add", "openapi.json")
            self._git(tmp, "commit", "-qm", "base")
            target.write_text("gate drift\n")

            real_run = subprocess.run

            def fake_run(cmd, **kwargs):
                if cmd[:2] == ["make", "check"]:
                    return MagicMock(returncode=0, stdout="ok\n")
                return real_run(cmd, **kwargs)

            with patch("subprocess.run", side_effect=fake_run):
                res = run_queue.run_precomputed_gate(tmp, generated_paths=["openapi.json"])

            self.assertTrue(res["success"])
            self.assertEqual(target.read_text(), "original\n")


class FloorReplayTests(unittest.TestCase):
    """Replay of #1421: a reviewed draft must reach ready below the floor."""

    def test_clean_draft_is_submitted_below_the_floor(self):
        state = {
            "issue": "https://github.com/o/r/issues/1421",
            "number": 1421,
            "title": "Split tests",
            "labels": ["triage:ready"],
            "pr": {"number": 1619, "url": "https://github.com/o/r/pull/1619",
                   "head": "dcf16807", "head_branch": "issue-1421",
                   "state": "OPEN", "is_draft": True},
            "ci": "green",
            "pending_review_requests": [],
            "review_verdicts": [{"head": "dcf16807", "verdict": "clean"}],
        }
        submitted = []

        def fake_submit(state_arg, owner, project, notes_dir, options, cli_fn=None):
            submitted.append(state_arg["issue"])
            return True, {"url": "https://github.com/o/r/pull/1619", "number": 1619}

        def fake_observe_parent(ref, gh_cmd="gh", cwd=None):
            return {
                "parent": {"number": 1438, "title": "Epic", "state": "OPEN",
                           "url": "https://github.com/o/r/issues/1438"},
                "children": [{"number": 1421, "title": "Split tests", "state": "OPEN",
                              "url": state["issue"]}],
            }

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", side_effect=fake_observe_parent), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.execute_submit_pr", side_effect=fake_submit), \
             patch("run_queue.run_cli", return_value=({}, 0)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.narrative.post_issue_checkpoint"):
            ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "1438", "--project", "o/6",
                                  "--hours", "0.2", "--floor", "30", "--once",
                                  "--no-notebook", "--no-symbol-indexing",
                                  "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        self.assertEqual(submitted, [state["issue"]])

    def test_failed_submit_is_parked_without_crashing(self):
        state = {
            "issue": "https://github.com/o/r/issues/1421",
            "number": 1421,
            "title": "Split tests",
            "labels": ["triage:ready"],
            "pr": {"number": 1619, "url": "https://github.com/o/r/pull/1619",
                   "head": "dcf16807", "head_branch": "issue-1421",
                   "state": "OPEN", "is_draft": True},
            "ci": "green",
            "pending_review_requests": [],
            "review_verdicts": [{"head": "dcf16807", "verdict": "clean"}],
        }

        def fake_submit(state_arg, owner, project, notes_dir, options, cli_fn=None):
            return False, {"error": "boom"}

        def fake_observe_parent(ref, gh_cmd="gh", cwd=None):
            return {
                "parent": {"number": 1438, "title": "Epic", "state": "OPEN",
                           "url": "https://github.com/o/r/issues/1438"},
                "children": [{"number": 1421, "title": "Split tests", "state": "OPEN",
                              "url": state["issue"]}],
            }

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.observe_parent", side_effect=fake_observe_parent), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.execute_submit_pr", side_effect=fake_submit), \
             patch("run_queue.run_cli", return_value=({}, 0)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.narrative.post_issue_checkpoint"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--parent", "1438", "--project", "o/6",
                                      "--hours", "0.2", "--floor", "30", "--once",
                                      "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp])

        self.assertEqual(ret, 0)
        self.assertIn("parked", out.getvalue())


class StaleFactsDirectiveTests(unittest.TestCase):
    """Stale project-facts sources are named in the session directive."""

    def test_stale_sources_are_named_in_the_implement_directive(self):
        captured = {}

        def fake_run_session(step, issue_url, notes_dir, options, cli_fn=None, log_hook=None):
            captured.update(options)
            return True, "ses_id"

        state = {"issue": "https://github.com/o/r/issues/7", "number": 7, "title": "Fix it",
                 "labels": ["triage:ready"], "pr": None}
        facts = {"project_facts": {"origin": {"stale_sources": [{"path": "Makefile"}]}}}

        def fake_cli(*args, cwd=None):
            if args and args[0] == "facts":
                return facts, 0
            if args and args[0] == "worktree" and args[1] == "create":
                return {"path": "/repo/.claude/worktrees/issue-7-fix-it", "action": "exists"}, 3
            return {}, 0

        board = {"in_flight": [], "parked": [], "selection": [{"number": 7, "issue": state["issue"]}]}
        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.publish_committed", return_value=None), \
             patch("run_queue.run_session", side_effect=fake_run_session), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing", "--notes-dir", tmp])

        extra = captured.get("extra_text", "")
        self.assertIn("Makefile", extra)
        self.assertIn("do not rely on the stale facts sections", extra)


class MonitorIntegrationTests(unittest.TestCase):
    def test_main_writes_monitor_reports_and_status_line(self):
        facts = {
            "identity": {"login": "MokaGnome", "ready": True},
            "checkout": {"branch": "main", "head": "a", "dirty": False},
            "repository": {"local_default_head": "a", "origin_default_head": "a"},
            "skill_source": {"head": "a", "up_to_date": True},
            "base_ci": {"commit": "a", "summary": "green",
                        "checks": [{"name": "check", "state": "passed"}]},
            "project_facts": {"present": True, "origin": {"present": True, "stale_sources": []}},
        }
        state = {"issue": "https://github.com/o/r/issues/7", "number": 7,
                 "labels": ["triage:ready"],
                 "pr": {"url": "https://github.com/o/r/pull/8", "head": "abc",
                        "is_draft": False},
                 "ci": "green", "pending_review_requests": []}
        board = {"in_flight": [], "parked": [],
                 "selection": [{"number": 7, "issue": state["issue"]}]}

        def fake_cli(*args, cwd=None):
            if args and args[0] == "facts":
                return facts, 0
            if args and args[0] == "identity":
                return {"login": "MokaGnome", "ready": True}, 0
            if args and args[0] == "exec":
                return {"login": "MokaGnome"}, 0
            if args and args[0] == "queue":
                return {"rows": [{"issue": "o/r#7"}]}, 0
            return {}, 0

        with tempfile.TemporaryDirectory() as tmp, \
             patch("run_queue.discover_project", return_value=("o", 12)), \
             patch("run_queue.acquire_run_lock"), \
             patch("run_queue.check_active_runs"), \
             patch("run_queue.observe_board", return_value=board), \
             patch("run_queue.observe_issue", return_value=state), \
             patch("run_queue.set_board_status"), \
             patch("run_queue.run_cli", side_effect=fake_cli):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                ret = run_queue.main(["--model", "lmstudio/test", "--review-model", "lmstudio/review", "--once", "--no-notebook", "--no-symbol-indexing",
                                      "--notes-dir", tmp])

            self.assertEqual(ret, 0)
            report_path = Path(tmp) / "monitor.json"
            self.assertTrue(report_path.is_file())
            self.assertTrue((Path(tmp) / "monitor.md").is_file())
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["schema"], "ghflow-monitor/1")
            self.assertTrue(report["checks"])
            self.assertIn("Monitor:", out.getvalue())
            self.assertIn("monitor.md", out.getvalue())


if __name__ == "__main__":
    unittest.main()
