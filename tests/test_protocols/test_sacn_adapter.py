"""Tests for the sACN protocol adapter."""

from typing import Any
from unittest.mock import Mock, PropertyMock
import pytest

from src.protocols.sacn_adapter import SACNAdapter
from src.protocols.types import DMXFrame, OSCMessage


class _FakeSender:
    def __init__(self, output: Any) -> None:
        self._output = output
        self.start = Mock()
        self.activate_output = Mock()
        self.deactivate_output = Mock()
        self.stop = Mock()

    def __getitem__(self, universe: int) -> Any:
        return self._output


class TestSACNAdapter:
    @pytest.mark.asyncio
    async def test_connect_creates_and_configures_sender(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_output = Mock()
        mock_sender = _FakeSender(mock_output)
        sender_factory = Mock(return_value=mock_sender)
        monkeypatch.setattr("src.protocols.sacn_adapter.sACNsender", sender_factory)

        adapter = SACNAdapter(universe=7, multicast=False, unicast_dest="10.0.0.50")
        await adapter.connect()

        sender_factory.assert_called_once_with()
        mock_sender.start.assert_called_once_with()
        mock_sender.activate_output.assert_called_once_with(7)
        assert mock_output.multicast is False
        assert mock_output.destination == "10.0.0.50"
        assert adapter.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect_stops_sender(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_output = Mock()
        mock_sender = _FakeSender(mock_output)
        monkeypatch.setattr("src.protocols.sacn_adapter.sACNsender", Mock(return_value=mock_sender))

        adapter = SACNAdapter(universe=3)
        await adapter.connect()
        assert adapter.is_connected() is True

        await adapter.disconnect()

        mock_sender.deactivate_output.assert_called_once_with(3)
        mock_sender.stop.assert_called_once_with()
        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_transmits_sparse_dmx_frame(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_output = Mock()
        mock_sender = _FakeSender(mock_output)
        monkeypatch.setattr("src.protocols.sacn_adapter.sACNsender", Mock(return_value=mock_sender))

        adapter = SACNAdapter(universe=1)
        await adapter.connect()
        adapter.send(DMXFrame(universe=1, channels={1: 255, 5: 128, 512: 1}))

        payload = mock_output.dmx_data
        assert isinstance(payload, tuple)
        assert len(payload) == 512
        assert payload[0] == 255
        assert payload[4] == 128
        assert payload[511] == 1
        assert payload[1] == 0

    @pytest.mark.asyncio
    async def test_send_in_dry_run_does_not_transmit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_output = Mock()
        mock_sender = _FakeSender(mock_output)
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.sacn_adapter.sACNsender", Mock(return_value=mock_sender))
        monkeypatch.setattr("src.protocols.base.logger", mock_logger)

        adapter = SACNAdapter(universe=1, dry_run=True)
        await adapter.connect()
        adapter.send(DMXFrame(universe=1, channels={1: 255}))

        assert "dmx_data" not in mock_output.__dict__
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args.args[0] == "protocol_dry_run_send"

    def test_send_without_connection_is_safe(self) -> None:
        adapter = SACNAdapter(universe=1)

        adapter.send(DMXFrame(universe=1, channels={1: 64}))

        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_handles_sender_errors_gracefully(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_output = Mock()
        type(mock_output).dmx_data = PropertyMock(side_effect=RuntimeError("socket error"))
        mock_sender = _FakeSender(mock_output)
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.sacn_adapter.sACNsender", Mock(return_value=mock_sender))
        monkeypatch.setattr("src.protocols.sacn_adapter.logger", mock_logger)

        adapter = SACNAdapter(universe=1)
        await adapter.connect()
        adapter.send(DMXFrame(universe=1, channels={1: 255}))

        assert mock_logger.error.call_args_list[-1].args[0] == "sacn_adapter_send_failed"

    def test_send_rejects_non_dmx_messages(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.sacn_adapter.logger", mock_logger)
        adapter = SACNAdapter(universe=1)

        adapter.send(OSCMessage(address="/lights/intensity", args=[1.0]))

        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == "sacn_adapter_invalid_message"
