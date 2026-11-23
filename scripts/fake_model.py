#!/usr/bin/env python3
"""A tiny OpenAI-compatible model server for runner integration tests.

It serves the chat-completions endpoint that OpenCode calls and replays a
script of text responses. It uses only the standard library and holds no
credentials. ``FakeModel.requests`` keeps each request body; ``GET /calls``
returns the same list for a manual check.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, List, Optional


DEFAULT_MODEL = "fake-model"
DEFAULT_RESPONSE = {"content": "done"}


class FakeModel:
    """A scripted response list and the request bodies received so far."""

    def __init__(self, responses: Optional[List[Dict[str, Any]]] = None, model: str = DEFAULT_MODEL):
        self.responses = list(responses or [DEFAULT_RESPONSE])
        self.model = model
        self.requests: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, body: Dict[str, Any]) -> None:
        with self._lock:
            self.requests.append(body)

    def next_response(self) -> Dict[str, Any]:
        with self._lock:
            if len(self.responses) > 1:
                return self.responses.pop(0)
            return self.responses[0]


class _Handler(BaseHTTPRequestHandler):
    server_version = "ghflow-fake-model/1"

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def _json(self, payload: Any, status: int = 200) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = self.path.rstrip("/")
        if path in ("/v1/models", "/models"):
            self._json({"object": "list",
                        "data": [{"id": self.server.fake.model, "object": "model", "owned_by": "fake"}]})
            return
        if path in ("/calls", "/v1/calls"):
            self._json({"calls": self.server.fake.requests})
            return
        self._json({"error": {"message": "not found"}}, 404)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            body = {}
        if not isinstance(body, dict):
            body = {}
        self.server.fake.record(body)
        if not self.path.rstrip("/").endswith("/chat/completions"):
            self._json({"error": {"message": "not found"}}, 404)
            return
        response = self.server.fake.next_response()
        if body.get("stream"):
            self._stream(response)
        else:
            self._completion(response)

    def _completion(self, response: Dict[str, Any]) -> None:
        self._json({
            "id": "chatcmpl-fake",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.server.fake.model,
            "choices": [{"index": 0,
                         "message": {"role": "assistant", "content": response.get("content") or ""},
                         "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11},
        })

    def _stream(self, response: Dict[str, Any]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        base = {"id": "chatcmpl-fake", "object": "chat.completion.chunk",
                "created": int(time.time()), "model": self.server.fake.model}

        def send(delta: Dict[str, Any], finish: Optional[str] = None) -> None:
            chunk = {**base, "choices": [{"index": 0, "delta": delta, "finish_reason": finish}]}
            self.wfile.write(f"data: {json.dumps(chunk)}\n\n".encode("utf-8"))
            self.wfile.flush()

        send({"role": "assistant"})
        content = response.get("content") or ""
        if content:
            send({"content": content})
        final = {**base,
                 "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                 "usage": {"prompt_tokens": 10, "completion_tokens": 1, "total_tokens": 11}}
        self.wfile.write(f"data: {json.dumps(final)}\n\n".encode("utf-8"))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()


class FakeModelServer:
    """Run a FakeModel on a loopback port in a background thread."""

    def __init__(self, fake: Optional[FakeModel] = None, host: str = "127.0.0.1", port: int = 0):
        self.fake = fake or FakeModel()
        self.httpd = ThreadingHTTPServer((host, port), _Handler)
        self.httpd.daemon_threads = True
        self.httpd.fake = self.fake
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def endpoint(self) -> str:
        host, port = self.httpd.server_address[:2]
        return f"http://{host}:{port}/v1"

    def start(self) -> "FakeModelServer":
        self.thread.start()
        return self

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def __enter__(self) -> "FakeModelServer":
        return self.start()

    def __exit__(self, *exc: Any) -> None:
        self.stop()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Serve a scripted OpenAI-compatible model for runner tests.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0, help="port (default: an ephemeral port)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--content", default=DEFAULT_RESPONSE["content"],
                        help="text the model returns for each request")
    args = parser.parse_args(argv)
    server = FakeModelServer(FakeModel([{"content": args.content}], model=args.model),
                             host=args.host, port=args.port).start()
    print(server.endpoint, flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
