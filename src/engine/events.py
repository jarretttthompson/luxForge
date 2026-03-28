"""Async event bus for internal publish/subscribe communication."""

import asyncio
from collections import defaultdict
from collections.abc import Callable, Awaitable
from typing import Any

import structlog

logger = structlog.get_logger()


class AsyncEventBus:
    """Simple async pub/sub event bus.

    Event types:
    - "audio.analysis"       — new AnalysisResult available
    - "mapping.output"       — new OutputValues computed
    - "scene.activated"      — a scene was activated
    - "scene.deactivated"    — a scene was deactivated
    - "protocol.status"      — protocol connection status changed
    - "engine.started"       — engine loop started
    - "engine.stopped"       — engine loop stopped
    """

    def __init__(self):
        self._subscribers: dict[str, list[Callable[[Any], Awaitable[None] | None]]] = defaultdict(list)

    def subscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None] | None]) -> None:
        """Subscribe to an event type."""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: Callable[[Any], Awaitable[None] | None]) -> None:
        """Unsubscribe from an event type."""
        if event_type in self._subscribers:
            try:
                self._subscribers[event_type].remove(callback)
            except ValueError:
                pass

    async def publish(self, event_type: str, data: Any = None) -> None:
        """Publish an event to all subscribers. Awaits async callbacks."""
        for callback in self._subscribers.get(event_type, []):
            try:
                result = callback(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.error("event_callback_error", event_type=event_type, error=str(e))

    def publish_sync(self, event_type: str, data: Any = None) -> None:
        """Fire-and-forget publish for use from sync contexts. Schedules callbacks as tasks."""
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(self.publish(event_type, data))

    @property
    def event_types(self) -> list[str]:
        """Return all event types that have subscribers."""
        return list(self._subscribers.keys())
