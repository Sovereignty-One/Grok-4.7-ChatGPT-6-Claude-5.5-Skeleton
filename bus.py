"""Async event bus for inter-agent communication.

Supports an in-process asyncio queue by default. Redis is available only in
hybrid or online mode and only when REDIS_URL is configured. Offline mode is
strictly local and cannot use Redis.
"""

import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, Optional

from mode_policy import allows_redis, current_mode

logger = logging.getLogger(__name__)

_redis_client: Optional[Any] = None
_local_queue: asyncio.Queue = asyncio.Queue()
_handlers: Dict[str, Callable] = {}


async def _get_redis():
    """Return a Redis asyncio client only for an allowed execution mode."""
    global _redis_client
    if not allows_redis():
        return None
    if _redis_client is None:
        try:
            import redis.asyncio as redis

            _redis_client = redis.from_url(os.getenv("REDIS_URL", ""))
            logger.info("Event bus Redis transport enabled in %s mode", current_mode())
        except Exception as exc:
            logger.warning("Redis unavailable (%s); using in-process queue", exc)
    return _redis_client


async def send_event(agent_id: str, task: Dict[str, Any]) -> None:
    """Enqueue a task using the mode-approved local or Redis transport."""
    event = {"agent_id": agent_id, "task": task}
    redis = await _get_redis()
    if redis:
        try:
            await redis.lpush("sg:events", json.dumps(event))
            logger.debug("Sent Redis event to %s", agent_id)
            return
        except Exception as exc:
            logger.warning("Redis send failed (%s); falling back to queue", exc)
    await _local_queue.put(event)
    logger.debug("Sent local event to %s", agent_id)


def register_handler(agent_id: str, handler: Callable) -> None:
    """Register a coroutine handler for an agent identifier."""
    _handlers[agent_id] = handler
    logger.info("Registered handler for agent '%s'", agent_id)


async def process_events() -> None:
    """Continuously dequeue and dispatch events to registered handlers."""
    logger.info("Event bus processing loop started in %s mode", current_mode())
    redis = await _get_redis()

    while True:
        try:
            if redis:
                raw = await redis.brpop("sg:events", timeout=1)
                if raw is None:
                    continue
                event = json.loads(raw[1])
            else:
                event = await asyncio.wait_for(_local_queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            continue
        except asyncio.CancelledError:
            logger.info("Event bus processing loop cancelled")
            raise

        agent_id = event.get("agent_id", "")
        task = event.get("task", {})
        handler = _handlers.get(agent_id)
        if handler is None:
            logger.warning("No handler for agent '%s'; dropping event", agent_id)
            continue
        try:
            await handler(task)
        except Exception as exc:
            logger.error("Handler for '%s' raised an error: %s", agent_id, exc, exc_info=True)
