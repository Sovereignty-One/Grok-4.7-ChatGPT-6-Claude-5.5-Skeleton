from __future__ import annotations

import json
import os
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from mode_policy import mode_payload

DEFAULT_AI_MAX_TOKENS = 131072
DEFAULT_BRIDGE_PORT = int(os.getenv("SG_PORT", os.getenv("PORT", "9897")))
STATE_FILE = Path(os.getenv("SG_STATE_FILE", "./data/sg_state.json"))


def _parse_ai_max_tokens() -> int:
    raw = os.getenv("SG_MAX_TOKENS")
    if raw is None:
        return DEFAULT_AI_MAX_TOKENS
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_AI_MAX_TOKENS
    return value if value > 0 else DEFAULT_AI_MAX_TOKENS


AI_MAX_TOKENS = _parse_ai_max_tokens()


def build_health_payload() -> dict:
    return {
        "status": "live",
        "service": "SovereignBridge",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "port": DEFAULT_BRIDGE_PORT,
        "max_tokens": AI_MAX_TOKENS,
        "mode": mode_payload(),
    }


def build_connect_payload() -> dict:
    return {
        "status": "ok",
        "service": "SovereignBridge",
        "port": DEFAULT_BRIDGE_PORT,
        "max_tokens": AI_MAX_TOKENS,
        "mode": mode_payload(),
    }


def _load_state() -> dict:
    try:
        if STATE_FILE.exists():
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"users": {}, "files": {}, "last_sync": None}


def _sync_hint() -> dict:
    state = _load_state()
    return {
        "status": "ok",
        "port": DEFAULT_BRIDGE_PORT,
        "max_tokens": AI_MAX_TOKENS,
        "state_file": str(STATE_FILE),
        "last_sync": state.get("last_sync"),
        "files_tracked": len(state.get("files", {})),
        "users_tracked": len(state.get("users", {})),
        "mode": mode_payload(),
    }


class BridgeHandler(BaseHTTPRequestHandler):
    server_version = "SovereignBridge/2.0"

    def log_message(self, format: str, *args) -> None:
        return

    def _send_json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        if self.path in {"/", "/health", "/api/health"}:
            self._send_json(200, {**build_health_payload(), **_sync_hint()})
            return
        if self.path in {"/sync", "/api/sync", "/api/bootstrap"}:
            self._send_json(200, _sync_hint())
            return
        self.send_error(404, "Not Found")


def main() -> None:
    host = os.getenv("SG_HOST", "127.0.0.1")
    port = int(os.getenv("SG_PORT", str(DEFAULT_BRIDGE_PORT)))
    server = ThreadingHTTPServer((host, port), BridgeHandler)
    print(f"Sovereign Bridge listening on http://{host}:{port} mode={mode_payload()['mode']}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
