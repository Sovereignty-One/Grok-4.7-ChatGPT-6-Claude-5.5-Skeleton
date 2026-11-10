"""Central execution-mode policy for the public local control plane.

The mode is explicit and fail-closed:
- Linux defaults to hybrid so self-hosted Linux is the primary boundary.
- Other platforms default to offline.
- Online mode is never selected implicitly.

This module only describes routing policy. It does not execute network calls,
load provider credentials, or grant authority.
"""
from __future__ import annotations

import os
import platform
from typing import Any

MODES = frozenset({"offline", "hybrid", "online"})


def current_mode() -> str:
    configured = os.getenv("SG_MODE", "").strip().lower()
    if configured in MODES:
        return configured
    return "hybrid" if platform.system().lower() == "linux" else "offline"


def allows_redis(mode: str | None = None) -> bool:
    return (mode or current_mode()) in {"hybrid", "online"} and bool(
        os.getenv("REDIS_URL", "").strip()
    )


def allows_external_network(mode: str | None = None) -> bool:
    return (mode or current_mode()) == "online"


def mode_payload(mode: str | None = None) -> dict[str, Any]:
    selected = mode or current_mode()
    if selected not in MODES:
        raise ValueError(f"unsupported SG_MODE: {selected}")

    return {
        "mode": selected,
        "execution_boundary": "self-hosted-linux" if selected == "hybrid" else "local",
        "network": {
            "external": allows_external_network(selected),
            "redis": allows_redis(selected),
            "loopback": True,
        },
        "pqc_boundary": selected in {"hybrid", "online"},
        "online_requires_explicit_mode": True,
    }
