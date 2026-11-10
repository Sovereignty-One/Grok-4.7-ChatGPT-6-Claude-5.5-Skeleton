from __future__ import annotations

import importlib
import os
from types import ModuleType

from mode_policy import mode_payload

_impl: ModuleType = importlib.import_module("bridge.python3_bridge")

DEFAULT_AI_MAX_TOKENS = getattr(_impl, "DEFAULT_AI_MAX_TOKENS", 131072)
BridgeHandler = getattr(_impl, "BridgeHandler")
main = getattr(_impl, "main")


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
        "port": getattr(_impl, "DEFAULT_BRIDGE_PORT", 9897),
        "max_tokens": AI_MAX_TOKENS,
        "mode": mode_payload(),
    }


def build_connect_payload() -> dict:
    return {
        "status": "ok",
        "service": "SovereignBridge",
        "port": getattr(_impl, "DEFAULT_BRIDGE_PORT", 9897),
        "max_tokens": AI_MAX_TOKENS,
        "mode": mode_payload(),
    }


__all__ = [
    "AI_MAX_TOKENS",
    "DEFAULT_AI_MAX_TOKENS",
    "BridgeHandler",
    "build_connect_payload",
    "build_health_payload",
    "main",
    "_parse_ai_max_tokens",
]

if __name__ == "__main__":
    main()
