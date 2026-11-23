"""Run one real OpenCode session against a scripted model server.

This test skips when OpenCode is absent or older than 2.x. It is not part of
``make check`` because it needs the OpenCode binary; run it with
``make test-runner-integration``.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

CLI_DIR = Path(__file__).resolve().parent.parent / "cli"
if str(CLI_DIR) not in sys.path:
    sys.path.insert(0, str(CLI_DIR))

import run_queue  # noqa: E402
from fake_model import FakeModel, FakeModelServer  # noqa: E402
from session import parse_session_log  # noqa: E402

OPENCODE = shutil.which("opencode")


def opencode_major():
    if not OPENCODE:
        return 0
    try:
        result = subprocess.run([OPENCODE, "--version"], capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    text = (result.stdout or result.stderr or "").strip()
    match = re.search(r"(\d+)\.\d+", text)
    return int(match.group(1)) if match else 0


def config(endpoint):
    return {
        "model": "fake/fake-model",
        "small_model": "fake/fake-model",
        "enabled_providers": ["fake"],
        "share": "disabled",
        "autoupdate": False,
        "plugin": [],
        "mcp": {},
        "instructions": [],
        "lsp": False,
        "formatter": False,
        "permission": {"*": "allow"},
        "provider": {"fake": {
            "npm": "@ai-sdk/openai-compatible",
            "name": "Fake model",
            "options": {"baseURL": endpoint, "apiKey": "fake"},
            "models": {"fake-model": {"name": "fake-model",
                                      "limit": {"context": 32768, "output": 4096}}},
        }},
    }


class OpenCodeEnvironment:
    """Isolated OpenCode stores that point at a fake provider."""

    def __init__(self, root, endpoint):
        self.root = Path(root)
        self.env = {
            "OPENCODE_CONFIG_CONTENT": json.dumps(config(endpoint)),
            "OPENCODE_CONFIG_DIR": str(self.root / "config"),
            "XDG_CONFIG_HOME": str(self.root / "config"),
            "XDG_DATA_HOME": str(self.root / "data"),
            "XDG_CACHE_HOME": str(self.root / "cache"),
            "XDG_STATE_HOME": str(self.root / "state"),
            "OPENCODE_DISABLE_AUTOUPDATE": "true",
            "OPENCODE_DISABLE_CLAUDE_CODE": "true",
            "OPENCODE_DISABLE_DEFAULT_PLUGINS": "true",
            "OPENCODE_DISABLE_LSP_DOWNLOAD": "true",
            "OPENCODE_DISABLE_MODELS_FETCH": "true",
        }
        for key in ("OPENCODE_CONFIG_DIR", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
                    "XDG_CACHE_HOME", "XDG_STATE_HOME"):
            Path(self.env[key]).mkdir(parents=True, exist_ok=True)


@unittest.skipUnless(OPENCODE, "opencode is not installed")
class RunnerIntegrationTests(unittest.TestCase):
    """The runner must read a session that a real OpenCode run produced."""

    @unittest.skipUnless(opencode_major() >= 2, "the integration test needs OpenCode 2.x")
    def test_run_session_reads_a_real_opencode_session(self):
        fake = FakeModel([{"content": "done"}])
        server = FakeModelServer(fake).start()
        self.addCleanup(server.stop)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            notes = root / "notes"
            notes.mkdir()
            skill = root / "skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
            environment = OpenCodeEnvironment(root / "opencode", server.endpoint)
            deletes = []

            def fake_run(cmd, **kwargs):
                deletes.append(cmd)
                return subprocess.CompletedProcess(cmd, 0, "", "")

            options = {
                "skill_dir": str(skill),
                "opencode_cmd": "opencode",
                "standalone": True,
                "model": "fake/fake-model",
                "max_turns": 5,
                "session_timeout": 120,
                "step_idle_timeout": 60,
            }

            def fake_cli(*args, cwd=None):
                return {"dispatch_prompt": "Do the task."}, 0

            with patch.dict(os.environ, environment.env), patch("subprocess.run", side_effect=fake_run):
                ok, session_id = run_queue.run_session(
                    "implement-issue", "https://github.com/o/r/issues/1", notes, options, cli_fn=fake_cli)

            self.assertTrue(ok, session_id)
            self.assertTrue(session_id.startswith("ses_"), session_id)
            log = next(notes.glob("session-*.log"))
            parsed = parse_session_log(log)
            self.assertGreaterEqual(parsed["total_turns"], 1)
            self.assertEqual(parsed["session_id"], session_id)
            self.assertTrue(fake.requests, "the fake model received no request")
            self.assertTrue(any(request.get("stream") for request in fake.requests),
                            "no streaming request reached the fake model")
            self.assertTrue(any(cmd[:3] == ["opencode", "session", "delete"] for cmd in deletes),
                            "the runner did not delete the OpenCode session")


if __name__ == "__main__":
    unittest.main()
