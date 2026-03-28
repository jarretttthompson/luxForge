"""Tests for the AsyncEventBus."""

import asyncio
import pytest

from src.engine.events import AsyncEventBus


@pytest.mark.asyncio
class TestAsyncEventBus:
    async def test_subscribe_and_publish(self):
        bus = AsyncEventBus()
        received = []

        async def handler(data):
            received.append(data)

        bus.subscribe("test.event", handler)
        await bus.publish("test.event", {"key": "value"})

        assert len(received) == 1
        assert received[0] == {"key": "value"}

    async def test_multiple_subscribers(self):
        bus = AsyncEventBus()
        results_a = []
        results_b = []

        async def handler_a(data):
            results_a.append(data)

        async def handler_b(data):
            results_b.append(data)

        bus.subscribe("test", handler_a)
        bus.subscribe("test", handler_b)
        await bus.publish("test", 42)

        assert results_a == [42]
        assert results_b == [42]

    async def test_unsubscribe(self):
        bus = AsyncEventBus()
        received = []

        async def handler(data):
            received.append(data)

        bus.subscribe("test", handler)
        await bus.publish("test", 1)
        bus.unsubscribe("test", handler)
        await bus.publish("test", 2)

        assert received == [1]

    async def test_publish_no_subscribers(self):
        bus = AsyncEventBus()
        # Should not raise
        await bus.publish("nobody.listening", "data")

    async def test_sync_callback(self):
        bus = AsyncEventBus()
        received = []

        def sync_handler(data):
            received.append(data)

        bus.subscribe("test", sync_handler)
        await bus.publish("test", "hello")

        assert received == ["hello"]

    async def test_error_in_callback_doesnt_break_others(self):
        bus = AsyncEventBus()
        received = []

        async def bad_handler(data):
            raise ValueError("boom")

        async def good_handler(data):
            received.append(data)

        bus.subscribe("test", bad_handler)
        bus.subscribe("test", good_handler)
        await bus.publish("test", "ok")

        assert received == ["ok"]

    async def test_event_types_property(self):
        bus = AsyncEventBus()
        bus.subscribe("a", lambda d: None)
        bus.subscribe("b", lambda d: None)
        assert set(bus.event_types) == {"a", "b"}
