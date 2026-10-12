#!/usr/bin/env python3
"""Deterministic GitHub reads and writes for the gh-project-workflow skills.

The command shells out to an authenticated `gh`. It reports facts and never
judges whether a review is favorable or whether work may merge.

A part that could not be read is null and has an entry in "errors". An empty
list means GitHub returned nothing. Exit status: 0 when every part was read,
2 when some parts failed, 1 when the PR or commit itself could not be read.
verify-commit exits 3 when the commit was read and an expectation is false.
board set-status exits 3 when it refuses a backward move or a detected stale
transition, and exits 1 when a membership read could not be read in full.
pr ready exits 3 when it refuses to write because the PR is not open or its head
is not the expected commit, and 2 when a write happened but a read-back failed.
"""

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

CHECK_RUN_STATES = {
    "SUCCESS": "passed",
    "NEUTRAL": "passed",
    "SKIPPED": "skipped",
    "CANCELLED": "canceled",
    "FAILURE": "failed",
    "TIMED_OUT": "failed",
    "STARTUP_FAILURE": "failed",
    "ACTION_REQUIRED": "failed",
    "STALE": "failed",
}
STATUS_CONTEXT_STATES = {
    "SUCCESS": "passed",
    "PENDING": "pending",
    "EXPECTED": "pending",
    "FAILURE": "failed",
    "ERROR": "failed",
}


class GhError(Exception):
    pass


class IdentityError(GhError):
    pass


def response_type(value, expected, label):
    """Check a consumed response value before attribute access or comparison."""
    valid = type(value) is expected if expected in (int, bool) else isinstance(value, expected)
    if not valid:
        description = {dict: "an object", list: "a list", str: "a string", int: "an integer", bool: "a boolean"}[expected]
        raise ValueError(f"{label} is not {description}.")
    return value


def response_string(value, label, nullable=False, empty=False):
    if nullable and value is None:
        return None
    response_type(value, str, label)
    if not empty and not value:
        raise ValueError(f"{label} is empty.")
    return value


def response_integer(value, label):
    response_type(value, int, label)
    if value < 0:
        raise ValueError(f"{label} is negative.")
    return value


def run_gh(args):
    """Run gh under the configured agent identity and return parsed JSON output."""
    identity = resolve_identity()
    env = identity_env(identity)
    if args[:2] in (["project", "item-add"], ["project", "item-edit"]):
        confirm_authenticated_login(identity, env)
    result = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise GhError((result.stderr or result.stdout).strip() or f"gh exited {result.returncode}")
    return json.loads(result.stdout) if result.stdout.strip() else None


def run_gh_text(args):
    """Run a gh write under the configured agent identity and return its text output.

    Commands such as ``gh pr edit`` and ``gh pr ready`` print text, not JSON.
    The caller confirms the write identity first and reads the result back.
    """
    identity = resolve_identity()
    env = identity_env(identity)
    result = subprocess.run(["gh", *args], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise GhError((result.stderr or result.stdout).strip() or f"gh exited {result.returncode}")
    return result.stdout


def confirm_write_identity():
    """Confirm that the active token belongs to the selected login before a GitHub write."""
    identity = resolve_identity()
    confirm_authenticated_login(identity, identity_env(identity))


def confirm_authenticated_login(identity, env):
    """Make sure a board mutation uses a token for the selected login."""
    login = identity.get("login")
    if not login:
        raise IdentityError("A selected GitHub login is required before a board write.")
    if not identity.get("ready"):
        raise IdentityError("A selected login and usable token are required before a board write.")
    result = subprocess.run(["gh", "api", "user"], capture_output=True, text=True, env=env)
    if result.returncode != 0:
        raise IdentityError("Could not confirm the authenticated GitHub login before a board write.")
    try:
        profile = json.loads(result.stdout)
        actual = profile.get("login") if isinstance(profile, dict) else None
    except (json.JSONDecodeError, AttributeError):
        actual = None
    if not isinstance(actual, str) or actual.casefold() != login.casefold():
        raise IdentityError("The authenticated login does not match the selected GitHub login.")


def is_git_commit_command(command):
    """Recognize a direct Git commit invocation without inspecting scripts."""
    if not command or os.path.basename(command[0]) not in {"git", "git.exe"}:
        return False
    index = 1
    takes_value = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--super-prefix", "--config-env"}
    while index < len(command):
        token = command[index]
        if token == "--":
            index += 1
            break
        if token in takes_value:
            index += 2
            continue
        if token.startswith("-"):
            index += 1
            continue
        return token == "commit"
    return index < len(command) and command[index] == "commit"


def git_config_parameter_tokens(parameters):
    """Split GIT_CONFIG_PARAMETERS while preserving each parameter's original encoding."""
    tokens = []
    index = 0
    while index < len(parameters):
        while index < len(parameters) and parameters[index].isspace():
            index += 1
        if index == len(parameters):
            break
        start = index
        quote = None
        while index < len(parameters):
            char = parameters[index]
            if quote:
                if char == quote:
                    quote = None
                elif char == "\\" and quote == '"' and index + 1 < len(parameters):
                    index += 1
            elif char in ("'", '"'):
                quote = char
            elif char == "\\" and index + 1 < len(parameters):
                index += 1
            elif char.isspace():
                break
            index += 1
        if quote:
            raise ValueError("An inherited Git configuration parameter has an unclosed quote.")
        token = parameters[start:index]
        if len(shlex.split(token)) != 1:
            raise ValueError("An inherited Git configuration parameter has invalid quoting.")
        tokens.append(token)
    return tokens


def run_gh_paginated(path):
    """Read every page of a REST list endpoint."""
    pages = run_gh(["api", path, "--paginate", "--slurp"])
    response_type(pages, list, "The paginated response")
    for page in pages:
        response_type(page, list, "A response page")
    return [item for page in pages for item in page]


def parse_pr(ref, repo):
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/pull/(\d+)", ref)
    if match:
        return match.group(1), int(match.group(2))
    if ref.isdigit() and repo:
        return repo, int(ref)
    raise SystemExit("Give a PR URL, or a PR number with --repo OWNER/NAME.")


def parse_issue(ref, repo):
    match = re.match(r"https://github\.com/([^/]+/[^/]+)/issues/(\d+)", ref)
    if match:
        return match.group(1), int(match.group(2))
    if ref.isdigit() and repo:
        return repo, int(ref)
    raise SystemExit("Give an issue URL, or an issue number with --repo OWNER/NAME.")


def check_state(item):
    if item.get("__typename") == "StatusContext":
        return item.get("context"), STATUS_CONTEXT_STATES.get(item.get("state"), "unknown")
    if item.get("status") != "COMPLETED":
        return item.get("name"), "pending"
    return item.get("name"), CHECK_RUN_STATES.get(item.get("conclusion"), "unknown")


def summarize_ci(checks, required):
    """Summarize observed check states and whether required-check discovery succeeded."""
    if checks is None:
        return None
    states = {c["state"] for c in checks}
    if "failed" in states or "canceled" in states or "unknown" in states:
        return "failing"
    if any(c["state"] == "missing" for c in checks):
        return "missing"
    if "pending" in states:
        return "pending"
    if required is None:
        return "incomplete"
    if not checks:
        return "none"
    return "green"


def same_reviewer(requested, author):
    """Match a requested reviewer to a review author.

    GitHub records a Copilot request as "Copilot" but its reviews as
    "copilot-pull-request-reviewer".
    """
    if requested is None or author is None:
        return False
    requested, author = requested.lower(), author.lower()
    if requested == author:
        return True
    return requested == "copilot" and author.startswith("copilot")


def pr_state(repo, number, gh=run_gh, gh_paginated=run_gh_paginated):
    errors = []

    def part(name, read):
        try:
            return read()
        except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
            errors.append({"part": name, "error": str(error)})
            return None

    fields = "number,url,state,isDraft,mergeable,headRefOid,headRefName,baseRefName,reviewRequests,statusCheckRollup"
    required_pr_fields = ("number", "url", "state", "isDraft", "mergeable", "headRefOid", "headRefName", "baseRefName")
    try:
        pr = gh(["pr", "view", str(number), "--repo", repo, "--json", fields])
        response_type(pr, dict, "The PR response")
        missing = [field for field in required_pr_fields if field not in pr]
        if missing:
            raise ValueError(f"The PR response is missing {', '.join(missing)}.")
        response_integer(pr["number"], "The PR number")
        if pr["number"] == 0:
            raise ValueError("The PR number is zero.")
        response_type(pr["isDraft"], bool, "The PR draft flag")
        for name in ("url", "state", "mergeable", "headRefOid", "headRefName", "baseRefName"):
            response_string(pr[name], f"The PR {name}")
        for name in ("reviewRequests", "statusCheckRollup"):
            collection = pr[name]
            # A nullable GraphQL connection can have no check or request nodes.
            if collection is None:
                continue
            response_type(collection, list, f"The PR {name}")
            for item in collection:
                response_type(item, dict, f"A PR {name} entry")
        for request in pr["reviewRequests"] or []:
            for name in ("login", "slug", "name"):
                if name in request:
                    response_string(request[name], f"A requested reviewer's {name}", nullable=True)
            response_string(request.get("login") or request.get("slug") or request.get("name"), "A requested reviewer")
        for item in pr["statusCheckRollup"] or []:
            kind = response_string(item.get("__typename"), "A check type")
            if kind == "StatusContext":
                response_string(item.get("context"), "A status context")
                response_string(item.get("state"), "A status context state")
            elif kind == "CheckRun":
                response_string(item.get("name"), "A check name")
                response_string(item.get("status"), "A check status")
                # gh exports an unset conclusion as an empty Go string.
                response_string(item.get("conclusion"), "A check conclusion", nullable=True, empty=item["status"] != "COMPLETED")
            else:
                raise ValueError(f"Unknown check type: {kind}.")
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        return {"repo": repo, "number": number, "errors": [{"part": "pr", "error": str(error)}]}, 1

    head = pr["headRefOid"]
    base = pr["baseRefName"]

    def read_required():
        rules = gh_paginated(f"repos/{repo}/rules/branches/{base}")
        response_type(rules, list, "The branch rules")
        contexts = []
        for rule in rules:
            response_type(rule, dict, "A branch rule")
            kind = response_string(rule.get("type"), "A branch rule type")
            if kind != "required_status_checks":
                continue
            parameters = response_type(rule["parameters"], dict, "The required check parameters")
            entries = response_type(parameters["required_status_checks"], list, "The required checks")
            for check in entries:
                response_type(check, dict, "A required check")
                contexts.append(response_string(check["context"], "A required check context"))
        return sorted(contexts)

    required = part("required_checks", read_required)

    def read_behind():
        comparison = response_type(gh(["api", f"repos/{repo}/compare/{base}...{head}"]), dict, "The branch comparison")
        return response_integer(comparison["behind_by"], "The behind count")

    behind = part("base_behind_by", read_behind)

    checks = []
    for item in pr.get("statusCheckRollup") or []:
        name, state = check_state(item)
        checks.append({"name": name, "state": state, "required": None if required is None else name in required})
    for name in required or []:
        if not any(c["name"] == name for c in checks):
            checks.append({"name": name, "state": "missing", "required": True})

    def read_reviews():
        reviews = response_type(gh_paginated(f"repos/{repo}/pulls/{number}/reviews"), list, "The reviews")
        comments = response_type(gh_paginated(f"repos/{repo}/pulls/{number}/comments"), list, "The review comments")
        counts = {}
        for comment in comments:
            response_type(comment, dict, "A review comment")
            review_id = comment.get("pull_request_review_id")
            if review_id is not None:
                response_integer(review_id, "A comment review id")
            counts[review_id] = counts.get(review_id, 0) + 1
        for review in reviews:
            response_type(review, dict, "A review")
            response_integer(review["id"], "A review id")
            user = review["user"]
            if user is not None:
                response_type(user, dict, "A review user")
                response_string(user["login"], "A review author")
            response_string(review["state"], "A review state")
            for name in ("submitted_at", "commit_id", "body"):
                response_string(review.get(name), f"A review {name}", nullable=True, empty=name == "body")
        return [
            {
                "id": review["id"],
                "author": review["user"]["login"] if review["user"] is not None else None,
                "state": review["state"],
                "submitted_at": review.get("submitted_at"),
                "commit": review.get("commit_id"),
                "covers_head": review.get("commit_id") == head,
                "inline_comments": counts.get(review["id"], 0),
                "body": review.get("body") or "",
            }
            for review in reviews
        ]

    reviews = part("reviews", read_reviews)

    def read_comments():
        items = response_type(gh_paginated(f"repos/{repo}/issues/{number}/comments"), list, "The top-level comments")
        comments = []
        for item in items:
            response_type(item, dict, "A top-level comment")
            response_integer(item["id"], "A comment id")
            user = item.get("user")
            if user is not None:
                response_type(user, dict, "A comment user")
                response_string(user["login"], "A comment author")
            for name in ("created_at", "html_url"):
                response_string(item.get(name), f"A comment {name}", nullable=True)
            response_string(item.get("body"), "A comment body", nullable=True, empty=True)
            comments.append({
                "id": item["id"],
                "author": user["login"] if user is not None else None,
                "created_at": item.get("created_at"),
                "url": item.get("html_url"),
                "body": item.get("body") or "",
            })
        return comments

    comments = part("comments", read_comments)

    def read_requests():
        events = response_type(gh_paginated(f"repos/{repo}/issues/{number}/timeline"), list, "The timeline events")
        requests = []
        for event in events:
            response_type(event, dict, "A timeline event")
            kind = response_string(event.get("event"), "A timeline event type")
            if kind not in ("review_requested", "review_request_removed"):
                continue
            for name, key in (("requested_reviewer", "login"), ("requested_team", "slug"), ("actor", "login")):
                person = event.get(name)
                if person is not None:
                    response_type(person, dict, f"A timeline {name}")
                    response_string(person.get(key), f"A timeline {name} {key}")
            reviewer = (event.get("requested_reviewer") or {}).get("login") or (event.get("requested_team") or {}).get("slug")
            response_string(reviewer, "A review request recipient")
            response_string(event.get("created_at"), "A review request time")
            requests.append({
                "event": event["event"],
                "reviewer": reviewer,
                "requested_at": event.get("created_at"),
                "actor": (event.get("actor") or {}).get("login"),
            })
        return requests

    request_events = part("review_request_events", read_requests)

    latest_requests = None
    if request_events is not None:
        latest = {}
        for event in request_events:
            if event["event"] == "review_requested":
                latest[event["reviewer"]] = event
            else:
                latest.pop(event["reviewer"], None)
        latest_requests = []
        for reviewer, event in sorted(latest.items()):
            answered = None
            if reviews is not None:
                answered = any(
                    same_reviewer(reviewer, r["author"]) and (r["submitted_at"] or "") >= event["requested_at"]
                    for r in reviews
                )
            latest_requests.append({"reviewer": reviewer, "requested_at": event["requested_at"], "answered": answered})

    result = {
        "repo": repo,
        "number": pr["number"],
        "url": pr["url"],
        "state": pr["state"],
        "is_draft": pr["isDraft"],
        "mergeable": pr["mergeable"],
        "head": head,
        "head_branch": pr["headRefName"],
        "base": base,
        "base_behind_by": behind,
        "ci": summarize_ci(checks, required),
        "checks": checks,
        "required_checks": required,
        "pending_review_requests": [r.get("login") or r.get("slug") or r.get("name") for r in pr.get("reviewRequests") or []],
        "latest_review_requests": latest_requests,
        "review_request_events": request_events,
        "reviews": reviews,
        "comments": comments,
        "errors": errors,
    }
    return result, 2 if errors else 0


def verify_commit(repo, rev, subject=None, on=None, pr_head=None, gh=run_gh):
    """Resolve a published commit and compare it with what the caller expects it to be."""
    errors = []
    expectations = {}
    try:
        commit = gh(["api", f"repos/{repo}/commits/{rev}"])
        if not isinstance(commit, dict):
            raise ValueError("The commit response is not an object.")
        if "sha" not in commit:
            raise ValueError("The commit response is missing its sha.")
        body = commit["commit"]
        if not isinstance(body, dict):
            raise ValueError("The commit body is not an object.")
        if "message" not in body:
            raise ValueError("The commit response is missing its message.")
        if "author" not in body:
            raise ValueError("The commit response is missing its author.")
        author = body["author"]
        author_date = None
        if author is not None:
            response_type(author, dict, "The commit author")
            author_date = response_string(author.get("date"), "The commit author date", nullable=True)
        sha = response_string(commit["sha"], "The commit sha")
        message = body["message"]
        if not isinstance(message, str):
            raise ValueError("The commit message is not a string.")
        parents = commit.get("parents")
        if parents is None:
            parents = []
        elif not isinstance(parents, list):
            raise ValueError("The commit parents are not a list.")
        for parent in parents:
            if not isinstance(parent, dict) or "sha" not in parent:
                raise ValueError("A commit parent is missing its sha.")
            response_string(parent["sha"], "A commit parent sha")
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        result = {"repo": repo, "rev": rev, "errors": [{"part": "commit", "error": str(error)}]}
        if "No commit found" in str(error):
            result["note"] = "GitHub gives this error for an unpushed or missing commit and for an ambiguous or too-short prefix. Check that the commit is pushed, then retry with the full SHA."
        return result, 1

    result = {
         "repo": repo,
         "rev": rev,
         "sha": sha,
         "subject": message.splitlines()[0] if message else "",
         "author_date": author_date,
         "parents": [parent["sha"] for parent in parents],
         "expectations": expectations,
         "errors": errors,
     }

    if subject is not None:
        expectations["subject_matches"] = result["subject"] == subject.strip()

    if on is not None:
        try:
            # "behind" or "identical" means the commit is in the branch's history.
            comparison = response_type(gh(["api", f"repos/{repo}/compare/{on}...{sha}", "--jq", "{status}"]), dict, "The branch comparison")
            status = response_string(comparison["status"], "The branch comparison status")
            if status not in ("behind", "identical", "ahead", "diverged"):
                raise ValueError(f"Unknown branch comparison status: {status}.")
            expectations["on_branch"] = status in ("behind", "identical")
        except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
            errors.append({"part": "on_branch", "error": str(error)})
            expectations["on_branch"] = None

    if pr_head is not None:
        pr_repo, number = pr_head
        try:
            pr = response_type(gh(["pr", "view", str(number), "--repo", pr_repo, "--json", "headRefOid"]), dict, "The PR head response")
            head = response_string(pr["headRefOid"], "The PR head")
            result["pr_head"] = head
            expectations["is_pr_head"] = head == sha
        except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
            errors.append({"part": "is_pr_head", "error": str(error)})
            expectations["is_pr_head"] = None

    if False in expectations.values():
        return result, 3
    return result, 2 if errors else 0


ISSUE_ITEMS_QUERY = """
query($owner: String!, $name: String!, $number: Int!, $page: String) {
  repository(owner: $owner, name: $name) {
    issue(number: $number) {
      url
      projectItems(first: 50, after: $page) {
        pageInfo { hasNextPage endCursor }
        nodes {
          id
          project { id }
          fieldValueByName(name: "Status") { ... on ProjectV2ItemFieldSingleSelectValue { name } }
        }
      }
    }
  }
}
"""


READBACK_ATTEMPTS = 4
READBACK_DELAY_SECONDS = 2


def board_set_status(repo, number, owner, project, status, allow_backward=False, gh=run_gh, sleep=time.sleep):
    """Move one issue to a status on one board, refusing backward moves and stale transitions, and read the result back."""
    result = {"issue": f"{repo}#{number}", "project": f"{owner}/{project}", "requested": status,
              "facts": [], "added": False, "errors": []}

    def fail(part, error):
        result["errors"].append({"part": part, "error": str(error)})
        return result, 1

    def fact(step, state):
        result["facts"].append({"step": step, "state": state})

    def read_item():
        """Return (issue_url, item, incomplete).

        item is None only when its absence is proven. Read every membership page: a
        read that stops because a page claims a next page but gives no cursor returns
        incomplete=True, so a partial read is never treated as an absent item and
        used to add one on an assumed absence.
        """
        repo_owner, name = repo.split("/")
        url = None
        node = None
        cursor = None
        incomplete = False
        while True:
            args = ["api", "graphql", "-f", f"query={ISSUE_ITEMS_QUERY}", "-f", f"owner={repo_owner}", "-f", f"name={name}", "-F", f"number={number}"]
            if cursor:
                args += ["--raw-field", f"page={cursor}"]
            data = response_type(gh(args), dict, "The issue response")
            data = response_type(data["data"], dict, "The issue data")
            repository = response_type(data["repository"], dict, "The issue repository")
            issue = response_type(repository["issue"], dict, "The issue")
            issue_url = response_string(issue["url"], "The issue URL")
            if url is None:
                url = issue_url
            items = response_type(issue["projectItems"], dict, "The issue project items")
            info = items.get("pageInfo")
            for node_item in response_type(items["nodes"], list, "The project item nodes"):
                response_type(node_item, dict, "A project item")
                item_project = response_type(node_item["project"], dict, "A project item project")
                item_project_id = response_string(item_project["id"], "A project item project id")
                item_id = response_string(node_item["id"], "A project item id")
                if item_project_id == project_id:
                    value = node_item.get("fieldValueByName")
                    item_status = None
                    if value is not None:
                        response_type(value, dict, "A project item Status value")
                        item_status = response_string(value.get("name"), "A project item Status name", nullable=True)
                    node = (item_id, item_status)
            if not isinstance(info, dict):
                incomplete = True
                break
            has_next = info.get("hasNextPage")
            if not isinstance(has_next, bool):
                incomplete = True
                break
            if not has_next:
                break
            cursor = info.get("endCursor")
            if not isinstance(cursor, str) or not cursor:
                incomplete = True
                break
        return url, node, incomplete

    try:
        board = response_type(gh(["project", "view", str(project), "--owner", owner, "--format", "json"]), dict, "The project response")
        project_id = response_string(board["id"], "The project id")
        field_list = response_type(gh(["project", "field-list", str(project), "--owner", owner, "--format", "json"]), dict, "The project field response")
        fields = response_type(field_list["fields"], list, "The project fields")
        for entry in fields:
            response_type(entry, dict, "A project field")
            response_string(entry["name"], "A project field name")
        field = next(f for f in fields if f["name"] == "Status")
        response_string(field["id"], "The Status field id")
        if not isinstance(field.get("options"), list):
            raise ValueError("The Status field has no option list.")
        options = []
        for option in field["options"]:
            if not isinstance(option, dict) or not isinstance(option.get("name"), str):
                raise ValueError("A Status option is not a named string.")
            if "id" not in option:
                raise ValueError("A Status option is missing its id.")
            response_string(option["id"], "A Status option id")
            response_string(option["name"], "A Status option name")
            options.append(option["name"])
    except StopIteration:
        return fail("status_field", "The board has no Status field.")
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        return fail("board", error)

    result["options"] = options
    matches = [name for name in options if name == status] or [name for name in options if name.lower() == status.lower()]
    if len(matches) != 1:
        return fail("status", f"No single Status option matches {status!r}.")
    target = matches[0]
    result["target"] = target

    try:
        url, item, incomplete = read_item()
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        return fail("issue", error)
    result["before"] = item[1] if item else None
    result["membership_complete"] = not incomplete

    if item is None and incomplete:
        result.update(action="refused", after=result["before"], membership_complete=False)
        result["reason"] = "Membership could not be read in full, so absence is not proven. No item was added."
        return result, 1

    if item and item[1] == target:
        result.update(action="unchanged", after=target, readback_matches=True)
        fact("membership", "reused")
        fact("status", "already_at_target")
        return result, 0
    if item and item[1] in options and options.index(item[1]) > options.index(target) and not allow_backward:
        result.update(action="refused", after=item[1])
        result["reason"] = f"{item[1]} to {target} is a backward move. Pass --allow-backward only with a reason and authorization."
        fact("status", "refused")
        return result, 3

    # Re-read the live status just before the write. Another actor may have moved the
    # item between the first read and now; a stale request must not overwrite that
    # move. This narrows the race but cannot close it: a later remote write still
    # wins, and no local lock or repeated read makes the update atomic.
    try:
        _, live, live_incomplete = read_item()
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        return fail("recheck", error)
    if live_incomplete:
        result.update(action="refused", after=result["before"], membership_complete=False)
        result["reason"] = "The pre-write membership read was incomplete, so the live status is unconfirmed. No write was made."
        return result, 1
    live_status = live[1] if live else None
    if live != item:
        result.update(action="stale-refused", after=live_status)
        result["reason"] = f"Another actor moved the item from {result['before']} to {live_status} since it was first read. The write was refused to preserve that change."
        return result, 3
    result["recheck"] = live_status

    try:
        if live is None:
            added = response_type(gh(["project", "item-add", str(project), "--owner", owner, "--url", url, "--format", "json"]), dict, "The added item response")
            item_id = response_string(added["id"], "The added item id")
            result["added"] = True
            fact("membership", "completed")
        else:
            item_id = live[0]
            fact("membership", "reused")
    except IdentityError as error:
        result.update(action="refused", after=live_status)
        result["errors"].append({"part": "identity", "error": str(error)})
        fact("write", "refused")
        return result, 1
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
        result["errors"].append({"part": "add", "error": str(error)})
        fact("membership", "uncertain")
        return result, 1

    edit_failed = False
    option_id = next(option["id"] for option in field["options"] if option["name"] == target)
    try:
        gh(["project", "item-edit", "--id", item_id, "--project-id", project_id, "--field-id", field["id"],
              "--single-select-option-id", option_id, "--format", "json"])
        fact("status", "completed")
        result["action"] = "set"
    except IdentityError as error:
        result.update(action="refused", after=live_status)
        result["errors"].append({"part": "identity", "error": str(error)})
        fact("write", "refused")
        return result, 1
    except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
         # The edit reported a failure but the remote change may have taken hold,
         # so reconcile through a fresh read rather than the failed response.
        edit_failed = True
        result["errors"].append({"part": "write", "error": str(error)})
        fact("status", "uncertain")

    for attempt in range(1, READBACK_ATTEMPTS + 1):
        if attempt > 1:
            sleep(READBACK_DELAY_SECONDS)
        result["readback_attempts"] = attempt
        try:
            _, item, incomplete = read_item()
            result["after"] = item[1] if item else None
        except (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError) as error:
            result["errors"].append({"part": "readback", "error": str(error)})
            result["after"] = None
            break
        if incomplete:
            result["readback_incomplete"] = True
            break
        if result["after"] == target:
            break
    if result.get("readback_incomplete"):
        result["readback_matches"] = False
        return result, 2
    result["readback_matches"] = result["after"] == target

    if result["readback_matches"]:
        fact("readback", "confirmed")
        if edit_failed:
            result["action"] = "reconciled"
        return result, 0
    if edit_failed:
        fact("readback", "unknown" if result["after"] is None else "mismatch")
        return result, 1
    if result["after"] is None:
        fact("readback", "unknown")
        return result, 2
    fact("readback", "mismatch")
    result["action"] = "mismatch"
    return result, 2


def normalize_body(text):
    """Compare PR bodies without line-ending and trailing-whitespace differences that gh introduces."""
    return (text or "").replace("\r\n", "\n").rstrip()


def pr_ready(repo, number, body_file=None, expect_head=None, board=None, gh=run_gh, gh_text=run_gh_text,
             confirm=confirm_write_identity, board_write=board_set_status, state=pr_state):
    """Refresh a PR description, mark the draft ready, move its issue, and read each result back.

    ``board`` is ``(issue_repo, issue_number, owner, project, status)`` or ``None``.
    Nothing is written when the PR is not open, when ``expect_head`` does not match the
    current head, or when the write identity cannot be confirmed. Each write has its own
    read-back; a failed or mismatched read-back stops the sequence before the next write.
    """
    result = {"repo": repo, "number": number, "facts": [], "errors": []}

    def fact(step, outcome):
        result["facts"].append({"step": step, "state": outcome})

    def fail(part, error, status):
        result["errors"].append({"part": part, "error": str(error)})
        return result, status

    fields = "number,url,state,isDraft,headRefOid,headRefName,baseRefName,body"

    def read_pr():
        pr = gh(["pr", "view", str(number), "--repo", repo, "--json", fields])
        response_type(pr, dict, "The PR response")
        for name in ("url", "state", "headRefOid", "headRefName", "baseRefName"):
            response_string(pr[name], f"The PR {name}")
        response_type(pr["isDraft"], bool, "The PR draft flag")
        response_string(pr.get("body"), "The PR body", nullable=True, empty=True)
        return pr

    read_errors = (GhError, json.JSONDecodeError, TypeError, KeyError, ValueError)
    try:
        pr = read_pr()
    except read_errors as error:
        return fail("pr", error, 1)
    head = pr["headRefOid"]
    result.update({"url": pr["url"], "head_branch": pr["headRefName"], "base": pr["baseRefName"],
                   "before": {"state": pr["state"], "is_draft": pr["isDraft"], "head": head}})

    if pr["state"] != "OPEN":
        fact("write", "refused")
        return fail("state", f"The PR is {pr['state']}, not OPEN; nothing was written.", 3)
    if expect_head is not None:
        if len(expect_head) < 7 or not head.startswith(expect_head):
            fact("write", "refused")
            return fail("head", f"The PR head is {head}, not the expected {expect_head}; nothing was written.", 3)
        result["expected_head_matches"] = True

    body_text = None
    if body_file is not None:
        try:
            body_text = Path(body_file).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            fact("write", "refused")
            return fail("body_file", error, 1)

    try:
        confirm()
    except IdentityError as error:
        fact("write", "refused")
        return fail("identity", error, 1)

    if body_file is not None:
        write_failed = False
        try:
            gh_text(["pr", "edit", str(number), "--repo", repo, "--body-file", body_file])
        except GhError as error:
            write_failed = True
            result["errors"].append({"part": "description", "error": str(error)})
        try:
            after = read_pr()
        except read_errors as error:
            result["description_matches"] = None
            fact("description", "unknown")
            return fail("description_readback", error, 2)
        result["description_matches"] = normalize_body(after["body"]) == normalize_body(body_text)
        if not result["description_matches"]:
            fact("description", "mismatch")
            return result, 1 if write_failed else 2
        fact("description", "confirmed")
        if after["headRefOid"] != head:
            result["after"] = {"state": after["state"], "is_draft": after["isDraft"], "head": after["headRefOid"]}
            return fail("head", f"The PR head moved from {head} to {after['headRefOid']} during the description update; "
                                "the PR was not marked ready.", 2)

    if pr["isDraft"]:
        write_failed = False
        try:
            gh_text(["pr", "ready", str(number), "--repo", repo])
        except GhError as error:
            write_failed = True
            result["errors"].append({"part": "ready", "error": str(error)})
        try:
            after = read_pr()
        except read_errors as error:
            fact("ready", "unknown")
            return fail("ready_readback", error, 2)
        result["after"] = {"state": after["state"], "is_draft": after["isDraft"], "head": after["headRefOid"]}
        if after["isDraft"]:
            fact("ready", "mismatch")
            return result, 1 if write_failed else 2
        result["action"] = "reconciled" if write_failed else "ready"
        fact("ready", "confirmed")
        if after["headRefOid"] != head:
            return fail("head", f"The PR head moved from {head} to {after['headRefOid']}; the PR is ready at the new head, "
                                "which the review may not cover.", 2)
    else:
        result["action"] = "unchanged"
        result["after"] = {"state": pr["state"], "is_draft": False, "head": head}
        fact("ready", "unchanged")

    if board is not None:
        issue_repo, issue_number, owner, project, status = board
        board_result, board_status = board_write(issue_repo, issue_number, owner, project, status)
        result["board"] = board_result
        if board_status != 0:
            result["errors"].append({"part": "board", "error": f"board set-status exited {board_status}."})

    final, final_status = state(repo, number)
    result["pr_state"] = final
    if final_status == 1:
        result["errors"].append({"part": "pr_state", "error": "The final PR state could not be read."})
    elif final_status == 2:
        result["errors"].append({"part": "pr_state", "error": "Some parts of the final PR state could not be read."})
    return result, 2 if result["errors"] else 0

PROJECT_FACTS_PATH = Path(".ghflow") / "project.md"
INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md", ".github/copilot-instructions.md", "CONTRIBUTING.md")
PR_TEMPLATE_CANDIDATES = (".github/PULL_REQUEST_TEMPLATE.md", ".github/pull_request_template.md", "PULL_REQUEST_TEMPLATE.md")


def run_git(args, cwd):
    """Run a read-only git command and return its stdout text."""
    result = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise GhError((result.stderr or result.stdout).strip() or f"git exited {result.returncode}")
    return result.stdout


def parse_remote(url):
    """Return OWNER/NAME from a GitHub remote URL, or None."""
    match = re.search(r"github\.com[:/]([^/\s]+)/([^/\s]+?)(?:\.git)?/?$", url.strip())
    return f"{match.group(1)}/{match.group(2)}" if match else None


def parse_facts_sources(text):
    """Return (written, [(path, blob_hash)]) from a project facts file's frontmatter."""
    if not text.startswith("---\n"):
        return None, []
    end = text.find("\n---", 4)
    if end < 0:
        return None, []
    written = None
    sources = []
    in_sources = False
    for line in text[4:end].splitlines():
        if line.startswith("written:"):
            written = line.split(":", 1)[1].strip() or None
            in_sources = False
        elif line.strip() == "sources:":
            in_sources = True
        elif in_sources and line.lstrip().startswith("- "):
            parts = line.lstrip()[2:].split()
            if len(parts) == 2:
                sources.append((parts[0], parts[1]))
        elif line and not line.startswith(" "):
            in_sources = False
    return written, sources


def project_facts(cwd=None, issue=None, gh=run_gh, git=run_git, gh_paginated=run_gh_paginated, identity=None):
    """Report the live, deterministic facts about a checkout that a task handoff would otherwise restate.

    Reads only. ``issue`` is ``(repo, number)`` or ``None``. Each part that could not be read
    is ``null`` with an entry in ``errors``; exit 2 when any part failed.
    """
    errors = []
    read_errors = (GhError, OSError, json.JSONDecodeError, TypeError, KeyError, ValueError, IndexError)

    def part(name, read):
        try:
            return read()
        except read_errors as error:
            errors.append({"part": name, "error": str(error)})
            return None

    start = Path.cwd() if cwd is None else Path(cwd)
    try:
        root = Path(git(["rev-parse", "--show-toplevel"], start).strip()).resolve()
    except read_errors as error:
        return {"checkout": None, "errors": [{"part": "checkout", "error": str(error)}]}, 1

    def read_checkout():
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], root).strip()
        head = git(["rev-parse", "HEAD"], root).strip()
        worktrees = []
        current = {}
        for block in git(["worktree", "list", "--porcelain"], root).strip().split("\n\n"):
            if not block.strip():
                continue
            current = {}
            for line in block.splitlines():
                key, _, value = line.partition(" ")
                current[key] = value
            worktrees.append({"path": current.get("worktree"), "head": current.get("HEAD"),
                              "branch": current.get("branch", "").removeprefix("refs/heads/") or None,
                              "bare": "bare" in current})
        primary = next((w["path"] for w in worktrees if not w["bare"]), str(root))
        dirty = bool(git(["status", "--porcelain"], root).strip())
        return {"root": str(root), "primary_root": primary, "is_linked_worktree": str(root) != primary,
                "branch": branch, "head": head, "dirty": dirty, "worktrees": worktrees}

    checkout = part("checkout", read_checkout)

    def read_repository():
        url = git(["remote", "get-url", "origin"], root).strip()
        remote = parse_remote(url)
        default = None
        try:
            default = git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], root).strip().removeprefix("origin/")
        except GhError:
            if remote:
                data = gh(["api", f"repos/{remote}"])
                default = response_string(response_type(data, dict, "The repository response")["default_branch"], "The default branch")
        info = {"remote": remote, "remote_url": url, "default_branch": default}
        if default:
            origin_head = git(["rev-parse", f"origin/{default}"], root).strip()
            info["origin_default_head"] = origin_head
            try:
                local_head = git(["rev-parse", "--verify", f"refs/heads/{default}"], root).strip()
                counts = git(["rev-list", "--left-right", "--count", f"refs/heads/{default}...origin/{default}"], root).split()
                info.update({"local_default_head": local_head, "local_default_ahead": int(counts[0]), "local_default_behind": int(counts[1])})
            except GhError:
                info.update({"local_default_head": None, "local_default_ahead": None, "local_default_behind": None})
            info["recent_subjects"] = git(["log", "--format=%s", "-5", f"origin/{default}"], root).strip().splitlines()
        fetch_head = Path(git(["rev-parse", "--git-common-dir"], root).strip())
        if not fetch_head.is_absolute():
            fetch_head = root / fetch_head
        fetch_head = fetch_head / "FETCH_HEAD"
        info["fetch_head_age_seconds"] = int(time.time() - fetch_head.stat().st_mtime) if fetch_head.exists() else None
        return info

    repository = part("repository", read_repository)

    def read_project_files():
        tracked = set(git(["ls-files", "-z"], root).split("\0"))
        tracked.discard("")
        instructions = [name for name in INSTRUCTION_FILES if name in tracked]
        make_targets = []
        if "Makefile" in tracked:
            for line in (root / "Makefile").read_text(encoding="utf-8", errors="replace").splitlines():
                match = re.match(r"^([A-Za-z0-9_][A-Za-z0-9_.-]*)\s*:(?!=)", line)
                if match and not match.group(1).startswith("."):
                    make_targets.append(match.group(1))
        return {
            "instructions": instructions,
            "make_targets": make_targets,
            "python_project": "pyproject.toml" in tracked,
            "node_project": "package.json" in tracked,
            "conftest_paths": sorted(path for path in tracked if path == "conftest.py" or path.endswith("/conftest.py")),
            "ci_workflows": sorted(path for path in tracked if path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))),
            "pr_template": next((name for name in PR_TEMPLATE_CANDIDATES if name in tracked), None),
            "env_example": next((name for name in (".env.example", ".env.sample", "env.example") if name in tracked), None),
            "lockfiles": sorted(path for path in tracked if path in ("uv.lock", "poetry.lock", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "Cargo.lock", "go.sum")),
        }

    project_files = part("project_files", read_project_files)

    def read_facts_file():
        path = root / PROJECT_FACTS_PATH
        if not path.exists():
            return {"path": str(PROJECT_FACTS_PATH), "present": False}
        text = path.read_text(encoding="utf-8")
        written, sources = parse_facts_sources(text)
        stale = []
        for source, recorded in sources:
            source_path = root / source
            if not source_path.exists():
                stale.append({"path": source, "reason": "missing"})
                continue
            current = git(["hash-object", "--", source], root).strip()
            if current != recorded:
                stale.append({"path": source, "reason": "changed", "recorded": recorded, "current": current})
        return {"path": str(PROJECT_FACTS_PATH), "present": True, "written": written, "sources": len(sources),
                "stale_sources": stale, "lines": len(text.splitlines())}

    facts_file = part("project_facts", read_facts_file)

    def read_identity():
        config = identity if identity is not None else resolve_identity()
        return {key: config.get(key) for key in ("login", "configured", "ready", "source")}

    identity_facts = part("identity", read_identity)

    required_checks = None
    if repository and repository.get("remote") and repository.get("default_branch"):
        def read_required():
            rules = gh_paginated(f"repos/{repository['remote']}/rules/branches/{repository['default_branch']}")
            response_type(rules, list, "The branch rules")
            contexts = []
            for rule in rules:
                response_type(rule, dict, "A branch rule")
                if rule.get("type") != "required_status_checks":
                    continue
                for check in response_type(response_type(rule["parameters"], dict, "The rule parameters")["required_status_checks"], list, "The required checks"):
                    contexts.append(response_string(response_type(check, dict, "A required check")["context"], "A required check context"))
            return sorted(contexts)
        required_checks = part("required_checks", read_required)

    issue_facts = None
    if issue is not None:
        issue_repo, number = issue

        def read_issue():
            data = gh(["issue", "view", str(number), "--repo", issue_repo, "--json", "url,title,state,labels,projectItems"])
            response_type(data, dict, "The issue response")
            items = []
            for item in response_type(data.get("projectItems") or [], list, "The issue project items"):
                response_type(item, dict, "A project item")
                status = item.get("status")
                items.append({"project": item.get("title"), "status": status.get("name") if isinstance(status, dict) else None})
            return {"url": response_string(data["url"], "The issue url"), "title": data.get("title"), "state": data.get("state"),
                    "labels": [label.get("name") for label in data.get("labels") or [] if isinstance(label, dict)],
                    "board_items": items}

        issue_facts = part("issue", read_issue) or {}
        pattern = str(number)

        def read_branches():
            names = git(["for-each-ref", "--format=%(refname:short)", "refs/heads/", "refs/remotes/origin/"], root).split()
            return sorted(name for name in names if re.search(rf"(^|[^0-9]){re.escape(pattern)}([^0-9]|$)", name))

        issue_facts["branches"] = part("issue_branches", read_branches)
        if checkout:
            issue_facts["worktrees"] = [w["path"] for w in checkout["worktrees"]
                                        if w.get("branch") and re.search(rf"(^|[^0-9]){re.escape(pattern)}([^0-9]|$)", w["branch"])]

        def read_prs():
            prs = gh(["pr", "list", "--repo", issue_repo, "--state", "all", "--search", f"{number} in:title,body", "--json",
                      "number,url,state,isDraft,headRefName,headRefOid,title"])
            response_type(prs, list, "The PR list")
            return [{"number": pr.get("number"), "url": pr.get("url"), "state": pr.get("state"), "is_draft": pr.get("isDraft"),
                     "head_branch": pr.get("headRefName"), "head": pr.get("headRefOid"), "title": pr.get("title")}
                    for pr in prs if isinstance(pr, dict)]

        issue_facts["prs"] = part("issue_prs", read_prs)

    result = {"checkout": checkout, "repository": repository, "project_files": project_files, "project_facts": facts_file,
              "identity": identity_facts, "required_checks": required_checks, "issue": issue_facts, "errors": errors}
    return result, 2 if errors else 0


def identity_config_paths(cwd=None):
    """Return identity config paths in project, primary-checkout, then home order."""
    current = Path.cwd() if cwd is None else Path(cwd)
    current = current.resolve()
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], cwd=current,
        capture_output=True, check=False,
    )
    if result.returncode != 0:
        return [current / ".ghflow" / "identity.json", Path.home() / ".config" / "ghflow" / "identity.json"]

    worktree_root_text = os.fsdecode(result.stdout.removesuffix(b"\n"))
    worktree_root = Path(worktree_root_text).resolve()
    primary_root = worktree_root
    worktrees = subprocess.run(
        ["git", "worktree", "list", "--porcelain", "-z"], cwd=worktree_root,
        capture_output=True, check=False,
    )
    if worktrees.returncode == 0:
        for block in worktrees.stdout.split(b"\0\0"):
            fields = block.split(b"\0")
            worktree_field = next((field for field in fields if field.startswith(b"worktree ")), None)
            if worktree_field and b"bare" not in fields:
                primary_path = os.fsdecode(worktree_field.removeprefix(b"worktree "))
                primary_root = Path(primary_path).resolve()
                break

    paths = [worktree_root / ".ghflow" / "identity.json"]
    primary_config = primary_root / ".ghflow" / "identity.json"
    if primary_config != paths[0]:
        paths.append(primary_config)
    paths.append(Path.home() / ".config" / "ghflow" / "identity.json")
    return paths


def resolve_identity(env=None, config_paths=None):
    """Resolve agent identity from explicit environment values and the selected config."""
    if env is None:
        env = os.environ
    if config_paths is None:
        config_paths = identity_config_paths()

    config_data = {}
    config_source = None
    for p in config_paths:
        expanded = Path(p).expanduser()
        config_source = str(expanded.resolve())
        try:
            with open(expanded, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except FileNotFoundError:
            config_source = None
            continue
        except (OSError, UnicodeError) as error:
            raise IdentityError(f"Cannot read identity configuration at {config_source}: {error}") from None
        except json.JSONDecodeError as error:
            raise IdentityError(f"Invalid identity configuration at {config_source}: {error}") from None
        if not isinstance(config_data, dict):
            raise IdentityError(f"Invalid identity configuration at {config_source}: expected a JSON object.")
        break

    login = env.get("GHFLOW_IDENTITY_LOGIN") or env.get("GHFLOW_LOGIN") or config_data.get("login")
    name = env.get("GHFLOW_IDENTITY_NAME") or env.get("GHFLOW_NAME") or config_data.get("name") or login
    email = env.get("GHFLOW_IDENTITY_EMAIL") or env.get("GHFLOW_EMAIL") or config_data.get("email")
    token_file = env.get("GHFLOW_TOKEN_FILE") or env.get("GHFLOW_IDENTITY_TOKEN_FILE") or config_data.get("token_file")

    token_path = None
    token_present = False
    if token_file:
        token_path = Path(token_file).expanduser()
        try:
            token_present = bool(token_path.read_text(encoding="utf-8").strip())
        except (OSError, UnicodeError):
            token_present = False
    elif "GH_TOKEN" in env:
        token_present = bool(env["GH_TOKEN"].strip())

    environment_source = any(env.get(key) for key in (
        "GHFLOW_IDENTITY_LOGIN", "GHFLOW_LOGIN", "GHFLOW_IDENTITY_NAME", "GHFLOW_NAME",
        "GHFLOW_IDENTITY_EMAIL", "GHFLOW_EMAIL", "GHFLOW_TOKEN_FILE",
        "GHFLOW_IDENTITY_TOKEN_FILE",
    ))
    configured = bool(login or token_path or "GH_TOKEN" in env)
    return {
        "login": login,
        "name": name,
        "email": email,
        "token_file": str(token_path) if token_path else None,
        "token_present": token_present,
        "configured": configured,
        "ready": bool(login and token_present),
        "source": "environment" if environment_source else config_source,
    }


def identity_env(identity, base_env=None):
    """Build environment dict with GH_TOKEN, Git author/committer, and credential config."""
    env = dict(os.environ if base_env is None else base_env)
    env.pop("GITHUB_TOKEN", None)
    token_file = identity.get("token_file")
    if token_file:
        p = Path(token_file).expanduser()
        try:
            token = p.read_text(encoding="utf-8").strip()
        except (OSError, UnicodeError):
            raise GhError("The selected token file is unavailable.") from None
        if not token:
            raise GhError("The selected token file is empty.")
        env["GH_TOKEN"] = token

    name = identity.get("name")
    if name:
        env["GIT_AUTHOR_NAME"] = name
        env["GIT_COMMITTER_NAME"] = name

    email = identity.get("email")
    if email:
        env["GIT_AUTHOR_EMAIL"] = email
        env["GIT_COMMITTER_EMAIL"] = email

    if token_file or "GH_TOKEN" in env:
        inherited_config = env.get("GIT_CONFIG_PARAMETERS", "").strip()
        try:
            parameters = git_config_parameter_tokens(inherited_config) if inherited_config else []
        except ValueError:
            raise GhError("Inherited Git configuration parameters could not be read.") from None
        helper_key = "credential.https://github.com.helper"
        kept_parameters = []
        try:
            for parameter in parameters:
                decoded = shlex.split(parameter)
                key = decoded[0].partition("=")[0]
                if key.casefold() != helper_key.casefold():
                    kept_parameters.append(parameter)
        except (IndexError, ValueError):
            raise GhError("Inherited Git configuration parameters could not be read.") from None
        kept_parameters.extend((f"'{helper_key}='", f"'{helper_key}=!gh auth git-credential'"))
        env["GIT_CONFIG_PARAMETERS"] = " ".join(kept_parameters)

    return env


def main(argv=None):
    parser = argparse.ArgumentParser(prog="ghflow", description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    state = commands.add_parser("pr-state", help="Report CI, review requests, and reviews for a PR's current head.")
    state.add_argument("pr", help="PR URL, or PR number with --repo")
    state.add_argument("--repo", help="OWNER/NAME when giving a PR number")
    verify = commands.add_parser("verify-commit", help="Resolve a published commit and check that it is the one you expect.")
    verify.add_argument("rev", help="commit SHA or prefix")
    verify.add_argument("--repo", required=True, help="OWNER/NAME")
    verify.add_argument("--subject", help="expected first line of the commit message")
    verify.add_argument("--on", metavar="BRANCH", help="branch whose history should contain the commit")
    verify.add_argument("--pr-head", metavar="PR", help="PR URL or number whose current head should be the commit")
    board = commands.add_parser("board", help="Project board operations.")
    board_commands = board.add_subparsers(dest="board_command", required=True)
    set_status = board_commands.add_parser("set-status", help="Move one issue to a board status, refusing backward moves, and read it back.")
    set_status.add_argument("issue", help="issue URL, or issue number with --repo")
    set_status.add_argument("--repo", help="OWNER/NAME when giving an issue number")
    set_status.add_argument("--owner", required=True, help="login that owns the project board")
    set_status.add_argument("--project", required=True, type=int, help="project board number")
    set_status.add_argument("--status", required=True, help="target Status option name")
    set_status.add_argument("--allow-backward", action="store_true", help="permit a backward move; use only with a reason and authorization")
    pr_group = commands.add_parser("pr", help="PR write operations with read-backs.")
    pr_commands = pr_group.add_subparsers(dest="pr_command", required=True)
    ready = pr_commands.add_parser("ready", help="Refresh the description, mark a draft ready, move its issue In review, and read each back.")
    ready.add_argument("pr", help="PR URL, or PR number with --repo")
    ready.add_argument("--repo", help="OWNER/NAME when giving a PR number")
    ready.add_argument("--body-file", metavar="FILE", help="UTF-8 file with the final description; omit to keep the current body")
    ready.add_argument("--expect-head", metavar="SHA", help="refuse to write unless the current head is this reviewed commit")
    ready.add_argument("--issue", help="issue URL to move on the board; needs --owner and --project")
    ready.add_argument("--owner", help="login that owns the project board")
    ready.add_argument("--project", type=int, help="project board number")
    ready.add_argument("--status", default="In review", help='target Status option name (default "In review")')

    facts = commands.add_parser("facts", help="Report live checkout, repository, tooling, identity, and issue facts for a handoff; reads only.")
    facts.add_argument("--issue", help="issue URL, or issue number with --repo, to include its branches, worktrees, PRs, and board items")
    facts.add_argument("--repo", help="OWNER/NAME when giving an issue number")
    ident = commands.add_parser("identity", help="Report or export the configured agent identity.")
    ident.add_argument("--export", action="store_true", help="output shell export statements")
    exec_cmd = commands.add_parser("exec", help="Run a command under the configured agent identity.")
    exec_cmd.add_argument("exec_args", nargs=argparse.REMAINDER, help="command and arguments to run")
    args = parser.parse_args(argv)

    if args.command == "pr-state":
        repo, number = parse_pr(args.pr, args.repo)
        result, status = pr_state(repo, number)
    elif args.command == "verify-commit":
        pr_head = parse_pr(args.pr_head, args.repo) if args.pr_head else None
        result, status = verify_commit(args.repo, args.rev, args.subject, args.on, pr_head)
    elif args.command == "board":
        repo, number = parse_issue(args.issue, args.repo)
        result, status = board_set_status(repo, number, args.owner, args.project, args.status, args.allow_backward)
    elif args.command == "pr":
        repo, number = parse_pr(args.pr, args.repo)
        board = None
        if args.issue or args.owner or args.project is not None:
            if not (args.issue and args.owner and args.project is not None):
                parser.error("--issue, --owner, and --project are required together for a board move.")
            issue_repo, issue_number = parse_issue(args.issue, repo)
            board = (issue_repo, issue_number, args.owner, args.project, args.status)
        result, status = pr_ready(repo, number, args.body_file, args.expect_head, board)

    elif args.command == "facts":
        issue = parse_issue(args.issue, args.repo) if args.issue else None
        result, status = project_facts(issue=issue)
    elif args.command == "identity":
        try:
            identity = resolve_identity()
        except GhError as error:
            sys.stderr.write(f"{error}\n")
            return 1
        if args.export:
            try:
                env = identity_env(identity)
            except GhError as error:
                sys.stderr.write(f"{error}\n")
                return 1
            statements = ["unset GITHUB_TOKEN"]
            if "GH_TOKEN" in env:
                statements.append(f'export GH_TOKEN={shlex.quote(env["GH_TOKEN"])}')
            if "GIT_AUTHOR_NAME" in env:
                statements.append(f'export GIT_AUTHOR_NAME={shlex.quote(env["GIT_AUTHOR_NAME"])}')
            if "GIT_COMMITTER_NAME" in env:
                statements.append(f'export GIT_COMMITTER_NAME={shlex.quote(env["GIT_COMMITTER_NAME"])}')
            if "GIT_AUTHOR_EMAIL" in env:
                statements.append(f'export GIT_AUTHOR_EMAIL={shlex.quote(env["GIT_AUTHOR_EMAIL"])}')
            if "GIT_COMMITTER_EMAIL" in env:
                statements.append(f'export GIT_COMMITTER_EMAIL={shlex.quote(env["GIT_COMMITTER_EMAIL"])}')
            if "GIT_CONFIG_PARAMETERS" in env:
                statements.append(f'export GIT_CONFIG_PARAMETERS={shlex.quote(env["GIT_CONFIG_PARAMETERS"])}')
            sys.stdout.write("\n".join(statements) + ("\n" if statements else ""))
            return 0
        json.dump(identity, sys.stdout, indent=2)
        sys.stdout.write("\n")
        return 0 if identity["ready"] else 1
    elif args.command == "exec":
        cmd_args = args.exec_args
        if cmd_args and cmd_args[0] == "--":
            cmd_args = cmd_args[1:]
        if not cmd_args:
            sys.stderr.write("Give a command to run with exec.\n")
            return 1
        try:
            identity = resolve_identity()
            env = identity_env(identity)
        except GhError as error:
            sys.stderr.write(f"{error}\n")
            return 1
        if is_git_commit_command(cmd_args) and (not identity.get("name") or not identity.get("email")):
            sys.stderr.write("A selected Git author name and email are required before a commit.\n")
            return 1
        res = subprocess.run(cmd_args, env=env)
        return res.returncode
    else:
        return 1
    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return status


if __name__ == "__main__":
    sys.exit(main())
