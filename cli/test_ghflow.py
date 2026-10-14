import io
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

import ghflow
from ghflow import GhError, board_set_field, read_runtime, read_skill_source, strip_jsonc, board_set_status, identity_env, IdentityError, main, parse_facts_sources, parse_remote, pr_ready, pr_state, project_facts, resolve_identity, run_gh, verify_commit

HEAD = "a" * 40
OLD = "b" * 40


def pr(**overrides):
    data = {
        "number": 7,
        "url": "https://github.com/o/r/pull/7",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "headRefOid": HEAD,
        "headRefName": "task",
        "baseRefName": "main",
        "reviewRequests": [],
        "statusCheckRollup": [
            {"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    }
    data.update(overrides)
    return data


def rules(*contexts):
    return [{"type": "required_status_checks", "parameters": {"required_status_checks": [{"context": c} for c in contexts]}}]


def fake(pr_data, rules_data=None, reviews=(), comments=(), timeline=(), fail=(), behind_by=0, issue_comments=()):
    def gh(args):
        if args[0] == "pr":
            if "pr" in fail:
                raise GhError("not found")
            return pr_data
        if "/compare/" in args[1]:
            if "compare" in fail:
                raise GhError("HTTP 404")
            return {"behind_by": behind_by, "ahead_by": 1}
        raise AssertionError(f"Unexpected gh call: {args}")

    def gh_paginated(path):
        if "/rules/branches/" in path:
            if "rules" in fail:
                raise GhError("HTTP 403")
            return rules_data if rules_data is not None else rules("test")
        if path.endswith("/reviews"):
            if "reviews" in fail:
                raise GhError("HTTP 502")
            return list(reviews)
        if "/issues/" in path and path.endswith("/comments"):
            if "comments" in fail:
                raise GhError("HTTP 500")
            return list(issue_comments)
        if path.endswith("/comments"):
            return list(comments)
        if "timeline" in fail:
            raise GhError("rate limited")
        return list(timeline)

    return {"gh": gh, "gh_paginated": gh_paginated}


def review(rid, author, commit, submitted, state="COMMENTED", body=""):
    return {"id": rid, "user": {"login": author}, "state": state, "commit_id": commit, "submitted_at": submitted, "body": body}


def requested(reviewer, at, event="review_requested"):
    return {"event": event, "requested_reviewer": {"login": reviewer}, "created_at": at, "actor": {"login": "les"}}


class CiTests(unittest.TestCase):
    def test_green_when_required_checks_pass(self):
        result, status = pr_state("o/r", 7, **fake(pr()))
        self.assertEqual(result["ci"], "green")
        self.assertEqual(status, 0)

    def test_required_check_without_result_is_missing(self):
        result, _ = pr_state("o/r", 7, **fake(pr(), rules_data=rules("test", "typecheck")))
        self.assertEqual(result["ci"], "missing")
        self.assertIn({"name": "typecheck", "state": "missing", "required": True}, result["checks"])

    def test_skipped_optional_check_stays_green(self):
        rollup = [
            {"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"},
            {"__typename": "CheckRun", "name": "preview", "status": "COMPLETED", "conclusion": "SKIPPED"},
        ]
        result, _ = pr_state("o/r", 7, **fake(pr(statusCheckRollup=rollup)))
        self.assertEqual(result["ci"], "green")

    def test_running_check_is_pending(self):
        rollup = [{"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": None}]
        result, _ = pr_state("o/r", 7, **fake(pr(statusCheckRollup=rollup)))
        self.assertEqual(result["ci"], "pending")

    def test_failure_outranks_pending(self):
        rollup = [
            {"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": None},
            {"__typename": "StatusContext", "context": "lint", "state": "FAILURE"},
        ]
        result, _ = pr_state("o/r", 7, **fake(pr(statusCheckRollup=rollup), rules_data=[]))
        self.assertEqual(result["ci"], "failing")

    def test_no_checks_is_none_not_green(self):
        result, _ = pr_state("o/r", 7, **fake(pr(statusCheckRollup=[]), rules_data=[]))
        self.assertEqual(result["ci"], "none")

    def test_head_current_with_base(self):
        result, _ = pr_state("o/r", 7, **fake(pr()))
        self.assertEqual(result["base_behind_by"], 0)

    def test_head_behind_base_is_reported(self):
        result, status = pr_state("o/r", 7, **fake(pr(), behind_by=2))
        self.assertEqual(result["base_behind_by"], 2)
        self.assertEqual(result["ci"], "green")
        self.assertEqual(status, 0)

    def test_unreadable_compare_leaves_behind_unknown(self):
        result, status = pr_state("o/r", 7, **fake(pr(), fail={"compare"}))
        self.assertIsNone(result["base_behind_by"])
        self.assertEqual(status, 2)

    def test_unreadable_rules_leave_required_unknown(self):
        result, status = pr_state("o/r", 7, **fake(pr(), fail={"rules"}))
        self.assertIsNone(result["required_checks"])
        self.assertIsNone(result["checks"][0]["required"])
        self.assertEqual(status, 2)

    def test_unreadable_rules_do_not_report_green_for_only_passing_or_empty_checks(self):
        cases = (
            (
                "passed",
                [{"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"}],
                "incomplete",
                [{"name": "test", "state": "passed", "required": None}],
            ),
            (
                "pending",
                [{"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": None}],
                "pending",
                [{"name": "test", "state": "pending", "required": None}],
            ),
            (
                "failed",
                [{"__typename": "StatusContext", "context": "test", "state": "FAILURE"}],
                "failing",
                [{"name": "test", "state": "failed", "required": None}],
            ),
            ("empty", [], "incomplete", []),
        )
        for name, rollup, summary, checks in cases:
            with self.subTest(name=name):
                result, status = pr_state(
                    "o/r", 7, **fake(pr(statusCheckRollup=rollup), fail={"rules"})
                )
                self.assertEqual(status, 2)
                self.assertEqual(result["ci"], summary)
                self.assertIsNone(result["required_checks"])
                self.assertEqual(result["checks"], checks)
                self.assertEqual(result["errors"][0]["part"], "required_checks")
                self.assertIn("HTTP 403", result["errors"][0]["error"])


class ReviewTests(unittest.TestCase):
    def test_copilot_request_matches_bot_review_after_it(self):
        data = fake(
            pr(),
            reviews=[review(1, "copilot-pull-request-reviewer[bot]", HEAD, "2026-10-02T03:45:00Z")],
            timeline=[requested("Copilot", "2026-10-02T03:41:00Z")],
        )
        result, _ = pr_state("o/r", 7, **data)
        self.assertEqual(result["latest_review_requests"], [{"reviewer": "Copilot", "requested_at": "2026-10-02T03:41:00Z", "answered": True}])
        self.assertTrue(result["reviews"][0]["covers_head"])

    def test_review_before_latest_request_does_not_answer_it(self):
        data = fake(
            pr(reviewRequests=[{"login": "Copilot"}]),
            reviews=[review(1, "copilot-pull-request-reviewer[bot]", OLD, "2026-10-02T03:00:00Z")],
            timeline=[requested("Copilot", "2026-10-02T02:50:00Z"), requested("Copilot", "2026-10-02T03:30:00Z")],
        )
        result, _ = pr_state("o/r", 7, **data)
        self.assertFalse(result["latest_review_requests"][0]["answered"])
        self.assertFalse(result["reviews"][0]["covers_head"])
        self.assertEqual(result["pending_review_requests"], ["Copilot"])

    def test_removed_request_is_not_latest(self):
        data = fake(pr(), timeline=[requested("alice", "2026-10-02T01:00:00Z"), requested("alice", "2026-10-02T01:05:00Z", "review_request_removed")])
        result, _ = pr_state("o/r", 7, **data)
        self.assertEqual(result["latest_review_requests"], [])

    def test_inline_comments_count_per_review(self):
        data = fake(
            pr(),
            reviews=[review(1, "bot", HEAD, "t1"), review(2, "les", HEAD, "t2")],
            comments=[{"pull_request_review_id": 1}, {"pull_request_review_id": 1}],
        )
        result, _ = pr_state("o/r", 7, **data)
        self.assertEqual([r["inline_comments"] for r in result["reviews"]], [2, 0])

    def test_failed_review_read_is_null_not_empty(self):
        result, status = pr_state("o/r", 7, **fake(pr(), timeline=[requested("Copilot", "t")], fail={"reviews"}))
        self.assertIsNone(result["reviews"])
        self.assertIsNone(result["latest_review_requests"][0]["answered"])
        self.assertEqual(result["errors"][0]["part"], "reviews")
        self.assertEqual(status, 2)

    def test_top_level_comments_are_listed_with_author_time_and_body(self):
        data = fake(pr(), issue_comments=[
            {"id": 11, "user": {"login": "les"}, "created_at": "2026-10-11T20:00:00Z",
             "html_url": "https://github.com/o/r/pull/7#issuecomment-11", "body": "Please also cover CRLF."},
            {"id": 12, "user": None, "created_at": None, "html_url": None, "body": None},
        ])
        result, status = pr_state("o/r", 7, **data)
        self.assertEqual(status, 0)
        self.assertEqual(result["comments"], [
            {"id": 11, "author": "les", "created_at": "2026-10-11T20:00:00Z",
             "url": "https://github.com/o/r/pull/7#issuecomment-11", "body": "Please also cover CRLF."},
            {"id": 12, "author": None, "created_at": None, "url": None, "body": ""},
        ])

    def test_no_top_level_comments_is_empty_list_not_null(self):
        result, status = pr_state("o/r", 7, **fake(pr()))
        self.assertEqual(status, 0)
        self.assertEqual(result["comments"], [])

    def test_failed_comments_read_is_null_not_empty(self):
        result, status = pr_state("o/r", 7, **fake(pr(), fail={"comments"}))
        self.assertIsNone(result["comments"])
        self.assertIsNotNone(result["reviews"])
        self.assertEqual(result["errors"][0]["part"], "comments")
        self.assertEqual(status, 2)

    def test_failed_timeline_read_is_null(self):
        result, status = pr_state("o/r", 7, **fake(pr(), fail={"timeline"}))
        self.assertIsNone(result["review_request_events"])
        self.assertIsNone(result["latest_review_requests"])
        self.assertEqual(status, 2)


class PrTests(unittest.TestCase):
    def test_unreadable_pr_exits_1(self):
        result, status = pr_state("o/r", 7, **fake(pr(), fail={"pr"}))
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")


def commit_fake(message="Fix the thing\n\nDetails.", compare="behind", head=HEAD, fail=()):
    def gh(args):
        path = args[1] if args[0] == "api" else None
        if args[0] == "pr":
            if "pr" in fail:
                raise GhError("not found")
            return {"headRefOid": head}
        if "/compare/" in path:
            if "compare" in fail:
                raise GhError("HTTP 404")
            return {"status": compare}
        if "commit" in fail:
            raise GhError("No commit found for SHA: abc (HTTP 422)")
        return {"sha": HEAD, "commit": {"message": message, "author": {"date": "2026-10-02T12:00:00Z"}}, "parents": [{"sha": OLD}]}

    return {"gh": gh}


class VerifyCommitTests(unittest.TestCase):
    def test_resolves_prefix_to_full_commit(self):
        result, status = verify_commit("o/r", "aaaaaaa", **commit_fake())
        self.assertEqual((result["sha"], result["subject"], result["parents"]), (HEAD, "Fix the thing", [OLD]))
        self.assertEqual(result["expectations"], {})
        self.assertEqual(status, 0)

    def test_all_expectations_hold(self):
        result, status = verify_commit("o/r", "aaaaaaa", subject="Fix the thing", on="main", pr_head=("o/r", 7), **commit_fake())
        self.assertEqual(result["expectations"], {"subject_matches": True, "on_branch": True, "is_pr_head": True})
        self.assertEqual(status, 0)

    def test_wrong_subject_exits_3(self):
        result, status = verify_commit("o/r", "aaaaaaa", subject="Something else", **commit_fake())
        self.assertFalse(result["expectations"]["subject_matches"])
        self.assertEqual(status, 3)

    def test_commit_not_in_branch_history(self):
        for compare in ("ahead", "diverged"):
            result, status = verify_commit("o/r", "aaaaaaa", on="main", **commit_fake(compare=compare))
            self.assertFalse(result["expectations"]["on_branch"])
            self.assertEqual(status, 3)

    def test_identical_to_branch_is_on_it(self):
        result, _ = verify_commit("o/r", "aaaaaaa", on="main", **commit_fake(compare="identical"))
        self.assertTrue(result["expectations"]["on_branch"])

    def test_pr_head_moved(self):
        result, status = verify_commit("o/r", "aaaaaaa", pr_head=("o/r", 7), **commit_fake(head=OLD))
        self.assertEqual(result["pr_head"], OLD)
        self.assertFalse(result["expectations"]["is_pr_head"])
        self.assertEqual(status, 3)

    def test_failed_expectation_read_is_null(self):
        result, status = verify_commit("o/r", "aaaaaaa", on="main", **commit_fake(fail={"compare"}))
        self.assertIsNone(result["expectations"]["on_branch"])
        self.assertEqual(result["errors"][0]["part"], "on_branch")
        self.assertEqual(status, 2)

    def test_false_expectation_outranks_read_error(self):
        _, status = verify_commit("o/r", "aaaaaaa", subject="Other", on="main", **commit_fake(fail={"compare"}))
        self.assertEqual(status, 3)

    def test_missing_commit_exits_1_with_prefix_note(self):
        result, status = verify_commit("o/r", "abc", **commit_fake(fail={"commit"}))
        self.assertEqual(status, 1)
        self.assertNotIn("sha", result)
        self.assertIn("full SHA", result["note"])


BOARD_OPTIONS = ["Backlog", "Ready", "In progress", "In review", "Done"]


class FakeBoard:
    """A board with one Status field, read through GraphQL projectItems pages; membership spans pages and reads report pagination."""

    def __init__(self, status=None, on_board=True, fail=(), sticky=True, lag=0,
                 advance=0, advance_to=None, member_page=1, incomplete_read=False,
                 missing_page_info=False, has_next_page_null=False,
                 missing_end_cursor=False, recheck_json_error=False,
                 readback_incomplete=False,
                 uncertain=False, fail_edits=0):
        self.status = status
        self.advance = advance
        self.advance_to = advance_to
        self.on_board = on_board
        self.fail = set(fail)
        self.sticky = sticky
        self.lag = lag
        self.page_count = member_page
        self.incomplete_read = incomplete_read
        self.missing_page_info = missing_page_info
        self.has_next_page_null = has_next_page_null
        self.missing_end_cursor = missing_end_cursor
        self.recheck_json_error = recheck_json_error
        self.readback_incomplete = readback_incomplete
        self.uncertain = uncertain
        self.fail_edits_remaining = fail_edits
        self.pending = None
        self.writes = []
        self.sleeps = []
        self.member_reads = 0

    def __call__(self, args):
        if args[:2] == ["project", "view"]:
            return {"id": "P1"}
        if args[:2] == ["project", "field-list"]:
            options = [{"id": f"opt-{i}", "name": name} for i, name in enumerate(BOARD_OPTIONS)]
            return {"fields": [{"id": "F0", "name": "Title"}, {"id": "F1", "name": "Status", "options": options}]}
        if args[:2] == ["project", "item-add"]:
            self.writes.append("add")
            self.on_board = True
            return {"id": "ITEM"}
        if args[:2] == ["project", "item-edit"]:
            if "write" in self.fail:
                raise GhError("HTTP 403")
            option = args[args.index("--single-select-option-id") + 1]
            if self.uncertain:
                self.writes.append(option)
                if self.sticky:
                    self.pending = BOARD_OPTIONS[int(option.split("-")[1])]
                raise GhError("HTTP 502")
            if self.fail_edits_remaining > 0:
                self.fail_edits_remaining -= 1
                self.writes.append("edit-failed")
                raise GhError("HTTP 403")
            self.writes.append(option)
            if self.sticky:
                self.pending = BOARD_OPTIONS[int(option.split("-")[1])]
            return {}
        if self.writes and "readback" in self.fail:
            raise GhError("HTTP 502")
        if "read" in self.fail:
            raise GhError("HTTP 502")
        if self.pending is not None:
            if self.lag:
                self.lag -= 1
            else:
                self.status, self.pending = self.pending, None
        self.member_reads += 1
        # recheck_json_error: on the second membership read (pre-write live re-read)
        # raise JSONDecodeError to exercise finding-D in read_item.
        if self.recheck_json_error and self.member_reads >= 2:
            raise json.JSONDecodeError("bad", "x", 0)
        page_index = min(self.member_reads, self.page_count)
        live = self.status
        if self.advance and self.member_reads > self.advance:
            live = self.advance_to
        if page_index < self.page_count:
            nodes = [{"id": "FILLER", "project": {"id": "P9"}, "fieldValueByName": {"name": "Backlog"}}]
            info = {"hasNextPage": True, "endCursor": f"CURSOR-{page_index}"}
        else:
            nodes = []
            if self.on_board:
                value = {"name": live} if live else {}
                nodes.append({"id": "ITEM", "project": {"id": "P1"}, "fieldValueByName": value})
            if self.missing_page_info:
                info = None   # entirely absent
            elif self.has_next_page_null:
                info = {"hasNextPage": None, "endCursor": None}
            elif self.missing_end_cursor:
                info = {"hasNextPage": True}   # hasNextPage=True but no endCursor
            elif self.readback_incomplete and self.writes:
                info = {"hasNextPage": True, "endCursor": None}   # post-write page incomplete
            else:
                info = {"hasNextPage": self.incomplete_read, "endCursor": None}
        if self.missing_page_info:
            return {"data": {"repository": {"issue": {"url": "https://github.com/o/r/issues/5",
                 "projectItems": {"nodes": nodes}}}}}
        return {"data": {"repository": {"issue": {"url": "https://github.com/o/r/issues/5",
             "projectItems": {"nodes": nodes, "pageInfo": info}}}}}


def set_status(board, status, **kwargs):
    return board_set_status("o/r", 5, "o", 6, status, gh=board, sleep=board.sleeps.append, **kwargs)


PRIORITIES = ["P0", "P1", "P2", "P3", "P4"]


class FakeFieldBoard:
    """A board with Status and Priority fields; the issue's Priority is read through a paginated projectItems query."""

    def __init__(self, priority="P2", on_board=True, sticky=True, fail=(), pages=1):
        self.priority, self.on_board, self.sticky, self.fail, self.pages = priority, on_board, sticky, set(fail), pages
        self.writes, self.reads, self.queried_fields = [], 0, []

    def __call__(self, args):
        if args[:2] == ["project", "view"]:
            return {"id": "P1"}
        if args[:2] == ["project", "field-list"]:
            return {"fields": [
                {"id": "F1", "name": "Status", "options": [{"id": "s0", "name": "Backlog"}]},
                {"id": "F2", "name": "Priority", "options": [{"id": f"p{i}", "name": n} for i, n in enumerate(PRIORITIES)]},
                {"id": "F3", "name": "Title"}]}
        if args[:2] == ["project", "item-edit"]:
            if "write" in self.fail:
                raise GhError("HTTP 403")
            option = args[args.index("--single-select-option-id") + 1]
            self.writes.append((args[args.index("--field-id") + 1], option))
            if self.sticky:
                self.priority = PRIORITIES[int(option[1:])]
            return {}
        if "readback" in self.fail and self.writes:
            raise GhError("HTTP 502")
        self.queried_fields.append(next(a.split("=", 1)[1] for a in args if a.startswith("field=")))
        self.reads += 1
        last = "page=CURSOR" in args or self.pages == 1
        nodes = [{"id": "OTHER", "project": {"id": "P9"}, "fieldValueByName": {"name": "P0"}}]
        if last and self.on_board:
            nodes.append({"id": "ITEM", "project": {"id": "P1"},
                          "fieldValueByName": {"name": self.priority} if self.priority else None})
        info = {"hasNextPage": False, "endCursor": None} if last else {"hasNextPage": True, "endCursor": "CURSOR"}
        return {"data": {"repository": {"issue": {"projectItems": {"pageInfo": info, "nodes": nodes}}}}}


def set_field(board, field, value):
    return board_set_field("o/r", 5, "me", 6, field, value, gh=board, sleep=lambda s: None)


class BoardSetFieldTests(unittest.TestCase):
    def test_sets_priority_and_reads_back(self):
        board = FakeFieldBoard("P2")
        result, status = set_field(board, "Priority", "p1")
        self.assertEqual((result["before"], result["target"], result["after"], status), ("P2", "P1", "P1", 0))
        self.assertEqual(result["item_id"], "ITEM")
        self.assertEqual(board.writes, [("F2", "p1")])
        self.assertEqual(set(board.queried_fields), {"Priority"})

    def test_reads_every_membership_page(self):
        result, status = set_field(FakeFieldBoard("P4", pages=2), "Priority", "P1")
        self.assertEqual((result["before"], status), ("P4", 0))

    def test_unchanged_value_writes_nothing(self):
        board = FakeFieldBoard("P1")
        result, status = set_field(board, "Priority", "P1")
        self.assertEqual((result["action"], board.writes, status), ("unchanged", [], 0))

    def test_unknown_field_or_value_exits_1_without_write(self):
        board = FakeFieldBoard()
        self.assertEqual(set_field(board, "Size", "S")[1], 1)
        self.assertEqual(set_field(board, "Title", "x")[1], 1)
        result, status = set_field(board, "Priority", "P9")
        self.assertEqual((status, result["options"]), (1, PRIORITIES))
        self.assertEqual(board.writes, [])

    def test_status_field_is_refused(self):
        board = FakeFieldBoard()
        result, status = set_field(board, "Status", "Backlog")
        self.assertEqual((status, board.writes), (1, []))
        self.assertIn("set-status", result["errors"][0]["error"])

    def test_issue_not_on_board_is_not_added(self):
        board = FakeFieldBoard(on_board=False)
        result, status = set_field(board, "Priority", "P1")
        self.assertEqual((status, board.writes, result["errors"][0]["part"]), (1, [], "membership"))

    def test_write_that_does_not_stick_exits_2(self):
        result, status = set_field(FakeFieldBoard("P2", sticky=False), "Priority", "P1")
        self.assertEqual((result["after"], result["readback_matches"], result["readback_attempts"], status), ("P2", False, 4, 2))

    def test_failed_write_that_did_not_land_exits_1(self):
        result, status = set_field(FakeFieldBoard("P2", fail={"write"}), "Priority", "P1")
        self.assertEqual((result["action"], status), ("uncertain", 1))

    def test_failed_readback_exits_2(self):
        result, status = set_field(FakeFieldBoard("P2", fail={"readback"}), "Priority", "P1")
        self.assertEqual((result["after"], status), (None, 2))


class BoardSetStatusTests(unittest.TestCase):
    def test_forward_move_sets_and_reads_back(self):
        board = FakeBoard("In progress")
        result, status = set_status(board, "In review")
        self.assertEqual(result["item_id"], "ITEM")
        self.assertEqual((result["before"], result["action"], result["after"]), ("In progress", "set", "In review"))
        self.assertTrue(result["readback_matches"])
        self.assertEqual(board.writes, ["opt-3"])
        self.assertEqual(status, 0)

    def test_option_name_matched_case_insensitively(self):
        result, _ = set_status(FakeBoard("Backlog"), "in progress")
        self.assertEqual(result["target"], "In progress")

    def test_unknown_option_exits_1_with_options(self):
        board = FakeBoard("Backlog")
        result, status = set_status(board, "Doing")
        self.assertEqual(status, 1)
        self.assertEqual(result["options"], BOARD_OPTIONS)
        self.assertEqual(board.writes, [])

    def test_same_status_is_unchanged_without_write(self):
        board = FakeBoard("In review")
        result, status = set_status(board, "In review")
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 0)

    def test_backward_move_refused(self):
        board = FakeBoard("Done")
        result, status = set_status(board, "In review")
        self.assertEqual((result["action"], result["after"]), ("refused", "Done"))
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 3)

    def test_backward_move_allowed_with_flag(self):
        result, status = set_status(FakeBoard("Done"), "In review", allow_backward=True)
        self.assertEqual((result["action"], result["after"], status), ("set", "In review", 0))

    def test_issue_without_status_moves_forward(self):
        result, status = set_status(FakeBoard(None), "Backlog")
        self.assertEqual((result["before"], result["after"], status), (None, "Backlog", 0))

    def test_issue_not_on_board_is_added(self):
        board = FakeBoard(on_board=False)
        result, status = set_status(board, "In progress")
        self.assertTrue(result["added"])
        self.assertEqual(board.writes, ["add", "opt-2"])
        self.assertEqual((result["after"], status), ("In progress", 0))

    def test_failed_write_exits_1(self):
        result, status = set_status(FakeBoard("Backlog", fail={"write"}), "In progress")
        self.assertEqual(result["errors"][0]["part"], "write")
        self.assertEqual(status, 1)

    def test_write_that_does_not_stick_exits_2(self):
        board = FakeBoard("Backlog", sticky=False)
        result, status = set_status(board, "In progress")
        self.assertEqual(result["after"], "Backlog")
        self.assertFalse(result["readback_matches"])
        self.assertEqual(result["readback_attempts"], 4)
        self.assertEqual(len(board.sleeps), 3)
        self.assertEqual(status, 2)

    def test_lagging_readback_is_retried(self):
        board = FakeBoard("Backlog", lag=2)
        result, status = set_status(board, "Ready")
        self.assertEqual((result["after"], result["readback_attempts"], status), ("Ready", 3, 0))
        self.assertTrue(result["readback_matches"])
        self.assertEqual(board.writes, ["opt-1"])

    def test_immediate_readback_does_not_sleep(self):
        board = FakeBoard("Backlog")
        result, _ = set_status(board, "Ready")
        self.assertEqual((result["readback_attempts"], board.sleeps), (1, []))

    def test_failed_readback_exits_2(self):
        result, status = set_status(FakeBoard("Backlog", fail={"readback"}), "In progress")
        self.assertIsNone(result["after"])
        self.assertEqual(result["errors"][0]["part"], "readback")
        self.assertEqual(status, 2)

    def test_stale_advance_between_reads_is_refused_without_write(self):
        board = FakeBoard("In progress", advance=1, advance_to="Done")
        result, status = set_status(board, "In review")
        self.assertEqual((result["action"], result["after"]), ("stale-refused", "Done"))
        self.assertEqual(result["before"], "In progress")
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 3)
        self.assertIn("another actor", result["reason"].lower())

    def test_stale_advance_refused_even_when_backward_allowed(self):
        board = FakeBoard("In progress", advance=1, advance_to="Done")
        result, status = set_status(board, "Backlog", allow_backward=True)
        self.assertEqual((result["action"], result["after"]), ("stale-refused", "Done"))
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 3)

    def test_member_on_later_page_is_found_by_paginating(self):
        board = FakeBoard("In review", member_page=3)
        result, status = set_status(board, "In review")
        self.assertEqual((result["action"], result["after"]), ("unchanged", "In review"))
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 0)
        self.assertGreaterEqual(board.member_reads, 3)

    def test_incomplete_read_refuses_add_on_assumed_absence(self):
        board = FakeBoard(on_board=False, incomplete_read=True)
        result, status = set_status(board, "In progress")
        self.assertEqual(result["action"], "refused")
        self.assertFalse(result["membership_complete"])
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 1)

    def test_failed_membership_read_blocks_add(self):
        board = FakeBoard(on_board=False, fail={"read"})
        result, status = set_status(board, "In progress")
        self.assertEqual(result["errors"][0]["part"], "issue")
        self.assertEqual(board.writes, [])
        self.assertEqual(status, 1)

    def test_stale_transition_with_item_removed_fires_refused(self):
        # An item is removed between reads; the guard compares full (id, status), so
        # None != (id, status) triggers stale-refused, not item-add.
        board = FakeBoard("In progress", on_board=True, advance=1, advance_to=None)
        result, status = set_status(board, "In review")
        self.assertEqual(result["action"], "stale-refused")
        self.assertFalse(result.get("added", True))
        self.assertEqual(status, 3)

    def test_incomplete_readback_does_not_report_success(self):
         # The post-write read page reports incomplete=True with the target present;
         # the result must not be status 0.
        board = FakeBoard("Backlog", readback_incomplete=True)
        result, status = set_status(board, "Ready")
        self.assertEqual(status, 2)
        self.assertFalse(result.get("readback_matches", False))

    def test_missing_page_info_marks_read_incomplete(self):
        # A response with absent pageInfo causes incomplete=True, which for an absent
        # item leads to "refused", not an item-add.
        board = FakeBoard(on_board=False, missing_page_info=True)
        result, status = set_status(board, "In progress")
        self.assertEqual(result["action"], "refused")
        self.assertFalse(result.get("membership_complete", True))
        self.assertEqual(status, 1)

    def test_non_boolean_has_next_page_is_incomplete(self):
        board = FakeBoard(on_board=False, has_next_page_null=True)
        result, status = set_status(board, "In progress")
        self.assertEqual(result["action"], "refused")
        self.assertEqual(status, 1)

    def test_missing_end_cursor_is_incomplete(self):
        board = FakeBoard(on_board=False, missing_end_cursor=True)
        result, status = set_status(board, "In progress")
        self.assertEqual(result["action"], "refused")
        self.assertEqual(status, 1)

    def test_recheck_catches_json_decode_error(self):
        board = FakeBoard("In progress", recheck_json_error=True)
        result, status = set_status(board, "In review")
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "recheck")

    def test_edit_succeeds_readback_fails_records_unknown_fact(self):
        board = FakeBoard("Backlog", fail={"readback"})
        result, status = set_status(board, "In progress")
        self.assertEqual(status, 2)
        self.assertIsNone(result["after"])
        self.assertFalse(result["readback_matches"])
        self.assertEqual(result["action"], "set")
        self.assertEqual(result["facts"][-1], {"step": "readback", "state": "unknown"})
        self.assertEqual(board.writes, ["opt-2"])

    def test_reuse_after_successful_add_no_duplicate(self):
        board = FakeBoard(on_board=False, fail_edits=1)
        result, status = set_status(board, "In progress")
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "write")
        self.assertTrue(result["added"])
        self.assertEqual(board.writes, ["add", "edit-failed"])
        result2, status2 = set_status(board, "In progress")
        self.assertEqual(status2, 0)
        self.assertFalse(result2["added"])
        self.assertEqual(result2["action"], "set")
        self.assertEqual(board.writes.count("add"), 1)
        self.assertEqual(board.status, "In progress")

    def test_missing_option_id_is_structured_error(self):
        # An option missing its id must surface as a structured board error, not a
        # traceback at the option_id lookup in the write block.
        def board(args):
            if args[:2] == ["project", "view"]:
                return {"id": "P1"}
            if args[:2] == ["project", "field-list"]:
                return {"fields": [{"id": "F1", "name": "Status",
                                     "options": [{"name": "Backlog"}]}]}
            raise Exception("unreachable")
        result, status = board_set_status("o/r", 5, "o", 6, "Backlog", gh=board, sleep=lambda *a: None)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "board")


    def test_reuse_after_successful_edit_no_duplicate(self):
        board = FakeBoard("In progress")
        result, status = set_status(board, "In review")
        self.assertEqual(status, 0)
        self.assertEqual(result["action"], "set")
        self.assertEqual(board.writes, ["opt-3"])
        result2, status2 = set_status(board, "In review")
        self.assertEqual(status2, 0)
        self.assertEqual(result2["action"], "unchanged")
        self.assertEqual(board.writes, ["opt-3"])
        self.assertEqual(board.status, "In review")

    def test_uncertain_write_reconciled_by_fresh_read(self):
        board = FakeBoard("Backlog", uncertain=True)
        result, status = set_status(board, "In progress")
        self.assertEqual(status, 0)
        self.assertEqual(result["action"], "reconciled")
        self.assertEqual(result["after"], "In progress")
        self.assertTrue(result["readback_matches"])
        self.assertTrue(any(f["step"] == "status" and f["state"] == "uncertain"
                             for f in result["facts"]))

    def test_repeated_calls_converge_without_duplicate_or_loss(self):
        board = FakeBoard(on_board=False, fail_edits=1)
        result1, status1 = set_status(board, "In progress")
        self.assertEqual(status1, 1)
        result2, status2 = set_status(board, "In progress")
        self.assertEqual(status2, 0)
        self.assertEqual(board.writes.count("add"), 1)
        self.assertEqual(board.status, "In progress")


class IdentityTests(unittest.TestCase):
    def init_repository(self, path):
        os.makedirs(path, exist_ok=True)
        subprocess.run(["git", "init", "-q", path], check=True)

    def write_identity(self, directory, login):
        config_dir = os.path.join(directory, ".ghflow")
        os.makedirs(config_dir, exist_ok=True)
        config_path = os.path.join(config_dir, "identity.json")
        with open(config_path, "w", encoding="utf-8") as config:
            json.dump({"login": login}, config)
        return os.path.realpath(config_path)

    def resolve_in(self, path, env=None, home=None):
        old_cwd = os.getcwd()
        try:
            test_home = home or os.path.dirname(os.path.abspath(path))
            with patch.dict(os.environ, {"HOME": test_home}):
                os.chdir(path)
                return resolve_identity(env={} if env is None else env)
        finally:
            os.chdir(old_cwd)

    def test_project_identity_is_stable_from_root_and_subdirectory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = os.path.join(temp_dir, "repo")
            self.init_repository(repo)
            source = self.write_identity(repo, "ProjectBot")
            subdirectory = os.path.join(repo, "src", "nested")
            os.makedirs(subdirectory)

            root_identity = self.resolve_in(repo)
            nested_identity = self.resolve_in(subdirectory)

            self.assertEqual(root_identity["login"], "ProjectBot")
            self.assertEqual(nested_identity["login"], "ProjectBot")
            self.assertEqual(root_identity["source"], source)
            self.assertEqual(nested_identity["source"], source)

            old_cwd = os.getcwd()
            try:
                os.chdir(subdirectory)
                with patch.dict(os.environ, {"HOME": temp_dir}):
                    stdout = io.StringIO()
                    with patch("sys.stdout", stdout):
                        self.assertEqual(main(["identity"]), 1)
                report = json.loads(stdout.getvalue())
            finally:
                os.chdir(old_cwd)
            self.assertEqual(report["source"], source)

    def test_project_identity_preserves_trailing_space_in_checkout_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = os.path.join(temp_dir, "checkout ")
            self.init_repository(repo)
            source = self.write_identity(repo, "SpaceBot")

            identity = self.resolve_in(repo)

            self.assertEqual(identity["login"], "SpaceBot")
            self.assertEqual(identity["source"], source)

    def test_linked_worktree_finds_primary_config_when_checkout_path_has_newline(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            primary = os.path.join(temp_dir, "primary\ncheckout")
            linked = os.path.join(temp_dir, "linked")
            self.init_repository(primary)
            primary_source = self.write_identity(primary, "NewlineBot")
            subprocess.run(["git", "-C", primary, "worktree", "add", "-q", "-b", "linked", linked], check=True)

            identity = self.resolve_in(linked)

            self.assertEqual(identity["login"], "NewlineBot")
            self.assertEqual(identity["source"], primary_source)

    def test_linked_worktree_finds_primary_config_when_checkout_path_has_carriage_return(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            primary = os.path.join(temp_dir, "primary\rcheckout")
            linked = os.path.join(temp_dir, "linked\rworktree")
            self.init_repository(primary)
            primary_source = self.write_identity(primary, "CarriageReturnBot")
            subprocess.run(["git", "-C", primary, "worktree", "add", "-q", "-b", "linked", linked], check=True)

            identity = self.resolve_in(linked)

            self.assertEqual(identity["login"], "CarriageReturnBot")
            self.assertEqual(identity["source"], primary_source)

    def test_nested_repository_uses_its_own_project_identity(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            outer = os.path.join(temp_dir, "outer")
            inner = os.path.join(outer, "nested", "inner")
            self.init_repository(outer)
            self.init_repository(inner)
            self.write_identity(outer, "OuterBot")
            inner_source = self.write_identity(inner, "InnerBot")

            identity = self.resolve_in(inner)

            self.assertEqual(identity["login"], "InnerBot")
            self.assertEqual(identity["source"], inner_source)

    def test_linked_worktree_uses_primary_config_unless_local_config_exists(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            primary = os.path.join(temp_dir, "primary")
            linked = os.path.join(temp_dir, "linked")
            self.init_repository(primary)
            primary_source = self.write_identity(primary, "PrimaryBot")
            subprocess.run(["git", "-C", primary, "worktree", "add", "-q", "-b", "linked", linked], check=True)

            inherited = self.resolve_in(linked)
            self.assertEqual(inherited["login"], "PrimaryBot")
            self.assertEqual(inherited["source"], primary_source)

            local_source = self.write_identity(linked, "WorktreeBot")
            local = self.resolve_in(linked)
            self.assertEqual(local["login"], "WorktreeBot")
            self.assertEqual(local["source"], local_source)

    def test_explicit_environment_identity_overrides_project_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = os.path.join(temp_dir, "repo")
            self.init_repository(repo)
            self.write_identity(repo, "ProjectBot")

            identity = self.resolve_in(repo, {"GHFLOW_IDENTITY_LOGIN": "EnvBot"})

            self.assertEqual(identity["login"], "EnvBot")
            self.assertEqual(identity["source"], "environment")

    def test_invalid_selected_project_config_errors_without_home_fallback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = os.path.join(temp_dir, "repo")
            home = os.path.join(temp_dir, "home")
            self.init_repository(repo)
            os.makedirs(os.path.join(repo, ".ghflow"))
            selected = os.path.join(repo, ".ghflow", "identity.json")
            with open(selected, "w", encoding="utf-8") as config:
                config.write("{")
            home_config = os.path.join(home, ".config", "ghflow", "identity.json")
            os.makedirs(os.path.dirname(home_config), exist_ok=True)
            with open(home_config, "w", encoding="utf-8") as config:
                json.dump({"login": "HomeBot"}, config)

            with patch.dict(os.environ, {"HOME": home}):
                old_cwd = os.getcwd()
                try:
                    os.chdir(repo)
                    with self.assertRaisesRegex(GhError, "Invalid identity configuration") as error:
                        resolve_identity(env={})
                finally:
                    os.chdir(old_cwd)
            self.assertIn(selected, str(error.exception))

    def test_identity_command_reports_selected_config_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            repo = os.path.join(temp_dir, "repo")
            self.init_repository(repo)
            os.makedirs(os.path.join(repo, ".ghflow"))
            with open(os.path.join(repo, ".ghflow", "identity.json"), "w", encoding="utf-8") as config:
                config.write("{")

            old_cwd = os.getcwd()
            try:
                os.chdir(repo)
                with patch.dict(os.environ, {"HOME": temp_dir}), \
                        patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()) as stderr:
                    status = main(["identity"])
            finally:
                os.chdir(old_cwd)

            self.assertEqual(status, 1)
            self.assertIn("Invalid identity configuration", stderr.getvalue())

    def test_outside_git_uses_current_directory_then_home_config(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            cwd = os.path.join(temp_dir, "outside")
            home = os.path.join(temp_dir, "home")
            os.makedirs(cwd)
            home_config = os.path.join(home, ".config", "ghflow", "identity.json")
            os.makedirs(os.path.dirname(home_config))
            with open(home_config, "w", encoding="utf-8") as config:
                json.dump({"login": "HomeBot"}, config)

            with patch.dict(os.environ, {"HOME": home}):
                home_identity = self.resolve_in(cwd, home=home)
                current_source = self.write_identity(cwd, "CurrentBot")
                current_identity = self.resolve_in(cwd, home=home)

            self.assertEqual(home_identity["login"], "HomeBot")
            self.assertEqual(home_identity["source"], os.path.realpath(home_config))
            self.assertEqual(current_identity["login"], "CurrentBot")
            self.assertEqual(current_identity["source"], current_source)

    def test_identity_unconfigured_when_no_env_and_no_config(self):
        ident = resolve_identity(env={}, config_paths=[])
        self.assertFalse(ident["configured"])
        self.assertIsNone(ident["login"])
        self.assertIsNone(ident["token_file"])

    def test_identity_from_config_file(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            json.dump({"login": "BotUser", "email": "bot@example.com"}, f)
            cfg_path = f.name
        try:
            ident = resolve_identity(env={}, config_paths=[cfg_path])
            self.assertTrue(ident["configured"])
            self.assertEqual(ident["login"], "BotUser")
            self.assertEqual(ident["name"], "BotUser")
            self.assertEqual(ident["email"], "bot@example.com")
        finally:
            os.unlink(cfg_path)

    def test_identity_env_overrides_config(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            json.dump({"login": "BotUser", "email": "bot@example.com"}, f)
            cfg_path = f.name
        try:
            env = {"GHFLOW_IDENTITY_LOGIN": "EnvBot", "GHFLOW_IDENTITY_EMAIL": "env@example.com"}
            ident = resolve_identity(env=env, config_paths=[cfg_path])
            self.assertEqual(ident["login"], "EnvBot")
            self.assertEqual(ident["email"], "env@example.com")
        finally:
            os.unlink(cfg_path)

    def test_identity_env_sets_variables(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("secret-token\n")
            token_path = f.name
        try:
            ident = {
                "login": "BotUser",
                "name": "Bot User",
                "email": "bot@example.com",
                "token_file": token_path,
            }
            env = identity_env(ident, base_env={})
            self.assertEqual(env["GH_TOKEN"], "secret-token")
            self.assertEqual(env["GIT_AUTHOR_NAME"], "Bot User")
            self.assertEqual(env["GIT_COMMITTER_NAME"], "Bot User")
            self.assertEqual(env["GIT_AUTHOR_EMAIL"], "bot@example.com")
            self.assertEqual(env["GIT_COMMITTER_EMAIL"], "bot@example.com")
            self.assertIn("GIT_CONFIG_PARAMETERS", env)
        finally:
            os.unlink(token_path)

    def test_selected_token_and_git_identity_override_inherited_values(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("selected-token\n")
            token_path = f.name
        try:
            inherited_config = "'example.unrelated=value' 'credential.https://github.com.helper=old-helper'"
            env = identity_env(
                {"login": "BotUser", "name": "Selected Bot", "email": "selected@example.com", "token_file": token_path},
                base_env={
                    "GH_TOKEN": "inherited-token",
                    "GITHUB_TOKEN": "other-inherited-token",
                    "GIT_AUTHOR_NAME": "Inherited Author",
                    "GIT_COMMITTER_NAME": "Inherited Committer",
                    "GIT_AUTHOR_EMAIL": "inherited-author@example.com",
                    "GIT_COMMITTER_EMAIL": "inherited-committer@example.com",
                    "GIT_CONFIG_PARAMETERS": inherited_config,
                },
            )
            self.assertEqual(env["GH_TOKEN"], "selected-token")
            self.assertNotIn("GITHUB_TOKEN", env)
            self.assertEqual(env["GIT_AUTHOR_NAME"], "Selected Bot")
            self.assertEqual(env["GIT_COMMITTER_NAME"], "Selected Bot")
            self.assertEqual(env["GIT_AUTHOR_EMAIL"], "selected@example.com")
            self.assertEqual(env["GIT_COMMITTER_EMAIL"], "selected@example.com")
            parameters = shlex.split(env["GIT_CONFIG_PARAMETERS"])
            self.assertIn("example.unrelated=value", parameters)
            self.assertNotIn("credential.https://github.com.helper=old-helper", parameters)
            self.assertIn("credential.https://github.com.helper=!gh auth git-credential", parameters)
        finally:
            os.unlink(token_path)

    def test_selected_token_file_must_exist_and_be_nonempty(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = os.path.join(temp_dir, "missing-token")
            with self.assertRaisesRegex(GhError, "selected token file is unavailable"):
                identity_env({"token_file": missing}, base_env={"GH_TOKEN": "inherited-token"})
            with self.assertRaisesRegex(GhError, "selected token file is unavailable"):
                identity_env({"token_file": temp_dir}, base_env={"GH_TOKEN": "inherited-token"})
            empty = os.path.join(temp_dir, "empty-token")
            open(empty, "w").close()
            with self.assertRaisesRegex(GhError, "selected token file is empty"):
                identity_env({"token_file": empty}, base_env={"GH_TOKEN": "inherited-token"})

    def test_exec_stops_before_child_when_selected_token_file_is_unavailable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            ident = {"login": "BotUser", "name": "BotUser", "email": "bot@example.com",
                     "token_file": os.path.join(temp_dir, "missing-token"), "token_present": False,
                     "configured": True, "ready": False}
            with patch.dict(os.environ, {}, clear=True), \
                    patch("ghflow.resolve_identity", return_value=ident), \
                    patch("ghflow.subprocess.run") as run:
                stderr = io.StringIO()
                with patch("sys.stderr", stderr):
                    status = main(["exec", "--", "gh", "api", "user"])
            self.assertEqual(status, 1)
            self.assertIn("selected token file is unavailable", stderr.getvalue())
            run.assert_not_called()

    def test_identity_configuration_and_readiness_are_distinct(self):
        ident = resolve_identity(env={"GHFLOW_IDENTITY_LOGIN": "BotUser"}, config_paths=[])
        self.assertTrue(ident["configured"])
        self.assertFalse(ident["ready"])
        self.assertFalse(ident["token_present"])

    def test_identity_login_with_inherited_gh_token_is_ready(self):
        ident = resolve_identity(env={"GHFLOW_IDENTITY_LOGIN": "BotUser", "GH_TOKEN": "fake-token"}, config_paths=[])
        self.assertTrue(ident["ready"])
        self.assertTrue(ident["token_present"])

    def test_inherited_github_token_is_not_selected_without_a_token_file(self):
        env = identity_env({"token_file": None}, base_env={"GITHUB_TOKEN": "other-token"})
        self.assertNotIn("GITHUB_TOKEN", env)
        self.assertNotIn("GH_TOKEN", env)

    def test_identity_command_reports_configured_but_not_ready(self):
        ident = {"login": "BotUser", "name": "BotUser", "email": None, "token_file": None,
                 "token_present": False, "configured": True, "ready": False}
        with patch("ghflow.resolve_identity", return_value=ident):
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                status = main(["identity"])
        self.assertEqual(status, 1)
        report = json.loads(stdout.getvalue())
        self.assertTrue(report["configured"])
        self.assertFalse(report["ready"])

    def test_selected_git_helper_wins_and_unrelated_config_survives(self):
        env = identity_env(
            {"token_file": None},
            base_env={
                "GH_TOKEN": "synthetic-token",
                "GIT_CONFIG_PARAMETERS": "'example.unrelated=preserved' 'credential.https://github.com.helper'='old-helper'",
            },
        )
        unrelated = subprocess.run(
            ["git", "config", "--get", "example.unrelated"], env=env, text=True, capture_output=True,
        )
        helpers = subprocess.run(
            ["git", "config", "--get-all", "credential.https://github.com.helper"], env=env, text=True, capture_output=True,
        )
        self.assertEqual(unrelated.stdout.strip(), "preserved")
        self.assertEqual(helpers.stdout.strip(), "!gh auth git-credential")

    def test_separately_quoted_git_config_key_and_value_survive(self):
        parameters = "'url.https://example.com/?ref=main.insteadOf'='example-alias:'"
        base_env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": "/private/tmp/ghflow22-test-home",
            "TMPDIR": "/private/tmp",
            "GH_TOKEN": "synthetic-token",
            "GIT_CONFIG_PARAMETERS": parameters,
        }
        before = subprocess.run(
            ["git", "config", "--get-regexp", "^url\\."], env=base_env, text=True, capture_output=True,
        )
        env = identity_env({"token_file": None}, base_env=base_env)
        after = subprocess.run(
            ["git", "config", "--get-regexp", "^url\\."], env=env, text=True, capture_output=True,
        )
        self.assertEqual(before.returncode, 0, before.stderr)
        self.assertEqual(after.returncode, 0, after.stderr)
        self.assertEqual(after.stdout, before.stdout)
        self.assertEqual(after.stdout.strip(), "url.https://example.com/?ref=main.insteadof example-alias:")

    def test_identity_export_unsets_inherited_github_token(self):
        ident = {"login": "FakeBot", "name": "FakeBot", "email": "bot@example.com", "token_file": None}
        with patch.dict(os.environ, {"GITHUB_TOKEN": "synthetic-inherited-token"}, clear=True), \
                patch("ghflow.resolve_identity", return_value=ident):
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                status = main(["identity", "--export"])

        self.assertEqual(status, 0)
        helper = "import json, os; print(json.dumps({'present': 'GITHUB_TOKEN' in os.environ}))"
        completed = subprocess.run(
            ["/bin/sh", "-c", stdout.getvalue() + f"\nexec python3 -c {shlex.quote(helper)}"],
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "GITHUB_TOKEN": "synthetic-inherited-token"},
            text=True, capture_output=True, check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(json.loads(completed.stdout), {"present": False})

    def test_exec_stops_git_commit_without_selected_author_email(self):
        with patch.dict(os.environ, {}, clear=True), \
                patch("ghflow.resolve_identity", return_value={"login": "BotUser", "name": "BotUser", "email": None, "token_file": None, "token_present": False, "configured": True, "ready": False}), \
                patch("ghflow.subprocess.run") as run:
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                status = main(["exec", "--", "git", "commit", "-m", "test"])
        self.assertEqual(status, 1)
        self.assertIn("author name and email", stderr.getvalue())
        run.assert_not_called()

    def test_identity_command_export(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            marker_path = os.path.join(temp_dir, "shell-expanded")
            token = f"token $value `tick` 'single' \"double\"\n$(touch {marker_path})"
            name = f"Bot $name `tick` 'single' \"double\"\n$(touch {marker_path})"
            email = "bot $email `tick` 'single' \"double\"\n@example.com"
            git_config = "'credential.https://github.com.helper=' $value `tick`\nnext"
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as token_file:
                token_file.write(token)
                token_path = token_file.name
            try:
                ident = {
                    "login": "BotUser",
                    "name": name,
                    "email": email,
                    "token_file": token_path,
                    "configured": True,
                }
                with patch("ghflow.resolve_identity", return_value=ident), \
                        patch.dict(os.environ, {"GIT_CONFIG_PARAMETERS": git_config}, clear=True):
                    stdout = io.StringIO()
                    with patch("sys.stdout", stdout):
                        status = main(["identity", "--export"])

                self.assertEqual(status, 0)
                exported = stdout.getvalue()
                names = [
                    "GH_TOKEN",
                    "GITHUB_TOKEN",
                    "GIT_AUTHOR_NAME",
                    "GIT_COMMITTER_NAME",
                    "GIT_AUTHOR_EMAIL",
                    "GIT_COMMITTER_EMAIL",
                    "GIT_CONFIG_PARAMETERS",
                ]
                helper = (
                    "import json, os; "
                    f"print(json.dumps({{key: os.environ.get(key) for key in {tuple(names)!r}}}))"
                )
                read_exports = f"\nexec python3 -c {shlex.quote(helper)}"
                completed = subprocess.run(
                    ["/bin/sh", "-c", exported + read_exports],
                    env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")},
                    text=True,
                    capture_output=True,
                    check=False,
                )

                self.assertEqual(completed.returncode, 0, completed.stderr)
                exported_env = json.loads(completed.stdout)
                self.assertEqual(
                    {key: value for key, value in exported_env.items() if key != "GIT_CONFIG_PARAMETERS"},
                    {
                        "GH_TOKEN": token,
                        "GITHUB_TOKEN": None,
                        "GIT_AUTHOR_NAME": name,
                        "GIT_COMMITTER_NAME": name,
                        "GIT_AUTHOR_EMAIL": email,
                        "GIT_COMMITTER_EMAIL": email,
                    },
                )
                parameters = shlex.split(exported_env["GIT_CONFIG_PARAMETERS"])
                self.assertEqual(parameters[-2:], [
                    "credential.https://github.com.helper=",
                    "credential.https://github.com.helper=!gh auth git-credential",
                ])
                self.assertIn("$value", parameters)
                self.assertIn("`tick`", parameters)
                self.assertIn("next", parameters)
                self.assertFalse(os.path.exists(marker_path), "shell metacharacter executed")
            finally:
                os.unlink(token_path)

    def test_run_gh_uses_configured_identity(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
            f.write("bot-token\n")
            token_path = f.name
        try:
            ident = {"login": "BotUser", "name": "BotUser", "email": None, "token_file": token_path}
            completed = subprocess.CompletedProcess([], 0, stdout='{"ok": true}', stderr="")
            with patch("ghflow.resolve_identity", return_value=ident), \
                    patch.dict(os.environ, {}, clear=True), \
                    patch("ghflow.subprocess.run", return_value=completed) as run:
                self.assertEqual(run_gh(["api", "user"]), {"ok": True})
            self.assertEqual(run.call_args.kwargs["env"]["GH_TOKEN"], "bot-token")
        finally:
            os.unlink(token_path)


class StructuredResponseTests(unittest.TestCase):
    """Malformed or incomplete external responses become structured errors, not tracebacks."""

    def test_null_pr_response_is_structured_error(self):
        result, status = pr_state("o/r", 7, gh=lambda args: None, gh_paginated=lambda path: [])
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")
        self.assertNotIn("head", result)

    def test_list_pr_response_is_structured_error(self):
        result, status = pr_state("o/r", 7, gh=lambda args: [1, 2, 3], gh_paginated=lambda path: [])
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")

    def test_malformed_pr_json_is_structured_error(self):
        def gh(args):
            raise json.JSONDecodeError("bad", "x", 0)
        result, status = pr_state("o/r", 7, gh=gh, gh_paginated=lambda path: [])
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")

    def test_missing_pr_field_is_structured_error(self):
        data = pr()
        del data["headRefOid"]
        result, status = pr_state("o/r", 7, **fake(data))
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")

    def test_null_commit_response_is_structured_error(self):
        result, status = verify_commit("o/r", "abc", gh=lambda args: None)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "commit")
        self.assertNotIn("sha", result)

    def test_missing_commit_field_is_structured_error(self):
        gh = lambda args: {"commit": {"message": "x", "author": {"date": "d"}}}
        result, status = verify_commit("o/r", "abc", gh=gh)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "commit")
        self.assertNotIn("sha", result)

    def test_malformed_commit_json_is_structured_error(self):
        def gh(args):
            raise json.JSONDecodeError("bad", "x", 0)
        result, status = verify_commit("o/r", "abc", gh=gh)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "commit")

    def test_malformed_board_json_is_structured_error(self):
        def board(args):
            raise json.JSONDecodeError("bad", "x", 0)
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=board, sleep=lambda *a: None)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "board")

    def test_malformed_issue_query_json_is_structured_error(self):
        def board(args):
            if args[:2] == ["project", "view"]:
                return {"id": "P1"}
            if args[:2] == ["project", "field-list"]:
                options = [{"id": f"opt-{i}", "name": name} for i, name in enumerate(BOARD_OPTIONS)]
                return {"fields": [{"id": "F1", "name": "Status", "options": options}]}
            raise json.JSONDecodeError("bad", "x", 0)
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=board, sleep=lambda *a: None)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "issue")

    def test_missing_issue_query_field_is_structured_error(self):
        def board(args):
            if args[:2] == ["project", "view"]:
                return {"id": "P1"}
            if args[:2] == ["project", "field-list"]:
                options = [{"id": f"opt-{i}", "name": name} for i, name in enumerate(BOARD_OPTIONS)]
                return {"fields": [{"id": "F1", "name": "Status", "options": options}]}
            if "graphql" in args:
                return {}
            return {}
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=board, sleep=lambda *a: None)
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "issue")

    def test_on_branch_catches_json_decode_error(self):
         def gh(args):
             joined = " ".join(args)
             if "commits/" in joined:
                return {"sha": "abc", "commit": {"message": "x", "author": {"date": "d"}}, "parents": [{"sha": "O"}]}
             if "compare" in joined:
                raise json.JSONDecodeError("bad", "x", 0)
             return {"status": "behind"}
         result, status = verify_commit("o/r", "abc", on="main", gh=gh)
         self.assertEqual(status, 2)
         self.assertEqual(result["errors"][0]["part"], "on_branch")

    def test_is_pr_head_catches_json_decode_error(self):
         def gh(args):
             joined = " ".join(args)
             if "commits/" in joined:
                return {"sha": "abc", "commit": {"message": "x", "author": {"date": "d"}}, "parents": []}
             if "pr" in joined and "view" in joined:
                raise json.JSONDecodeError("bad", "x", 0)
             return {"headRefOid": "abc"}
         result, status = verify_commit("o/r", "abc", pr_head=("o/r", 7), gh=gh)
         self.assertEqual(status, 2)
         self.assertEqual(result["errors"][0]["part"], "is_pr_head")

    def test_non_string_commit_message_is_structured_error(self):
        result, status = verify_commit("o/r", "abc", gh=lambda a: {"sha": "abc", "commit": {"message": 123, "author": {"date": "d"}}})
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "commit")

    def test_null_parent_entry_is_structured_error(self):
        result, status = verify_commit("o/r", "abc", gh=lambda a: {"sha": "abc", "commit": {"message": "x", "author": {"date": "d"}}, "parents": [None]})
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "commit")

    def test_absent_parent_list_is_empty(self):
        result, status = verify_commit("o/r", "abc", gh=lambda a: {"sha": "abc", "commit": {"message": "x", "author": {"date": "d"}}})
        self.assertEqual(status, 0)
        self.assertEqual(result["parents"], [])

    def test_null_in_review_requests_is_structured_error(self):
         def gh(args):
             if "pr" in args:
                return {"number": 7, "url": "u", "state": "open", "isDraft": False, "mergeable": "MERGEABLE",
                        "headRefOid": "abc", "headRefName": "b", "baseRefName": "main",
                        "reviewRequests": [None], "statusCheckRollup": None}
             return []
         result, status = pr_state("o/r", 7, gh=gh, gh_paginated=lambda p: [])
         self.assertEqual(status, 1)
         self.assertEqual(result["errors"][0]["part"], "pr")

    def test_null_board_option_name_is_structured_error(self):
         def board(args):
             if args[:2] == ["project", "view"]:
                return {"id": "P1"}
             if args[:2] == ["project", "field-list"]:
                return {"fields": [{"id": "F", "name": "Status", "options": [{"id": "o1", "name": None}]}]}
             raise Exception("unreachable")
         result, status = board_set_status("o/r", 5, "o", 6, "Ready", gh=board, sleep=lambda *a: None)
         self.assertEqual(status, 1)
         self.assertEqual(result["errors"][0]["part"], "board")


class ResponseValueTests(unittest.TestCase):
    def test_null_check_entry_is_structured_error(self):
        result, status = pr_state("o/r", 7, **fake(pr(statusCheckRollup=[None])))
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "pr")
        self.assertNotIn("head", result)

    def test_invalid_required_pr_scalars_are_structured_errors(self):
        for field in ("number", "url", "state", "isDraft", "mergeable", "headRefOid", "headRefName", "baseRefName"):
            for value in (None, [], {}, 123 if field != "number" else True):
                with self.subTest(field=field, value=value):
                    result, status = pr_state("o/r", 7, **fake(pr(**{field: value})))
                    self.assertEqual(status, 1)
                    self.assertEqual(result["errors"][0]["part"], "pr")
                    self.assertNotIn("head", result)

    def test_invalid_pr_collection_entries_are_structured_errors(self):
        for field, entry in (("reviewRequests", None), ("reviewRequests", {}),
                             ("reviewRequests", {"login": 123}),
                             ("statusCheckRollup", {}),
                             ("statusCheckRollup", {"__typename": "CheckRun", "name": "test", "status": []}),
                             ("statusCheckRollup", {"__typename": "StatusContext", "context": [], "state": "SUCCESS"})):
            with self.subTest(field=field, entry=entry):
                result, status = pr_state("o/r", 7, **fake(pr(**{field: [entry]})))
                self.assertEqual(status, 1)
                self.assertEqual(result["errors"][0]["part"], "pr")

    def test_nullable_rollup_and_check_conclusion_still_work(self):
        result, status = pr_state("o/r", 7, **fake(pr(statusCheckRollup=None), rules_data=[]))
        self.assertEqual((status, result["checks"], result["ci"]), (0, [], "none"))
        result, status = pr_state("o/r", 7, **fake(pr(statusCheckRollup=[
            {"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": None}])))
        self.assertEqual((status, result["ci"]), (0, "pending"))

    def test_unfinished_checks_accept_empty_gh_conclusions(self):
        for state in ("IN_PROGRESS", "QUEUED"):
            with self.subTest(state=state):
                data = pr(statusCheckRollup=[{"__typename": "CheckRun", "name": "test", "status": state, "conclusion": ""}])
                result, status = pr_state("o/r", 7, **fake(data))
                self.assertEqual(status, 0)
                self.assertEqual(result["head"], HEAD)
                self.assertEqual(result["ci"], "pending")
                self.assertEqual(result["errors"], [])

    def test_invalid_rule_entries_leave_required_checks_unread(self):
        for data in ([None], {}, [{"type": []}], rules([])):
            with self.subTest(data=data):
                result, status = pr_state("o/r", 7, **fake(pr(), rules_data=data))
                self.assertEqual(status, 2)
                self.assertIsNone(result["required_checks"])
                self.assertIsNone(result["checks"][0]["required"])
                self.assertEqual(result["head"], HEAD)
                self.assertEqual(result["errors"][0]["part"], "required_checks")

    def test_invalid_behind_counts_leave_compare_unread(self):
        for value in (None, "0", True, -1, [], {}):
            with self.subTest(value=value):
                result, status = pr_state("o/r", 7, **fake(pr(), behind_by=value))
                self.assertEqual(status, 2)
                self.assertIsNone(result["base_behind_by"])
                self.assertEqual(result["head"], HEAD)
                self.assertEqual(result["errors"][0]["part"], "base_behind_by")

    def test_invalid_reviews_and_comments_preserve_pr_facts(self):
        for kwargs in ({"reviews": [None]}, {"reviews": [review([], "bot", HEAD, "t")]},
                       {"reviews": [review(1, 123, HEAD, "t")]},
                       {"reviews": [review(1, "bot", HEAD, [])]},
                       {"comments": [None]}, {"comments": [{"pull_request_review_id": []}]}):
            with self.subTest(kwargs=kwargs):
                result, status = pr_state("o/r", 7, **fake(pr(), **kwargs))
                self.assertEqual(status, 2)
                self.assertIsNone(result["reviews"])
                self.assertEqual(result["head"], HEAD)
                self.assertEqual(result["ci"], "green")
                self.assertEqual(result["errors"][0]["part"], "reviews")

    def test_nullable_review_values_preserve_other_facts(self):
        data = review(1, "bot", None, None, state="PENDING", body=None)
        data["user"] = None
        result, status = pr_state("o/r", 7, **fake(pr(), reviews=[data], timeline=[requested("bot", "t")]))
        self.assertEqual(status, 0)
        self.assertIsNone(result["reviews"][0]["author"])
        self.assertIsNone(result["reviews"][0]["commit"])
        self.assertFalse(result["reviews"][0]["covers_head"])
        self.assertFalse(result["latest_review_requests"][0]["answered"])

    def test_invalid_timeline_entries_leave_requests_unread(self):
        for entry in (None, {"event": []}, requested([], "t"), requested("bot", [])):
            with self.subTest(entry=entry):
                result, status = pr_state("o/r", 7, **fake(pr(), timeline=[entry]))
                self.assertEqual(status, 2)
                self.assertIsNone(result["review_request_events"])
                self.assertIsNone(result["latest_review_requests"])
                self.assertEqual(result["head"], HEAD)
                self.assertEqual(result["ci"], "green")
                self.assertEqual(result["errors"][0]["part"], "review_request_events")

    def test_invalid_commit_scalars_are_structured_errors(self):
        for field, value in (("sha", 123), ("sha", None), ("date", []), ("parent", {"sha": 123})):
            with self.subTest(field=field):
                data = {"sha": HEAD, "commit": {"message": "fix", "author": {"date": "d"}}, "parents": []}
                if field == "date":
                    data["commit"]["author"]["date"] = value
                elif field == "parent":
                    data["parents"] = [value]
                else:
                    data[field] = value
                result, status = verify_commit("o/r", "abc", gh=lambda args: data)
                self.assertEqual(status, 1)
                self.assertNotIn("sha", result)
                self.assertEqual(result["errors"][0]["part"], "commit")

    def test_nullable_commit_author_is_preserved(self):
        for author in (None, {}, {"date": None}):
            with self.subTest(author=author):
                result, status = verify_commit("o/r", "abc", gh=lambda args: {
                    "sha": HEAD, "commit": {"message": "fix", "author": author}, "parents": []})
                self.assertEqual((status, result["author_date"]), (0, None))

    def test_nullable_request_actor_and_team_request_still_work(self):
        event = {"event": "review_requested", "requested_team": {"slug": "maintainers"},
                 "requested_reviewer": None, "actor": None, "created_at": "t"}
        result, status = pr_state("o/r", 7, **fake(pr(reviewRequests=[{"slug": "maintainers"}]), timeline=[event]))
        self.assertEqual(status, 0)
        self.assertEqual(result["pending_review_requests"], ["maintainers"])
        self.assertEqual(result["latest_review_requests"][0]["reviewer"], "maintainers")
        self.assertIsNone(result["review_request_events"][0]["actor"])

    def test_invalid_verification_values_are_unread_not_false(self):
        for value in (123, None, [], {}, ""):
            with self.subTest(value=value):
                result, status = verify_commit("o/r", "abc", on="main", **commit_fake(compare=value))
                self.assertEqual(status, 2)
                self.assertIsNone(result["expectations"]["on_branch"])
                self.assertEqual(result["sha"], HEAD)
                result, status = verify_commit("o/r", "abc", pr_head=("o/r", 7), **commit_fake(head=value))
                self.assertEqual(status, 2)
                self.assertIsNone(result["expectations"]["is_pr_head"])
                self.assertNotIn("pr_head", result)
        result, status = verify_commit("o/r", "abc", on="main", **commit_fake(compare="unexpected"))
        self.assertEqual(status, 2)
        self.assertIsNone(result["expectations"]["on_branch"])

    def test_invalid_board_values_fail_before_write(self):
        for part in ("project", "fields", "field", "option", "node", "status", "url"):
            with self.subTest(part=part):
                board = FakeBoard("Backlog")
                def gh(args):
                    data = board(args)
                    if part == "project" and args[:2] == ["project", "view"]:
                        data["id"] = 123
                    elif args[:2] == ["project", "field-list"]:
                        if part == "fields": data["fields"] = {}
                        if part == "field": data["fields"] = [None]
                        if part == "option": data["fields"][1]["options"][0]["id"] = None
                    elif "graphql" in args:
                        issue = data["data"]["repository"]["issue"]
                        if part == "node": issue["projectItems"]["nodes"] = [None]
                        if part == "status": issue["projectItems"]["nodes"][0]["fieldValueByName"] = 123
                        if part == "url": issue["url"] = None
                    return data
                result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=gh, sleep=lambda _: None)
                self.assertEqual(status, 1)
                self.assertTrue(result["errors"])
                self.assertEqual(board.writes, [])

    def test_invalid_board_readback_preserves_completed_write(self):
        board = FakeBoard("Backlog")
        def gh(args):
            data = board(args)
            if "graphql" in args and board.writes:
                data["data"]["repository"]["issue"]["projectItems"]["nodes"] = [None]
            return data
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=gh, sleep=lambda _: None)
        self.assertEqual(status, 2)
        self.assertEqual(result["before"], "Backlog")
        self.assertIn({"step": "status", "state": "completed"}, result["facts"])
        self.assertIsNone(result["after"])
        self.assertFalse(result["readback_matches"])
        self.assertEqual(result["errors"][0]["part"], "readback")

    def test_nullable_board_status_moves_forward(self):
        board = FakeBoard()
        def gh(args):
            data = board(args)
            if "graphql" in args and not board.writes:
                data["data"]["repository"]["issue"]["projectItems"]["nodes"][0]["fieldValueByName"] = None
            return data
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=gh, sleep=lambda _: None)
        self.assertEqual(status, 0)
        self.assertIsNone(result["before"])
        self.assertEqual(result["after"], "In progress")

    def test_empty_next_cursor_refuses_add_without_repeating_page(self):
        board = FakeBoard(on_board=False)
        def gh(args):
            data = board(args)
            if "graphql" in args:
                self.assertEqual(board.member_reads, 1, "The reader repeated the same membership page.")
                data["data"]["repository"]["issue"]["projectItems"]["pageInfo"] = {"hasNextPage": True, "endCursor": ""}
            return data
        result, status = board_set_status("o/r", 5, "o", 6, "In progress", gh=gh, sleep=lambda _: None)
        self.assertEqual(status, 1)
        self.assertFalse(result["membership_complete"])
        self.assertEqual(board.writes, [])


class FakeGhHarness:
    """Run ghflow.py as a subprocess with a fake `gh` on PATH.

    The fake `gh` (fake_gh.py) records the arguments it receives and returns
    controlled responses from fixture files, with no network access.
    """

    GHFLOW = os.path.join(os.path.dirname(__file__), "ghflow.py")
    FAKE = os.path.join(os.path.dirname(__file__), "fake_gh.py")

    def __init__(self, replies=None, board=None):
        self.dir = tempfile.mkdtemp(prefix="fakegh-")
        self.replies = {"api:user": {"out": {"login": "FakeBot"}}}
        self.replies.update(replies or {})
        self.board = board
        self.log_path = os.path.join(self.dir, "calls.log")
        open(self.log_path, "w").close()

    def _write(self, name, obj):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f)
        return path

    def run(self, argv):
        env = {key: os.environ[key] for key in ("PATH", "LANG", "TMPDIR") if key in os.environ}
        env["HOME"] = self.dir
        env["GHFLOW_IDENTITY_LOGIN"] = "FakeBot"
        env["GH_TOKEN"] = "synthetic-fake-token"
        env["GHHOW_LOG"] = self.log_path
        if self.replies:
            env["GHHOW_REPLIES"] = self._write("replies.json", self.replies)
        if self.board is not None:
            env["GHHOW_BOARD"] = self._write("board.json", self.board)
        bin_dir = os.path.join(self.dir, "bin")
        os.makedirs(bin_dir, exist_ok=True)
        gh = os.path.join(bin_dir, "gh")
        with open(gh, "w", encoding="utf-8") as f:
            f.write('#!/bin/sh\nexec "%s" "%s" "$@"\n' % (sys.executable, self.FAKE))
        os.chmod(gh, 0o755)
        env["PATH"] = bin_dir + os.pathsep + env.get("PATH", "")
        result = subprocess.run(
             [sys.executable, self.GHFLOW, *argv],
             env=env, capture_output=True, text=True, cwd=self.dir,
         )
        with open(self.log_path, encoding="utf-8") as f:
            raw = f.read()
        calls = [json.loads(line)["argv"] for line in raw.splitlines() if line.strip()]
        out = json.loads(result.stdout) if result.stdout.strip() else None
        return result, out, calls

    @staticmethod
    def calls_by_cmd(calls, *cmds):
        return [c for c in calls if c and c[0] in cmds]

    @staticmethod
    def calls_with(calls, *needles):
        return [c for c in calls if all(any(needle in t for t in c) for needle in needles)]


def pr_view_out(**overrides):
    data = {
        "number": 7,
        "url": "https://github.com/o/r/pull/7",
        "state": "OPEN",
        "isDraft": False,
        "mergeable": "MERGEABLE",
        "headRefOid": HEAD,
        "headRefName": "task",
        "baseRefName": "main",
        "reviewRequests": [],
        "statusCheckRollup": [
            {"__typename": "CheckRun", "name": "test",
             "status": "COMPLETED", "conclusion": "SUCCESS"},
        ],
    }
    data.update(overrides)
    return data


class PrStateSubprocessTests(unittest.TestCase):
    def _harness(self, head=HEAD, reviews=None, comments=None, issue_comments=None,
                 timeline=None, rules_data=None, rules_pages=None, behind_by=0, missing=()):
        replies = {
            "pr.view:o/r:7": {"out": pr_view_out(headRefOid=head)},
            "api.paginate:repos/o/r/rules/branches/main": {
                "out": rules_pages if rules_pages is not None else [rules_data if rules_data is not None else rules("test")]},
            "api:repos/o/r/compare/main...%s" % head: {"out": {"behind_by": behind_by}},
            "api.paginate:repos/o/r/pulls/7/reviews": {"out": [list(reviews or [])]},
            "api.paginate:repos/o/r/pulls/7/comments": {"out": [list(comments or [])]},
            "api.paginate:repos/o/r/issues/7/comments": {"out": [list(issue_comments or [])]},
            "api.paginate:repos/o/r/issues/7/timeline": {"out": [list(timeline or [])]},
        }
        for part in missing:
            if part == "rules":
                replies["api.paginate:repos/o/r/rules/branches/main"] = {"code": 1, "err": "HTTP 403"}
            elif part == "compare":
                replies["api:repos/o/r/compare/main...%s" % head] = {"code": 1, "err": "HTTP 404"}
            elif part == "reviews":
                replies["api.paginate:repos/o/r/pulls/7/reviews"] = {"code": 5, "err": "HTTP 502"}
            elif part == "comments":
                replies["api.paginate:repos/o/r/issues/7/comments"] = {"code": 1, "err": "HTTP 500"}
        return FakeGhHarness(replies)

    def test_pr_state_reports_head_ci_and_exit_zero(self):
        h = self._harness()
        result, out, calls = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(out["head"], HEAD)
        self.assertEqual(out["base"], "main")
        self.assertEqual(out["ci"], "green")
        self.assertIsNotNone(out["reviews"])

    def test_unfinished_gh_checks_preserve_head_and_pending_ci(self):
        for state in ("IN_PROGRESS", "QUEUED"):
            with self.subTest(state=state):
                h = self._harness()
                h.replies["pr.view:o/r:7"]["out"]["statusCheckRollup"] = [
                    {"__typename": "CheckRun", "name": "test", "status": state, "conclusion": ""}]
                result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
                self.assertEqual(result.returncode, 0)
                self.assertEqual(out["head"], HEAD)
                self.assertEqual(out["ci"], "pending")
                self.assertEqual(out["errors"], [])

    def test_pr_state_sends_repo_identifiers_to_gh(self):
        h = self._harness()
        _, _, calls = h.run(["pr-state", "7", "--repo", "o/r"])
        pr_call = FakeGhHarness.calls_by_cmd(calls, "pr")[0]
        self.assertEqual(pr_call[:3], ["pr", "view", "7"])
        self.assertIn("--repo", pr_call)
        self.assertIn("o/r", pr_call)
        api_calls = FakeGhHarness.calls_by_cmd(calls, "api")
        rules_call = next(c for c in api_calls if "repos/o/r/rules/branches/main" in c)
        self.assertIn("--paginate", rules_call)
        self.assertIn("--slurp", rules_call)
        compare_call = next(c for c in api_calls if any("repos/o/r/compare/main..." in t for t in c))
        self.assertTrue(any("repos/o/r/compare/main..." in t for t in compare_call))

    def test_pr_state_reads_required_check_from_later_branch_rules_page(self):
        first_page = [{"type": f"other_rule_{index}"} for index in range(30)]
        second_page = rules("typecheck")
        h = self._harness(rules_pages=[first_page, second_page])
        result, out, calls = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(out["required_checks"], ["typecheck"])
        self.assertEqual(out["ci"], "missing")
        self.assertIn({"name": "typecheck", "state": "missing", "required": True}, out["checks"])
        rules_call = next(c for c in FakeGhHarness.calls_by_cmd(calls, "api")
                          if "repos/o/r/rules/branches/main" in c)
        self.assertEqual(rules_call[:2], ["api", "repos/o/r/rules/branches/main"])
        self.assertEqual(rules_call[2:], ["--paginate", "--slurp"])

    def test_pr_state_partial_later_rule_page_failure_leaves_inventory_unread(self):
        h = self._harness()
        h.replies["api.paginate:repos/o/r/rules/branches/main"] = {
            "out": [rules("test")], "code": 1, "err": "HTTP 502 on a later page"}
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(out["required_checks"])
        self.assertEqual(out["errors"][0]["part"], "required_checks")

    def test_pr_state_summarizes_checks_when_rules_are_unread(self):
        cases = (
            (
                "passed",
                [{"__typename": "CheckRun", "name": "test", "status": "COMPLETED", "conclusion": "SUCCESS"}],
                "incomplete",
                [{"name": "test", "state": "passed", "required": None}],
            ),
            (
                "pending",
                [{"__typename": "CheckRun", "name": "test", "status": "IN_PROGRESS", "conclusion": ""}],
                "pending",
                [{"name": "test", "state": "pending", "required": None}],
            ),
            (
                "failed",
                [{"__typename": "StatusContext", "context": "test", "state": "FAILURE"}],
                "failing",
                [{"name": "test", "state": "failed", "required": None}],
            ),
            ("empty", [], "incomplete", []),
        )
        for name, rollup, summary, checks in cases:
            with self.subTest(name=name):
                h = self._harness(missing={"rules"})
                h.replies["pr.view:o/r:7"]["out"]["statusCheckRollup"] = rollup
                result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
                self.assertEqual(result.returncode, 2)
                self.assertEqual(out["ci"], summary)
                self.assertEqual(out["checks"], checks)
                self.assertIsNone(out["required_checks"])
                self.assertEqual(out["errors"][0]["part"], "required_checks")
                self.assertIn("HTTP 403", out["errors"][0]["error"])

    def test_pr_state_invalid_later_branch_rules_page_leaves_inventory_unread(self):
        h = self._harness(rules_pages=[rules("test"), {"not": "a page array"}])
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(out["required_checks"])
        self.assertEqual(out["errors"][0]["part"], "required_checks")

    def test_pr_state_exercises_rest_pagination(self):
        h = self._harness(reviews=[review(1, "bot", HEAD, "t1")],
                          timeline=[requested("Copilot", "t0")])
        _, out, calls = h.run(["pr-state", "7", "--repo", "o/r"])
        paginated = FakeGhHarness.calls_with(calls, "--paginate", "--slurp")
        endpoints = [c[1] for c in paginated]
        self.assertIn("repos/o/r/pulls/7/reviews", endpoints)
        self.assertIn("repos/o/r/pulls/7/comments", endpoints)
        self.assertIn("repos/o/r/issues/7/timeline", endpoints)
        self.assertIsNotNone(out["reviews"])
        self.assertEqual(out["ci"], "green")

    def test_pr_state_unreadable_pr_exits_1(self):
        h = FakeGhHarness({"pr.view:o/r:7": {"code": 4, "err": "No matches found"}})
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(out["errors"][0]["part"], "pr")
        self.assertIsNone(out.get("reviews"))

    def test_pr_state_failed_part_preserves_others_and_exits_2(self):
        h = self._harness(missing={"reviews"})
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(out["reviews"])
        self.assertEqual(out["ci"], "green")
        self.assertEqual(out["errors"][0]["part"], "reviews")

    def test_pr_state_reads_top_level_comments_through_gh(self):
        h = self._harness(issue_comments=[{"id": 3, "user": {"login": "les"}, "created_at": "t",
                                           "html_url": "u", "body": "Looks fine."}], missing={"comments"})
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(out["comments"])
        self.assertEqual(out["errors"][0]["part"], "comments")
        h = self._harness(issue_comments=[{"id": 3, "user": {"login": "les"}, "created_at": "t",
                                           "html_url": "u", "body": "Looks fine."}])
        result, out, calls = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(out["comments"][0]["author"], "les")
        self.assertEqual(out["comments"][0]["body"], "Looks fine.")

    def test_pr_state_malformed_part_is_structured(self):
        h = self._harness()
        h.replies["api.paginate:repos/o/r/pulls/7/reviews"] = {"raw": "not json", "code": 0}
        result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
        self.assertEqual(result.returncode, 2)
        self.assertIsNone(out["reviews"])
        self.assertEqual(out["errors"][0]["part"], "reviews")
        self.assertTrue(out["errors"][0]["error"])
        self.assertEqual(out["ci"], "green")

    def test_invalid_primary_values_exit_1_with_json_and_no_traceback(self):
        for overrides in ({"statusCheckRollup": [None]}, {"headRefOid": 123},
                          {"reviewRequests": [None]}):
            with self.subTest(overrides=overrides):
                h = self._harness()
                h.replies["pr.view:o/r:7"] = {"out": pr_view_out(**overrides)}
                result, out, calls = h.run(["pr-state", "7", "--repo", "o/r"])
                self.assertEqual(result.returncode, 1)
                self.assertEqual(out["errors"][0]["part"], "pr")
                self.assertNotIn("head", out)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(len(calls), 1)

    def test_invalid_optional_values_exit_2_and_preserve_facts(self):
        cases = (
            ("api.paginate:repos/o/r/rules/branches/main", [[None]], "required_checks"),
            ("api:repos/o/r/compare/main...%s" % HEAD, {"behind_by": "0"}, "base_behind_by"),
            ("api.paginate:repos/o/r/pulls/7/reviews", [None], "reviews"),
            ("api.paginate:repos/o/r/pulls/7/comments", {"message": "not pages"}, "reviews"),
            ("api.paginate:repos/o/r/issues/7/comments", [None], "comments"),
            ("api.paginate:repos/o/r/issues/7/timeline", [[None]], "review_request_events"),
        )
        for endpoint, value, part in cases:
            with self.subTest(endpoint=endpoint):
                h = self._harness()
                h.replies[endpoint] = {"out": value}
                result, out, _ = h.run(["pr-state", "7", "--repo", "o/r"])
                self.assertEqual(result.returncode, 2)
                self.assertEqual(out["head"], HEAD)
                self.assertEqual(out["errors"][0]["part"], part)
                self.assertIsNone(out[part])
                self.assertNotIn("Traceback", result.stderr)


class VerifyCommitSubprocessTests(unittest.TestCase):
    def _harness(self, message="The fix\n\nwhy", compare="behind",
                 head=HEAD, fail_commit=False, rev="aaaaaaa"):
        replies = {
            "api:repos/o/r/commits/%s" % rev: {
                  "out": {"sha": HEAD, "commit": {"message": message,
                           "author": {"date": "2026-10-02T12:00:00Z"}},
                           "parents": [{"sha": OLD}]},
              },
              "pr.view:o/r:7": {"out": {"headRefOid": head}},
          }
        if compare is not None:
            replies["api.jq:repos/o/r/compare/main...%s:{status}" % head] = {"out": {"status": compare}}
        if fail_commit:
            replies["api:repos/o/r/commits/%s" % rev] = {
                  "code": 422,
                  "err": "No commit found for SHA: %s (HTTP 422)" % rev,
              }
        return FakeGhHarness(replies)

    def test_verify_commit_holds_expectations_exit_zero(self):
        h = self._harness(message="The fix\n\nwhy", compare="behind")
        result, out, _ = h.run([
             "verify-commit", "aaaaaaa", "--repo", "o/r",
             "--subject", "The fix", "--on", "main", "--pr-head", "7",
         ])
        self.assertEqual(result.returncode, 0)
        self.assertEqual(out["expectations"],
             {"subject_matches": True, "on_branch": True, "is_pr_head": True})

    def test_verify_commit_sends_repo_and_rev_to_gh(self):
        h = self._harness(message="The fix\n\nwhy", compare="behind")
        _, _, calls = h.run([
             "verify-commit", "aaaaaaa", "--repo", "o/r",
             "--subject", "The fix", "--on", "main", "--pr-head", "7",
         ])
        commit_call = FakeGhHarness.calls_with(calls, "repos/o/r/commits/aaaaaaa")
        self.assertTrue(commit_call)
        self.assertEqual(commit_call[0][:2], ["api", "repos/o/r/commits/aaaaaaa"])

    def test_verify_commit_false_subject_exit_3(self):
        h = self._harness(message="The fix\n\nwhy", compare="behind")
        result, out, _ = h.run([
             "verify-commit", "aaaaaaa", "--repo", "o/r",
             "--subject", "Other subject", "--on", "main", "--pr-head", "7",
         ])
        self.assertEqual(result.returncode, 3)
        self.assertFalse(out["expectations"]["subject_matches"])

    def test_verify_commit_missing_commit_exit_1(self):
        h = self._harness(fail_commit=True, rev="abc")
        result, out, _ = h.run(["verify-commit", "abc", "--repo", "o/r"])
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("sha", out)
        self.assertIn("full SHA", out["note"])

    def test_invalid_commit_sha_exits_1_without_invented_facts(self):
        h = self._harness()
        h.replies["api:repos/o/r/commits/aaaaaaa"]["out"]["sha"] = 123
        result, out, _ = h.run(["verify-commit", "aaaaaaa", "--repo", "o/r"])
        self.assertEqual(result.returncode, 1)
        self.assertEqual(out["errors"][0]["part"], "commit")
        self.assertNotIn("sha", out)
        self.assertNotIn("Traceback", result.stderr)

    def test_invalid_expectations_exit_2_without_false_mismatch(self):
        for part, value, endpoint in (
            ("on_branch", {"status": 123}, "api.jq:repos/o/r/compare/main...%s:{status}" % HEAD),
            ("is_pr_head", {"headRefOid": 123}, "pr.view:o/r:7"),
        ):
            with self.subTest(part=part):
                h = self._harness()
                h.replies[endpoint] = {"out": value}
                argv = ["verify-commit", "aaaaaaa", "--repo", "o/r"]
                argv += ["--on", "main"] if part == "on_branch" else ["--pr-head", "7"]
                result, out, _ = h.run(argv)
                self.assertEqual(result.returncode, 2)
                self.assertEqual(out["sha"], HEAD)
                self.assertIsNone(out["expectations"][part])
                self.assertEqual(out["errors"][0]["part"], part)
                self.assertNotIn("Traceback", result.stderr)


class BoardSetStatusSubprocessTests(unittest.TestCase):
    def _harness(self, status, target, allow_backward=False):
        board = {
            "project_id": "P1",
            "options": BOARD_OPTIONS,
            "status": status,
            "on_board": True,
        }
        argv = [
            "board", "set-status", "5", "--repo", "o/r",
            "--owner", "o", "--project", "6", "--status", target,
        ]
        if allow_backward:
            argv.append("--allow-backward")
        return FakeGhHarness(board=board), argv

    def test_board_forward_move_sets_and_reads_back_exit_zero(self):
        h, argv = self._harness("In progress", "In review")
        result, out, _ = h.run(argv)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(out["action"], "set")
        self.assertEqual(out["after"], "In review")
        self.assertTrue(out["readback_matches"])

    def test_board_sends_board_identifiers_to_gh(self):
        h, argv = self._harness("In progress", "In review")
        _, _, calls = h.run(argv)
        self.assertTrue(FakeGhHarness.calls_with(calls, "project"))
        edit_call = FakeGhHarness.calls_with(calls, "item-edit")
        self.assertTrue(edit_call)
        self.assertIn("--project-id", edit_call[0])
        self.assertIn("P1", edit_call[0])

    def test_board_login_mismatch_stops_before_write(self):
        h, argv = self._harness("In progress", "In review")
        h.replies["api:user"] = {"out": {"login": "OtherBot"}}
        result, out, calls = h.run(argv)
        self.assertEqual(result.returncode, 1)
        self.assertIn("authenticated login", json.dumps(out["errors"]))
        self.assertFalse(any(call[:2] in (["project", "item-add"], ["project", "item-edit"]) for call in calls))
        self.assertIn(["api", "user"], calls)

    def test_board_login_lookup_failure_stops_before_write(self):
        h, argv = self._harness("In progress", "In review")
        h.replies["api:user"] = {"code": 1, "err": "synthetic lookup failure"}
        result, out, calls = h.run(argv)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Could not confirm", json.dumps(out["errors"]))
        self.assertFalse(any(call[:2] in (["project", "item-add"], ["project", "item-edit"]) for call in calls))

    def test_board_backward_move_refused_exit_3(self):
        h, argv = self._harness("Done", "In review")
        result, out, _ = h.run(argv)
        self.assertEqual(result.returncode, 3)
        self.assertEqual(out["action"], "refused")
        self.assertEqual(out["after"], "Done")

    def test_board_unknown_option_exit_1(self):
        h, argv = self._harness("Done", "Doing")
        result, out, _ = h.run(argv)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(out.get("options"), BOARD_OPTIONS)


if __name__ == "__main__":
    unittest.main()


class FakePr:
    """A PR with a body and draft flag; writes are recorded and read-backs see them."""

    def __init__(self, is_draft=True, head=HEAD, state="OPEN", body="old body\n", fail=(), sticky=True, move_head_after=None):
        self.is_draft = is_draft
        self.head = head
        self.state = state
        self.body = body
        self.fail = set(fail)
        self.sticky = sticky
        self.move_head_after = move_head_after
        self.writes = []
        self.reads = 0

    def gh(self, args):
        if args[:2] == ["pr", "view"]:
            self.reads += 1
            if "view" in self.fail:
                raise GhError("HTTP 502")
            return {"number": 7, "url": "https://github.com/o/r/pull/7", "state": self.state, "isDraft": self.is_draft,
                    "headRefOid": self.head, "headRefName": "task", "baseRefName": "main", "body": self.body}
        raise AssertionError(f"Unexpected gh call: {args}")

    def gh_text(self, args):
        self.writes.append(args)
        if args[:2] == ["pr", "edit"]:
            if "edit" in self.fail:
                raise GhError("HTTP 500")
            if self.sticky:
                with open(args[args.index("--body-file") + 1], encoding="utf-8") as body:
                    self.body = body.read()
            if self.move_head_after == "edit":
                self.head = OLD
            return "https://github.com/o/r/pull/7\n"
        if args[:2] == ["pr", "ready"]:
            if "ready" in self.fail:
                raise GhError("HTTP 500")
            if self.sticky:
                self.is_draft = False
            if self.move_head_after == "ready":
                self.head = OLD
            return ""
        raise AssertionError(f"Unexpected gh write: {args}")


def ready(fake, body=None, expect_head=None, board=None, confirm=lambda: None, board_write=None, state=None, tmp=None):
    body_file = None
    if body is not None:
        body_file = os.path.join(tmp, "body.md")
        with open(body_file, "w", encoding="utf-8") as out:
            out.write(body)
    board_calls = []

    def default_board_write(repo, number, owner, project, status):
        board_calls.append((repo, number, owner, project, status))
        return {"before": "In progress", "after": status, "readback_matches": True}, 0

    def default_state(repo, number):
        return {"head": fake.head, "ci": "green", "pending_review_requests": [], "reviews": [], "comments": []}, 0

    result, status = pr_ready("o/r", 7, body_file, expect_head, board, gh=fake.gh, gh_text=fake.gh_text, confirm=confirm,
                              board_write=board_write or default_board_write, state=state or default_state)
    result["_board_calls"] = board_calls
    return result, status


class PrReadyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def test_description_ready_board_and_final_state_in_order(self):
        fake = FakePr()
        result, status = ready(fake, body="new body\n", expect_head=HEAD, board=("o/r", 5, "o", 6, "In review"), tmp=self.tmp)
        self.assertEqual(status, 0, result)
        self.assertEqual([w[:2] for w in fake.writes], [["pr", "edit"], ["pr", "ready"]])
        self.assertTrue(result["description_matches"])
        self.assertEqual(result["action"], "ready")
        self.assertEqual(result["after"], {"state": "OPEN", "is_draft": False, "head": HEAD})
        self.assertEqual(result["_board_calls"], [("o/r", 5, "o", 6, "In review")])
        self.assertEqual(result["board"]["after"], "In review")
        self.assertEqual(result["pr_state"]["ci"], "green")
        self.assertEqual([f["step"] for f in result["facts"]], ["description", "ready"])

    def test_body_compared_without_trailing_newline_differences(self):
        fake = FakePr()
        fake_write = fake.gh_text

        def gh_text(args):
            out = fake_write(args)
            if args[:2] == ["pr", "edit"]:
                fake.body = fake.body.rstrip("\n") + "\n\n"
            return out

        fake.gh_text = gh_text
        result, status = ready(fake, body="line one\r\nline two", tmp=self.tmp)
        self.assertEqual(status, 0, result)
        self.assertTrue(result["description_matches"])

    def test_expected_head_mismatch_refuses_without_writes(self):
        fake = FakePr()
        result, status = ready(fake, body="new\n", expect_head=OLD, tmp=self.tmp)
        self.assertEqual(status, 3)
        self.assertEqual(fake.writes, [])
        self.assertEqual(result["errors"][0]["part"], "head")
        self.assertEqual(result["facts"], [{"step": "write", "state": "refused"}])

    def test_short_expected_head_is_refused(self):
        fake = FakePr()
        result, status = ready(fake, expect_head=HEAD[:6], tmp=self.tmp)
        self.assertEqual(status, 3)
        self.assertEqual(fake.writes, [])

    def test_prefix_expected_head_matches(self):
        fake = FakePr()
        result, status = ready(fake, expect_head=HEAD[:12], tmp=self.tmp)
        self.assertEqual(status, 0, result)
        self.assertTrue(result["expected_head_matches"])

    def test_closed_pr_refused_without_writes(self):
        fake = FakePr(state="MERGED")
        result, status = ready(fake, body="new\n", tmp=self.tmp)
        self.assertEqual(status, 3)
        self.assertEqual(fake.writes, [])
        self.assertEqual(result["errors"][0]["part"], "state")

    def test_identity_failure_refuses_without_writes(self):
        fake = FakePr()

        def confirm():
            raise IdentityError("The authenticated login does not match the selected GitHub login.")

        result, status = ready(fake, body="new\n", confirm=confirm, tmp=self.tmp)
        self.assertEqual(status, 1)
        self.assertEqual(fake.writes, [])
        self.assertEqual(result["errors"][0]["part"], "identity")

    def test_missing_body_file_refuses_before_identity_and_writes(self):
        fake = FakePr()
        result, status = pr_ready("o/r", 7, os.path.join(self.tmp, "absent.md"), None, None, gh=fake.gh, gh_text=fake.gh_text,
                                  confirm=lambda: (_ for _ in ()).throw(AssertionError("confirm should not run")))
        self.assertEqual(status, 1)
        self.assertEqual(result["errors"][0]["part"], "body_file")
        self.assertEqual(fake.writes, [])

    def test_description_mismatch_stops_before_ready(self):
        fake = FakePr(sticky=False)
        result, status = ready(fake, body="new\n", tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertFalse(result["description_matches"])
        self.assertEqual([w[:2] for w in fake.writes], [["pr", "edit"]])
        self.assertTrue(fake.is_draft)
        self.assertNotIn("action", result)

    def test_failed_description_write_that_took_hold_is_reconciled_by_readback(self):
        fake = FakePr()
        fake_write = fake.gh_text

        def gh_text(args):
            if args[:2] == ["pr", "edit"]:
                fake.body = "new\n"
                raise GhError("HTTP 502 after write")
            return fake_write(args)

        fake.gh_text = gh_text
        result, status = ready(fake, body="new\n", tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertTrue(result["description_matches"])
        self.assertEqual(result["action"], "ready")
        self.assertEqual(result["errors"][0]["part"], "description")

    def test_head_moved_during_description_update_stops_before_ready(self):
        fake = FakePr(move_head_after="edit")
        result, status = ready(fake, body="new\n", tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertEqual([w[:2] for w in fake.writes], [["pr", "edit"]])
        self.assertEqual(result["errors"][-1]["part"], "head")
        self.assertTrue(fake.is_draft)

    def test_head_moved_after_ready_is_reported(self):
        fake = FakePr(move_head_after="ready")
        result, status = ready(fake, tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertEqual(result["action"], "ready")
        self.assertEqual(result["after"]["head"], OLD)
        self.assertEqual(result["errors"][-1]["part"], "head")
        self.assertEqual(result["_board_calls"], [])

    def test_ready_that_does_not_stick_exits_2_without_board(self):
        fake = FakePr(sticky=False)
        result, status = ready(fake, board=("o/r", 5, "o", 6, "In review"), tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertEqual(result["facts"][-1], {"step": "ready", "state": "mismatch"})
        self.assertEqual(result["_board_calls"], [])
        self.assertNotIn("pr_state", result)

    def test_already_ready_is_unchanged_and_still_moves_board(self):
        fake = FakePr(is_draft=False)
        result, status = ready(fake, board=("o/r", 5, "o", 6, "In review"), tmp=self.tmp)
        self.assertEqual(status, 0, result)
        self.assertEqual(fake.writes, [])
        self.assertEqual(result["action"], "unchanged")
        self.assertEqual(len(result["_board_calls"]), 1)

    def test_board_failure_is_reported_after_ready(self):
        fake = FakePr()

        def board_write(repo, number, owner, project, status):
            return {"before": "Done", "after": "Done", "readback_matches": False, "errors": [{"part": "write", "error": "backward"}]}, 3

        result, status = ready(fake, board=("o/r", 5, "o", 6, "In review"), board_write=board_write, tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertEqual(result["action"], "ready")
        self.assertEqual(result["errors"][0], {"part": "board", "error": "board set-status exited 3."})
        self.assertIn("pr_state", result)

    def test_unreadable_pr_exits_1_without_writes(self):
        fake = FakePr(fail={"view"})
        result, status = ready(fake, body="new\n", tmp=self.tmp)
        self.assertEqual(status, 1)
        self.assertEqual(fake.writes, [])
        self.assertEqual(result["errors"][0]["part"], "pr")

    def test_partial_final_state_read_exits_2(self):
        fake = FakePr()

        def state(repo, number):
            return {"head": fake.head, "ci": None, "errors": [{"part": "rules", "error": "HTTP 403"}]}, 2

        result, status = ready(fake, state=state, tmp=self.tmp)
        self.assertEqual(status, 2)
        self.assertEqual(result["action"], "ready")
        self.assertEqual(result["errors"][0]["part"], "pr_state")

    def test_main_requires_board_arguments_together(self):
        with self.assertRaises(SystemExit) as raised, patch("sys.stderr", new=io.StringIO()):
            main(["pr", "ready", "https://github.com/o/r/pull/7", "--issue", "https://github.com/o/r/issues/5"])
        self.assertEqual(raised.exception.code, 2)

    def test_main_passes_board_tuple_and_prints_result(self):
        captured = {}

        def fake_pr_ready(repo, number, body_file, expect_head, board):
            captured.update(repo=repo, number=number, body_file=body_file, expect_head=expect_head, board=board)
            return {"action": "ready"}, 0

        with patch("ghflow.pr_ready", fake_pr_ready), patch("sys.stdout", new=io.StringIO()) as out:
            status = main(["pr", "ready", "https://github.com/o/r/pull/7", "--body-file", "b.md", "--expect-head", HEAD,
                           "--issue", "https://github.com/o/r/issues/5", "--owner", "o", "--project", "6"])
        self.assertEqual(status, 0)
        self.assertEqual(captured, {"repo": "o/r", "number": 7, "body_file": "b.md", "expect_head": HEAD,
                                    "board": ("o/r", 5, "o", 6, "In review")})
        self.assertEqual(json.loads(out.getvalue())["action"], "ready")

def git(args, cwd):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


class RuntimeFactsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.root = self.tmp / "project"
        self.home = self.tmp / "home"
        (self.home / ".config" / "opencode").mkdir(parents=True)
        self.root.mkdir()

    def test_no_runtime_variable(self):
        self.assertEqual(read_runtime(self.root, {}, self.home)["agent"], None)

    def test_claude_reports_unknown_limits_without_reading_models(self):
        info = read_runtime(self.root, {"CLAUDECODE": "1"}, self.home)
        self.assertEqual((info["agent"], info["nested_dispatch"]), ("claude", None))
        self.assertNotIn("config_default_model", info)

    def test_opencode_merges_global_and_project_config(self):
        (self.home / ".config" / "opencode" / "opencode.jsonc").write_text(
            '{\n  // comment with "quotes"\n  "model": "a/global",\n  "agent": {"review": {"model": "b/reviewer"},},\n}\n')
        (self.root / "opencode.json").write_text('{"model": "c/project", "permission": {"edit": "deny"}}')
        info = read_runtime(self.root, {"OPENCODE": "1"}, self.home)
        self.assertEqual((info["agent"], info["detected_by"], info["nested_dispatch"]), ("opencode", "OPENCODE", False))
        self.assertNotIn("config_default_model", info)
        self.assertEqual(info["agent_models"], {"review": "b/reviewer"})
        self.assertEqual([f["scope"] for f in info["config_files"]], ["global", "project"])
        self.assertIn("--model", info["subagent_model_rule"])

    def test_opencode_config_variable_is_read_first(self):
        custom = self.tmp / "custom.json"
        custom.write_text('{"model": "d/custom", "agent": {"general": {"model": "e/general"}}}')
        info = read_runtime(self.root, {"OPENCODE_PID": "7", "OPENCODE_CONFIG": str(custom)}, self.home)
        self.assertEqual(info["detected_by"], "OPENCODE_PID")
        self.assertEqual(info["config_files"][0], {"scope": "env", "path": str(custom)})
        self.assertEqual(info["agent_models"], {"general": "e/general"})

    def test_strip_jsonc_keeps_slashes_inside_strings(self):
        text = '{"url": "http://x/y", /* block */ "a": [1, 2,],}'
        self.assertEqual(json.loads(strip_jsonc(text)), {"url": "http://x/y", "a": [1, 2]})


class SkillSourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.origin = os.path.join(self.tmp, "skill.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.origin], check=True)
        self.skill = os.path.join(self.tmp, "skill")
        subprocess.run(["git", "clone", "-q", self.origin, self.skill], check=True, capture_output=True)
        for args in (["config", "user.email", "t@example.com"], ["config", "user.name", "t"], ["checkout", "-q", "-b", "main"],
                     ["commit", "-q", "--allow-empty", "-m", "one"], ["push", "-q", "-u", "origin", "main"]):
            git(args, self.skill)

    def test_up_to_date_with_remote(self):
        info = read_skill_source(Path(self.skill), ghflow.run_git)
        self.assertEqual((info["upstream"], info["up_to_date"], info["dirty"]), ("origin/main", True, False))

    def test_behind_remote_is_reported(self):
        other = os.path.join(self.tmp, "other")
        subprocess.run(["git", "clone", "-q", self.origin, other], check=True, capture_output=True)
        for args in (["config", "user.email", "t@example.com"], ["config", "user.name", "t"],
                     ["commit", "-q", "--allow-empty", "-m", "two"], ["push", "-q", "origin", "main"]):
            git(args, other)
        info = read_skill_source(Path(self.skill), ghflow.run_git)
        self.assertFalse(info["up_to_date"])
        self.assertNotEqual(info["remote_head"], info["head"])

    def test_no_upstream(self):
        git(["checkout", "-q", "-b", "local-only"], self.skill)
        info = read_skill_source(Path(self.skill), ghflow.run_git)
        self.assertEqual((info["branch"], info["upstream"], info["up_to_date"]), ("local-only", None, None))


class ProjectFactsTests(unittest.TestCase):
    """A clone of a local bare origin with the files a project facts read inspects."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.origin = os.path.join(self.tmp, "origin.git")
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", self.origin], check=True)
        self.clone = os.path.join(self.tmp, "clone")
        subprocess.run(["git", "clone", "-q", self.origin, self.clone], check=True, capture_output=True)
        git(["config", "user.email", "t@example.com"], self.clone)
        git(["config", "user.name", "t"], self.clone)
        git(["checkout", "-q", "-b", "main"], self.clone)
        self.write("AGENTS.md", "# Agents\n")
        self.write("Makefile", ".PHONY: check test\nVAR := x\ncheck: test\n\tpython3 scripts/check.py\ntest:\n\tpytest\nfmt-check:\n\truff\n")
        self.write("conftest.py", "")
        self.write("tests/conftest.py", "")
        self.write(".github/workflows/ci.yml", "name: ci\n")
        self.write(".env.example", "PORT=1\n")
        self.write("pyproject.toml", "[project]\nname='x'\n")
        git(["add", "-A"], self.clone)
        git(["commit", "-q", "-m", "feat: first commit"], self.clone)
        git(["push", "-q", "-u", "origin", "main"], self.clone)
        git(["remote", "set-head", "origin", "main"], self.clone)
        git(["remote", "set-url", "--push", "origin", self.origin], self.clone)
        git(["remote", "set-url", "origin", "git@github.com:o/r.git"], self.clone)
        self.skill = os.path.join(self.tmp, "skill")
        subprocess.run(["git", "clone", "-q", self.origin, self.skill], check=True, capture_output=True)

    def write(self, rel, text):
        path = os.path.join(self.clone, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as out:
            out.write(text)
        return path

    def blob(self, rel):
        return subprocess.run(["git", "hash-object", rel], cwd=self.clone, capture_output=True, text=True, check=True).stdout.strip()

    def facts(self, issue=None, gh=None, gh_paginated=None, cwd=None):
        def default_gh(args):
            if args[:2] == ["issue", "view"]:
                return {"url": "https://github.com/o/r/issues/5", "title": "Fix it", "state": "OPEN",
                        "labels": [{"name": "bug"}], "projectItems": [{"title": "Board", "status": {"name": "Ready"}}]}
            if args[:2] == ["pr", "list"]:
                return [{"number": 9, "url": "https://github.com/o/r/pull/9", "state": "OPEN", "isDraft": True,
                         "headRefName": "issue-5-fix", "headRefOid": HEAD, "title": "Fix #5"}]
            if args[:2] == ["api", "repos/o/r"]:
                return {"default_branch": "main"}
            if args[0] == "api" and args[1].endswith("/check-runs?per_page=100"):
                return {"check_runs": [{"name": "lint", "status": "completed", "conclusion": "success"},
                                       {"name": "test", "status": "completed", "conclusion": "success"}]}
            if args[0] == "api" and args[1].endswith("/status"):
                return {"statuses": []}
            raise AssertionError(f"Unexpected gh call: {args}")

        def default_paginated(path):
            return rules("lint", "test")

        return project_facts(cwd=cwd or self.clone, issue=issue, gh=gh or default_gh,
                             gh_paginated=gh_paginated or default_paginated, identity={"login": "bot", "configured": True, "ready": True, "source": "env"},
                             env={}, home=self.tmp, skill_root=self.skill)

    def test_base_ci_runtime_and_skill_source(self):
        result, status = self.facts()
        self.assertEqual(status, 0, result["errors"])
        head = result["repository"]["origin_default_head"]
        base = dict(result["base_ci"])
        age, stale = base.pop("fetch_age_seconds"), base.pop("stale")
        self.assertEqual(base, {"commit": head, "summary": "green",
                                "checks": [{"name": "lint", "state": "passed"}, {"name": "test", "state": "passed"}]})
        self.assertEqual(stale, age is None or age > 600)
        self.assertEqual(result["runtime"]["agent"], None)
        source = result["skill_source"]
        self.assertEqual((source["head"], source["branch"], source["upstream"], source["up_to_date"]), (head, "main", "origin/main", True))

    def test_base_ci_is_stale_without_a_recent_fetch(self):
        fetch_head = os.path.join(self.clone, ".git", "FETCH_HEAD")
        with open(fetch_head, "w") as out:
            out.write("")
        old = time.time() - 3600
        os.utime(fetch_head, (old, old))
        result, _ = self.facts()
        self.assertTrue(result["base_ci"]["stale"])
        self.assertGreater(result["base_ci"]["fetch_age_seconds"], 3500)
        os.utime(fetch_head, None)
        result, _ = self.facts()
        self.assertFalse(result["base_ci"]["stale"])

    def test_base_ci_reports_a_missing_required_check_and_a_failure(self):
        def gh(args):
            if args[1].endswith("/check-runs?per_page=100"):
                return {"check_runs": [{"name": "lint", "status": "completed", "conclusion": "failure"}]}
            if args[1].endswith("/status"):
                return {"statuses": [{"context": "ext", "state": "pending"}]}
            raise AssertionError(args)
        result, status = self.facts(gh=gh)
        self.assertEqual(status, 0, result["errors"])
        self.assertEqual(result["base_ci"]["summary"], "failing")
        self.assertIn({"name": "test", "state": "missing"}, result["base_ci"]["checks"])
        self.assertIn({"name": "ext", "state": "pending"}, result["base_ci"]["checks"])

    def test_unreadable_base_ci_is_a_part_error(self):
        def gh(args):
            raise GhError("HTTP 502")
        result, status = self.facts(gh=gh)
        self.assertEqual(status, 2)
        self.assertIsNone(result["base_ci"])
        self.assertIn("base_ci", [e["part"] for e in result["errors"]])

    def test_checkout_repository_and_project_files(self):
        result, status = self.facts()
        self.assertEqual(status, 0, result["errors"])
        self.assertEqual(result["checkout"]["branch"], "main")
        self.assertFalse(result["checkout"]["is_linked_worktree"])
        self.assertFalse(result["checkout"]["dirty"])
        self.assertEqual(result["repository"]["remote"], "o/r")
        self.assertEqual(result["repository"]["default_branch"], "main")
        self.assertEqual((result["repository"]["local_default_ahead"], result["repository"]["local_default_behind"]), (0, 0))
        self.assertEqual(result["repository"]["recent_subjects"], ["feat: first commit"])
        files = result["project_files"]
        self.assertEqual(files["instructions"], ["AGENTS.md"])
        self.assertEqual(files["make_targets"], ["check", "test", "fmt-check"])
        self.assertEqual(files["conftest_paths"], ["conftest.py", "tests/conftest.py"])
        self.assertEqual(files["ci_workflows"], [".github/workflows/ci.yml"])
        self.assertEqual(files["env_example"], ".env.example")
        self.assertTrue(files["python_project"])
        self.assertIsNone(files["pr_template"])
        self.assertEqual(result["required_checks"], ["lint", "test"])
        self.assertEqual(result["identity"], {"login": "bot", "configured": True, "ready": True, "source": "env"})
        self.assertEqual(result["project_facts"], {"path": ".ghflow/project.md", "present": False})
        self.assertIsNone(result["issue"])

    def test_local_default_behind_origin_is_counted(self):
        self.write("new.txt", "x\n")
        git(["add", "-A"], self.clone)
        git(["commit", "-q", "-m", "fix: second"], self.clone)
        git(["push", "-q", "origin", "main"], self.clone)
        git(["reset", "-q", "--hard", "HEAD~1"], self.clone)
        result, status = self.facts()
        self.assertEqual(status, 0, result["errors"])
        self.assertEqual(result["repository"]["local_default_behind"], 1)
        self.assertEqual(result["repository"]["recent_subjects"][0], "fix: second")

    def test_issue_branches_worktrees_prs_and_board(self):
        git(["branch", "issue-5-fix"], self.clone)
        git(["branch", "issue-55-other"], self.clone)
        wt = os.path.join(self.tmp, "wt-5")
        git(["worktree", "add", "-q", wt, "issue-5-fix"], self.clone)
        result, status = self.facts(issue=("o/r", 5))
        self.assertEqual(status, 0, result["errors"])
        issue = result["issue"]
        self.assertEqual(issue["title"], "Fix it")
        self.assertEqual(issue["labels"], ["bug"])
        self.assertEqual(issue["board_items"], [{"project": "Board", "status": "Ready"}])
        self.assertEqual(issue["branches"], ["issue-5-fix"])
        self.assertEqual([os.path.realpath(p) for p in issue["worktrees"]], [os.path.realpath(wt)])
        self.assertEqual(issue["prs"][0]["number"], 9)
        self.assertEqual(len(result["checkout"]["worktrees"]), 2)

    def test_linked_worktree_reports_primary_root(self):
        wt = os.path.join(self.tmp, "wt-linked")
        git(["worktree", "add", "-q", "-b", "task", wt], self.clone)
        result, status = self.facts(cwd=wt)
        self.assertEqual(status, 0, result["errors"])
        self.assertTrue(result["checkout"]["is_linked_worktree"])
        self.assertEqual(os.path.realpath(result["checkout"]["primary_root"]), os.path.realpath(self.clone))
        self.assertEqual(result["checkout"]["branch"], "task")

    def test_facts_file_current_and_stale_sources(self):
        agents = self.blob("AGENTS.md")
        self.write(".ghflow/project.md", f"---\nghflow_project_facts: 1\nwritten: 2026-10-12\nsources:\n  - AGENTS.md {agents}\n  - Makefile {'0' * 40}\n  - docs/gone.md {'1' * 40}\n---\n# Facts\n")
        result, status = self.facts()
        self.assertEqual(status, 0, result["errors"])
        facts = result["project_facts"]
        self.assertTrue(facts["present"])
        self.assertEqual(facts["written"], "2026-10-12")
        self.assertEqual(facts["sources"], 3)
        self.assertEqual([(s["path"], s["reason"]) for s in facts["stale_sources"]], [("Makefile", "changed"), ("docs/gone.md", "missing")])
        self.assertEqual(facts["stale_sources"][0]["current"], self.blob("Makefile"))

    def test_missing_origin_head_falls_back_to_gh_default_branch(self):
        os.remove(os.path.join(self.clone, ".git", "refs", "remotes", "origin", "HEAD"))
        result, status = self.facts()
        self.assertEqual(status, 0, result["errors"])
        self.assertEqual(result["repository"]["default_branch"], "main")

    def test_failed_gh_read_is_null_with_error_and_exit_2(self):
        def paginated(path):
            raise GhError("HTTP 403")

        result, status = self.facts(gh_paginated=paginated)
        self.assertEqual(status, 2)
        self.assertIsNone(result["required_checks"])
        self.assertEqual(result["errors"], [{"part": "required_checks", "error": "HTTP 403"}])
        self.assertEqual(result["repository"]["remote"], "o/r")

    def test_outside_a_repository_exits_1(self):
        result, status = self.facts(cwd=self.tmp)
        self.assertEqual(status, 1)
        self.assertIsNone(result["checkout"])
        self.assertEqual(result["errors"][0]["part"], "checkout")

    def test_parse_remote_forms(self):
        self.assertEqual(parse_remote("git@github.com:o/r.git"), "o/r")
        self.assertEqual(parse_remote("https://github.com/o/r.git\n"), "o/r")
        self.assertEqual(parse_remote("https://github.com/o/r"), "o/r")
        self.assertIsNone(parse_remote("https://example.com/o/r.git"))

    def test_parse_facts_sources_ignores_other_frontmatter(self):
        written, sources = parse_facts_sources("---\nwritten: 2026-10-12\nother:\n  - a b\nsources:\n  - X 1\n  - bad\n  - Y 2\nafter: z\n---\nbody")
        self.assertEqual(written, "2026-10-12")
        self.assertEqual(sources, [("X", "1"), ("Y", "2")])
        self.assertEqual(parse_facts_sources("no frontmatter"), (None, []))

    def test_main_facts_passes_issue(self):
        captured = {}

        def fake_facts(issue=None):
            captured["issue"] = issue
            return {"ok": True}, 0

        with patch("ghflow.project_facts", fake_facts), patch("sys.stdout", new=io.StringIO()) as out:
            status = main(["facts", "--issue", "https://github.com/o/r/issues/5"])
        self.assertEqual(status, 0)
        self.assertEqual(captured["issue"], ("o/r", 5))
        self.assertTrue(json.loads(out.getvalue())["ok"])
