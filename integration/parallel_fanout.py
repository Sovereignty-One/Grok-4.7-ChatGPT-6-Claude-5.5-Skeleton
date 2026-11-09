"""Bounded async fan-out for already-authorized local model adapters.

No provider SDK, network client, or credentials are loaded here. Callers inject
model functions. A task-bound, unexpired GateAuthorization is mandatory.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Mapping


@dataclass(frozen=True)
class ProviderResult:
    provider_id: str
    status: str
    output: Any = None
    output_digest: str | None = None
    error_code: str | None = None


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


async def parallel_fanout(
    *,
    task_id: str,
    payload: Mapping[str, Any],
    authorization: Any,
    providers: Mapping[str, Callable[[Mapping[str, Any]], Awaitable[Any]]],
    max_concurrency: int = 3,
    timeout_seconds: float = 30.0,
    authorization_verifier: Callable[[Any, str], bool] | None = None,
) -> list[ProviderResult]:
    if not task_id or not isinstance(task_id, str):
        raise ValueError("task_id required")
    if not callable(getattr(authorization, "is_valid_for", None)):
        raise PermissionError("GateAuthorization is required")
    if authorization.is_valid_for(task_id) is not True:
        raise PermissionError("missing, expired, or task-mismatched GateAuthorization")
    if authorization_verifier is None or authorization_verifier(authorization, task_id) is not True:
        raise PermissionError("GateAuthorization cryptographic verification failed")
    if not providers or len(providers) != len(set(providers)):
        raise ValueError("unique provider adapters required")
    if not 1 <= max_concurrency <= 16:
        raise ValueError("max_concurrency must be between 1 and 16")
    if not 0 < timeout_seconds <= 300:
        raise ValueError("timeout_seconds must be in (0, 300]")
    if not isinstance(payload, Mapping):
        raise TypeError("payload must be a mapping")

    semaphore = asyncio.Semaphore(max_concurrency)

    async def invoke(provider_id: str, function: Callable) -> ProviderResult:
        async with semaphore:
            try:
                output = await asyncio.wait_for(function(dict(payload)), timeout=timeout_seconds)
                return ProviderResult(provider_id, "completed", output, _digest(output))
            except asyncio.TimeoutError:
                return ProviderResult(provider_id, "timeout", error_code="DEADLINE_EXCEEDED")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                return ProviderResult(provider_id, "failed", error_code=type(exc).__name__)

    tasks = [asyncio.create_task(invoke(name, fn)) for name, fn in providers.items()]
    try:
        return list(await asyncio.gather(*tasks))
    except BaseException:
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        raise
