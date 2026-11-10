"""Shared helpers for the persistent brain compatibility layer."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import threading
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()
_BRAIN_FILE = Path.home() / ".sg_brain.json"
_SIGNING_KEY_FILE = Path.home() / ".sg_brain_signing.key"
_SIGNING_KEY_ENV = "SG_BRAIN_SIGNING_KEY"
_SIGNING_KEY_FILE_ENV = "SG_BRAIN_SIGNING_KEY_FILE"
_AGENTS_FILE = Path("brain") / "agents.json"


def _default_brain() -> dict[str, Any]:
    return {"state": {}, "scarlog": [], "agents": [], "events": [], "errors": []}


def load_brain() -> dict[str, Any]:
    with _LOCK:
        if not _BRAIN_FILE.exists():
            return _default_brain()
        try:
            data = json.loads(_BRAIN_FILE.read_text("utf-8"))
        except Exception:
            return _default_brain()
        if not isinstance(data, dict):
            return _default_brain()
        data.setdefault("state", {})
        data.setdefault("scarlog", [])
        data.setdefault("agents", [])
        data.setdefault("events", [])
        data.setdefault("errors", [])
        return data


def save_brain(data: dict[str, Any]) -> dict[str, Any]:
    with _LOCK:
        _BRAIN_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False)
        tmp = _BRAIN_FILE.with_suffix(".json.tmp")
        tmp.write_text(payload, "utf-8")
        os.replace(tmp, _BRAIN_FILE)
        return data


def load_signing_key() -> bytes:
    with _LOCK:
        env_key = os.environ.get(_SIGNING_KEY_ENV, "").strip()
        if env_key:
            try:
                raw = bytes.fromhex(env_key)
            except ValueError as exc:
                raise RuntimeError(
                    f"{_SIGNING_KEY_ENV} must be a valid hex-encoded key."
                ) from exc
            if not raw:
                raise RuntimeError(f"{_SIGNING_KEY_ENV} is set but empty.")
            return raw

        configured_key_path = os.environ.get(_SIGNING_KEY_FILE_ENV, "").strip()
        key_path = Path(configured_key_path).expanduser() if configured_key_path else _SIGNING_KEY_FILE
        if not key_path.exists():
            raise FileNotFoundError(
                "Persistent signing key is missing. Configure "
                f"{_SIGNING_KEY_ENV} or mount/create a key file at {key_path} "
                f"(override path with {_SIGNING_KEY_FILE_ENV})."
            )

        try:
            raw = bytes.fromhex(key_path.read_text("utf-8").strip())
        except (ValueError, OSError) as exc:
            raise RuntimeError(
                f"Persistent signing key file {key_path} is unreadable or contains invalid hex."
            ) from exc
        if not raw:
            raise RuntimeError(f"Persistent signing key file {key_path} is empty.")
        return raw


def save_signing_key(key: bytes) -> None:
    with _LOCK:
        configured_key_path = os.environ.get(_SIGNING_KEY_FILE_ENV, "").strip()
        key_path = Path(configured_key_path).expanduser() if configured_key_path else _SIGNING_KEY_FILE
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_text(key.hex(), "utf-8")


def ensure_agents_file(agents: list[dict[str, Any]]) -> None:
    _AGENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _AGENTS_FILE.write_text(json.dumps(agents, indent=2, sort_keys=True, ensure_ascii=False), "utf-8")


class Signer:
    def __init__(self) -> None:
        self._key = load_signing_key()

    def rotate(self) -> bytes:
        self._key = secrets.token_bytes(32)
        save_signing_key(self._key)
        return self._key

    def sign(self, data: bytes) -> bytes:
        return hmac.new(self._key, data, hashlib.sha256).digest()


signer = Signer()
