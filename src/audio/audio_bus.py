"""Async pub/sub bus for audio analysis results.

Bridges the audio capture thread to the async main loop.
One producer writes from the audio/simulator thread,
multiple async consumers subscribe and receive results.
"""

import asyncio
from collections.abc import Callable, Awaitable
import structlog

from src.audio.types import AnalysisResult

logger = structlog.get_logger()


class AudioBus:
    """Thread-safe pub/sub for AnalysisResult objects.

    The producer (audio thread) calls `publish()` which is thread-safe.
    Async consumers call `subscribe()` to get an async generator of results.
    """

    def __init__(self, max_queue_size: int = 4):
        self._subscribers: list[asyncio.Queue[AnalysisResult]] = []
        self._max_queue_size = max_queue_size
        self._loop: asyncio.AbstractEventLoop | None = None
        self._latest: AnalysisResult | None = None
        self._callbacks: list[Callable[[AnalysisResult], Awaitable[None] | None]] = []

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Set the event loop for thread-safe publishing. Call from the async main thread."""
        self._loop = loop

    def publish(self, result: AnalysisResult) -> None:
        """Publish an analysis result. Thread-safe — can be called from the audio thread."""
        self._latest = result

        if self._loop is not None and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._distribute, result)
        else:
            # Fallback: direct distribution (only works if called from async context)
            self._distribute(result)

    def _distribute(self, result: AnalysisResult) -> None:
        """Distribute result to all subscriber queues (called on the event loop thread)."""
        for queue in self._subscribers:
            try:
                # Non-blocking put; drop oldest if full
                if queue.full():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        pass
                queue.put_nowait(result)
            except Exception:
                pass  # Don't let one bad subscriber break others

        # Fire callbacks
        for callback in self._callbacks:
            try:
                ret = callback(result)
                if asyncio.iscoroutine(ret):
                    asyncio.ensure_future(ret)
            except Exception:
                pass

    def subscribe(self) -> asyncio.Queue[AnalysisResult]:
        """Create a new subscription queue. Returns an asyncio.Queue to await on."""
        queue: asyncio.Queue[AnalysisResult] = asyncio.Queue(maxsize=self._max_queue_size)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[AnalysisResult]) -> None:
        """Remove a subscription queue."""
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def on_result(self, callback: Callable[[AnalysisResult], Awaitable[None] | None]) -> None:
        """Register a callback that fires on every new result."""
        self._callbacks.append(callback)

    @property
    def latest(self) -> AnalysisResult | None:
        """Get the most recent analysis result without subscribing."""
        return self._latest

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)
