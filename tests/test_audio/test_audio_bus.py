"""Tests for the async audio bus pub/sub system."""

import asyncio
import pytest

from src.audio.types import AnalysisResult, BandEnergies
from src.audio.audio_bus import AudioBus


def make_result(rms: float = 0.5, beat: bool = False) -> AnalysisResult:
    """Helper to create a test AnalysisResult."""
    return AnalysisResult(rms=rms, beat_detected=beat, bpm=120.0)


class TestAudioBus:
    def test_initial_state(self):
        bus = AudioBus()
        assert bus.latest is None
        assert bus.subscriber_count == 0

    def test_publish_updates_latest(self):
        bus = AudioBus()
        result = make_result(rms=0.7)
        bus.publish(result)
        assert bus.latest is not None
        assert bus.latest.rms == 0.7

    def test_subscribe_creates_queue(self):
        bus = AudioBus()
        queue = bus.subscribe()
        assert bus.subscriber_count == 1
        assert isinstance(queue, asyncio.Queue)

    def test_unsubscribe_removes_queue(self):
        bus = AudioBus()
        queue = bus.subscribe()
        assert bus.subscriber_count == 1
        bus.unsubscribe(queue)
        assert bus.subscriber_count == 0

    def test_unsubscribe_nonexistent_is_safe(self):
        bus = AudioBus()
        queue = asyncio.Queue()
        bus.unsubscribe(queue)  # Should not raise
        assert bus.subscriber_count == 0

    @pytest.mark.asyncio
    async def test_subscriber_receives_published_result(self):
        bus = AudioBus()
        loop = asyncio.get_event_loop()
        bus.set_loop(loop)

        queue = bus.subscribe()
        result = make_result(rms=0.8)
        bus.publish(result)

        # Give the event loop a chance to process
        await asyncio.sleep(0.01)

        received = queue.get_nowait()
        assert received.rms == 0.8

    @pytest.mark.asyncio
    async def test_multiple_subscribers_all_receive(self):
        bus = AudioBus()
        loop = asyncio.get_event_loop()
        bus.set_loop(loop)

        q1 = bus.subscribe()
        q2 = bus.subscribe()
        q3 = bus.subscribe()

        bus.publish(make_result(rms=0.6))
        await asyncio.sleep(0.01)

        assert q1.get_nowait().rms == 0.6
        assert q2.get_nowait().rms == 0.6
        assert q3.get_nowait().rms == 0.6

    @pytest.mark.asyncio
    async def test_queue_drops_oldest_when_full(self):
        bus = AudioBus(max_queue_size=2)
        loop = asyncio.get_event_loop()
        bus.set_loop(loop)

        queue = bus.subscribe()

        # Publish 3 results (queue max is 2)
        bus.publish(make_result(rms=0.1))
        await asyncio.sleep(0.01)
        bus.publish(make_result(rms=0.2))
        await asyncio.sleep(0.01)
        bus.publish(make_result(rms=0.3))
        await asyncio.sleep(0.01)

        # Should have the 2 most recent
        assert queue.qsize() == 2
        r1 = queue.get_nowait()
        r2 = queue.get_nowait()
        assert r1.rms == 0.2
        assert r2.rms == 0.3

    @pytest.mark.asyncio
    async def test_callback_fires_on_publish(self):
        bus = AudioBus()
        loop = asyncio.get_event_loop()
        bus.set_loop(loop)

        received = []
        bus.on_result(lambda r: received.append(r))

        bus.publish(make_result(rms=0.9))
        await asyncio.sleep(0.01)

        assert len(received) == 1
        assert received[0].rms == 0.9

    @pytest.mark.asyncio
    async def test_publish_without_loop_still_works(self):
        """Publishing without set_loop should still update latest and distribute."""
        bus = AudioBus()
        queue = bus.subscribe()

        bus.publish(make_result(rms=0.4))
        assert bus.latest.rms == 0.4
        # Direct distribution (no call_soon_threadsafe)
        assert queue.get_nowait().rms == 0.4
