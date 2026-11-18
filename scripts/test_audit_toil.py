#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from audit_toil import audit_toil, format_markdown_report, mine_patterns, normalize_command, parse_session_log


class AuditToilTests(unittest.TestCase):
    def test_normalize_command(self):
        raw = "python3 cli/ghflow.py review prepare https://github.com/lmorchard/ghflow/pull/180 --repo lmorchard/ghflow"
        norm = normalize_command(raw)
        self.assertIn("<PR_URL>", norm)
        self.assertNotIn("180", norm)

        sha_raw = "git merge-base --is-ancestor abcdef1234567890abcdef1234567890abcdef12 origin/main"
        norm_sha = normalize_command(sha_raw)
        self.assertIn("<SHA>", norm_sha)

        tmp_raw = "make check > /tmp/check-out.log 2>&1"
        norm_tmp = normalize_command(tmp_raw)
        self.assertIn("<TMP_PATH>", norm_tmp)

        wt_raw = "cd /home/user/repo/.claude/worktrees/issue-15-fix && uv sync"
        norm_wt = normalize_command(wt_raw)
        self.assertIn("<WORKTREE_PATH>", norm_wt)

    def test_parse_session_log_opencode_json(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".log", prefix="session-review-changes-") as f:
            f.write(json.dumps({"type": "step_start", "sessionID": "ses_abc123"}) + "\n")
            f.write(json.dumps({"type": "tool", "part": {"type": "tool", "name": "bash", "state": {"input": {"command": "make check > /tmp/check.log 2>&1"}}}}) + "\n")
            f.write(json.dumps({"type": "tool", "part": {"type": "tool", "name": "bash", "state": {"input": {"command": "echo exit=$?"}}}}) + "\n")
            f.write(json.dumps({"type": "step_finish"}) + "\n")
            f.flush()

            parsed = parse_session_log(Path(f.name))
            self.assertEqual(parsed["session_id"], "ses_abc123")
            self.assertEqual(parsed["step"], "review")
            self.assertEqual(len(parsed["operations"]), 2)
            self.assertIn("<TMP_PATH>", parsed["operations"][0])

    def test_parse_session_log_text_runner(self):
        with tempfile.NamedTemporaryFile("w+", suffix=".log", prefix="session-implement-issue-") as f:
            f.write("[12:00:00] [turn 1] Tool: bash git status\n")
            f.write("[12:00:01] [turn 2] Tool: bash git diff\n")
            f.flush()

            parsed = parse_session_log(Path(f.name))
            self.assertEqual(parsed["step"], "implement")
            self.assertEqual(parsed["operations"], ["git status", "git diff"])

    def test_mine_patterns_enforces_strike_threshold_and_prunes(self):
        sessions = [
            {"session_id": "s1", "step": "review", "operations": ["cmdA", "cmdB", "cmdC"]},
            {"session_id": "s2", "step": "review", "operations": ["cmdA", "cmdB", "cmdC"]},
            {"session_id": "s3", "step": "review", "operations": ["cmdA", "cmdB", "cmdC"]},
            {"session_id": "s4", "step": "review", "operations": ["cmdA", "cmdB", "cmdX"]},
        ]
        patterns = mine_patterns(sessions, min_strikes=3, min_length=2)
        self.assertTrue(len(patterns) >= 1)
        # Maximal pattern cmdA -> cmdB -> cmdC appears in 3 sessions (s1, s2, s3)
        triples = [p for p in patterns if len(p["sequence"]) == 3]
        self.assertEqual(len(triples), 1)
        self.assertEqual(triples[0]["strike_count"], 3)
        self.assertEqual(triples[0]["sequence"], ["cmdA", "cmdB", "cmdC"])

    def test_audit_toil_end_to_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            for i in range(3):
                log = tmp_path / f"session-review-changes-20261118-{i}.log"
                lines = [
                    json.dumps({"type": "step_start", "sessionID": f"ses_{i}"}),
                    json.dumps({"type": "tool", "part": {"name": "bash", "state": {"input": {"command": "make check > /tmp/out.log 2>&1"}}}}),
                    json.dumps({"type": "tool", "part": {"name": "bash", "state": {"input": {"command": "tail -n 35 /tmp/out.log"}}}}),
                ]
                log.write_text("\n".join(lines) + "\n", encoding="utf-8")

            result, status = audit_toil(dirs=[str(tmp_path)], min_strikes=3, min_length=2)
            self.assertEqual(status, 0)
            self.assertEqual(result["scanned"], 3)
            self.assertEqual(len(result["patterns"]), 1)
            self.assertEqual(result["patterns"][0]["strike_count"], 3)

            report = format_markdown_report(result["patterns"], result["scanned"])
            self.assertIn("**Strike Count**: 3", report)
            self.assertIn("<TMP_PATH>", report)


if __name__ == "__main__":
    unittest.main()
