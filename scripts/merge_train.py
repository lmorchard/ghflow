#!/usr/bin/env python3
"""Merge a PR batch, repairing conflicting PRs with the local model.

The CLI owns the deterministic train checks. The queue runner owns the model
repair. This coordinator runs the train, repairs each conflict in its worktree,
then runs the train again. It does not bypass a failed check or a review.

Set OPENCODE_CONFIG to the local-only overlay and GHFLOW_CLI to the skill's
cli/ghflow.py. The runner is invoked with --issue for each conflicting PR, so
the repair, review, and ready steps stay in the normal runner flow.
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "cli" / "ghflow.py"
RUNNER = ROOT / "scripts" / "run_queue.py"


def clean(value):
    value = (value or "").strip()
    if value in ("", "null"):
        return None
    if value.startswith('"') and value.endswith('"'):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value.strip('"')
    return value


def gh_text(args):
    proc = subprocess.run(["gh", *args], capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return clean(proc.stdout)


def parse_item(raw):
    if "=" in raw:
        return raw.rsplit("=", 1)
    return raw, None


def pr_number(ref):
    return str(ref).rstrip("/").split("/")[-1].split("#")[-1]


def pr_field(repo, number, field):
    return gh_text(["pr", "view", str(number), "--repo", repo, "--json", field,
                    "--jq", f".{field}"])


def pr_state(repo, number):
    return pr_field(repo, number, "state")


def pr_head(repo, number):
    return pr_field(repo, number, "headRefOid")


def pr_draft(repo, number):
    return (pr_field(repo, number, "isDraft") or "").lower() == "true"


def conflict_issue(repo, ref):
    number = pr_number(ref)
    return gh_text(["pr", "view", number, "--repo", repo, "--json",
                    "closingIssuesReferences", "--jq",
                    ".closingIssuesReferences[0].url"])


def refresh_items(repo, refs):
    items = []
    for ref in refs:
        pr, head = parse_item(ref)
        number = pr_number(pr)
        if pr_state(repo, number) != "OPEN":
            continue
        if pr_draft(repo, number):
            continue
        items.append(f"{pr}={head or pr_head(repo, number)}")
    return items


def run_train(args, items):
    cmd = [sys.executable, str(CLI), "pr", "merge-train", "--repo", args.repo,
           "--method", args.method, "--authorization", args.authorization,
           "--continue-on-conflict"]
    for item in items:
        cmd += ["--item", item]
    if args.owner and args.project:
        cmd += ["--owner", args.owner, "--project", str(args.project)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    try:
        result = json.loads(proc.stdout)
    except json.JSONDecodeError:
        result = {"raw": proc.stdout, "stderr": proc.stderr}
    return result, proc.returncode


def run_repair(args, issue_url):
    cmd = [sys.executable, str(RUNNER), "--issue", issue_url, "--once",
           "--model", args.model, "--review-model", args.review_model,
           "--hours", str(args.hours), "--floor", "30",
           "--step-idle-timeout", str(args.step_idle_timeout),
           "--session-timeout", str(args.session_timeout),
           "--context-warn-tokens", str(args.context_warn_tokens),
           "--skill-dir", str(ROOT)]
    if args.owner and args.project:
        cmd += ["--project", f"{args.owner}/{args.project}"]
    env = os.environ.copy()
    env["GHFLOW_CLI"] = str(CLI)
    print(f"[merge-train] repairing {issue_url}", flush=True)
    return subprocess.run(cmd, env=env).returncode


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run the merge train, repair conflicting PRs with the local runner, and rerun it.")
    parser.add_argument("--repo", required=True, help="OWNER/NAME for bare PR numbers")
    parser.add_argument("--method", required=True, choices=("merge", "squash", "rebase"))
    parser.add_argument("--authorization", required=True,
                        help="the user authorization that covers this batch")
    parser.add_argument("--item", action="append", required=True, metavar="PR[=HEAD]",
                        help="PR URL or number; repeat in merge order")
    parser.add_argument("--owner", help="project board owner for Done moves")
    parser.add_argument("--project", type=int, help="project board number for Done moves")
    parser.add_argument("--model", required=True, help="local implementation model")
    parser.add_argument("--review-model", required=True, help="local review model")
    parser.add_argument("--rounds", type=int, default=2,
                        help="train and repair rounds (default 2)")
    parser.add_argument("--hours", type=float, default=2.0,
                        help="runner budget per repair (default 2)")
    parser.add_argument("--step-idle-timeout", type=int, default=1800)
    parser.add_argument("--session-timeout", type=int, default=7200)
    parser.add_argument("--context-warn-tokens", type=int, default=100000)
    args = parser.parse_args(argv)

    if not os.environ.get("OPENCODE_CONFIG"):
        print("[merge-train] warning: OPENCODE_CONFIG is unset; the runner may use a cloud model.",
              file=sys.stderr)

    refs = list(args.item)
    for round_index in range(1, args.rounds + 1):
        items = refresh_items(args.repo, refs)
        if not items:
            print("[merge-train] no open, non-draft PRs remain.")
            break
        result, status = run_train(args, items)
        merged = result.get("merged") or []
        conflicts = result.get("conflicts") or []
        print(json.dumps({"round": round_index, "status": status,
                          "merged": merged, "conflicts": conflicts,
                          "stopped_at": result.get("stopped_at"),
                          "errors": result.get("errors")}, indent=2))
        if status == 0 or not conflicts:
            break
        repaired = 0
        for conflict in conflicts:
            issue = conflict_issue(args.repo, conflict.get("pr"))
            if not issue:
                print(f"[merge-train] no closing issue for {conflict.get('pr')}; cannot repair.")
                continue
            repair_status = run_repair(args, issue)
            if repair_status != 0:
                print(f"[merge-train] repair for {issue} exited {repair_status}.")
            else:
                repaired += 1
        if not repaired:
            print("[merge-train] no conflict repair completed; stopping.")
            break
    return 0


if __name__ == "__main__":
    sys.exit(main())
