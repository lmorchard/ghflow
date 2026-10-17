#!/usr/bin/env python3
"""A fake ``gh`` that records its arguments and returns controlled responses.

Place this file on ``PATH`` under the name ``gh`` and run ``ghflow.py`` as a
subprocess. It never reaches the network. It reads its fixtures and a log path
from the environment:

- ``GHHOW_LOG``: append one JSON object per invocation to this file so a test
  can verify the exact arguments sent to ``gh``.
- ``GHHOW_REPLIES``: a JSON object mapping a call key to its response. Each
  response is ``{"out": <json> | null, "code": <int>, "err": <str>, "raw": <str>}``.
  ``out`` is json-encoded to stdout; ``raw`` is printed verbatim (used to feed a
  malformed response). A key named ``_default`` answers any call that has no
  specific reply.
- ``GHHOW_BOARD``: a JSON file holding a small board model
  ``{"project_id", "options", "status", "on_board"}`` used to answer the
  ``project`` and ``graphql`` calls that ``board set-status`` makes. Writes to
  the model persist so a read-after-write reflects the write.

Call keys:
- ``pr view N --repo R`` is keyed ``pr.view:R:N``.
- ``api <path> --jq <expr>`` is keyed ``api.jq:<path>:<expr>``.
- ``api <path> --paginate --slurp`` is keyed ``api.paginate:<path>``.
- other ``api <path> ...`` is keyed ``api:<path>``.
"""

import json
import os
import sys


def flag(argv, name):
    """Return the token after ``name`` in ``argv``, or ``None``."""
    try:
        return argv[argv.index(name) + 1]
    except (ValueError, IndexError):
        return None


def record(log, argv):
    if log:
        with open(log, "a", encoding="utf-8") as out:
            out.write(json.dumps({"argv": argv}) + "\n")


def reply(replies, key, argv):
    entry = replies.get(key)
    if entry is None:
        entry = replies.get("_default")
    if entry is None:
        sys.stderr.write(f"fake gh: no reply for {key} (argv={argv})\n")
        sys.exit(1)
    if entry.get("raw") is not None:
        sys.stdout.write(entry["raw"])
        sys.exit(entry.get("code", 0))
    if entry.get("err"):
        sys.stderr.write(entry["err"])
    if entry.get("out") is not None:
        sys.stdout.write(json.dumps(entry["out"]))
    sys.exit(entry.get("code", 0))


def load_board(path):
    with open(path, "r", encoding="utf-8") as out:
        return json.load(out)


def save_board(path, board):
    with open(path, "w", encoding="utf-8") as out:
        json.dump(board, out)


def handle_board(argv, board, board_path):
    sub = argv[1]
    if sub == "view":
        sys.stdout.write(json.dumps({"id": board["project_id"]}))
    elif sub == "field-list":
        options = [{"id": f"opt-{i}", "name": name} for i, name in enumerate(board["options"])]
        fields = [{"id": "F0", "name": "Title"}, {"id": "F1", "name": "Status", "options": options}]
        sys.stdout.write(json.dumps({"fields": fields}))
    elif sub == "item-add":
        board["on_board"] = True
        save_board(board_path, board)
        sys.stdout.write(json.dumps({"id": "ITEM"}))
    elif sub == "item-edit":
        option_id = flag(argv, "--single-select-option-id")
        index = int(option_id.split("-")[1])
        board["status"] = board["options"][index]
        save_board(board_path, board)
        sys.stdout.write(json.dumps({}))
    else:
        sys.stderr.write(f"fake gh: unhandled project subcommand {sub}\n")
        sys.exit(1)


def handle_graphql(argv, board, board_path):
    owner = name = number = None
    for token in argv:
        if token.startswith("owner="):
            owner = token.split("=", 1)[1]
        elif token.startswith("name="):
            name = token.split("=", 1)[1]
        elif token.startswith("number="):
            number = token.split("=", 1)[1]
    nodes = []
    if board["on_board"]:
        value = {"name": board["status"]} if board["status"] else {}
        nodes.append({
                 "id": "ITEM",
                 "project": {"id": board["project_id"]},
                 "fieldValueByName": value,
           })
    result = {
        "data": {
            "repository": {
                "issue": {
                    "url": f"https://github.com/{owner}/{name}/issues/{number}",
                    "closedByPullRequestsReferences": {"nodes": board.get("linked_prs", [])},
                    "projectItems": {
                        "nodes": nodes,
                        "pageInfo": {"hasNextPage": False},
                    },
                },
            },
       },
    }
    sys.stdout.write(json.dumps(result))


def main():
    argv = sys.argv[1:]
    log = os.environ.get("GHHOW_LOG")
    record(log, argv)
    if not argv:
        sys.exit(1)

    cmd = argv[0]
    if cmd == "project" or (cmd == "api" and argv[1] == "graphql"):
        board_path = os.environ.get("GHHOW_BOARD")
        board = load_board(board_path)
        if cmd == "api":
            handle_graphql(argv, board, board_path)
        else:
            handle_board(argv, board, board_path)
        sys.exit(0)

    replies = {}
    replies_path = os.environ.get("GHHOW_REPLIES")
    if replies_path:
        with open(replies_path, "r", encoding="utf-8") as out:
            replies = json.load(out)

    if cmd == "pr":
        repo = flag(argv, "--repo")
        number = argv[2]
        reply(replies, f"pr.view:{repo}:{number}", argv)

    if cmd == "api":
        path = argv[1]
        rest = argv[2:]
        if "--jq" in rest:
            key = f"api.jq:{path}:{rest[rest.index('--jq') + 1]}"
        elif "--paginate" in rest and "--slurp" in rest:
            key = f"api.paginate:{path}"
        else:
            key = f"api:{path}"
        reply(replies, key, argv)

    sys.stderr.write(f"fake gh: unhandled command {argv[0]!r}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
