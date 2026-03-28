"""Tests for the OSC protocol adapter."""

from unittest.mock import Mock
import pytest

from src.protocols.osc_adapter import OSCAdapter
from src.protocols.types import OSCMessage


class TestOSCAdapter:
    @pytest.mark.asyncio
    async def test_connect_creates_udp_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = Mock()
        client_factory = Mock(return_value=mock_client)
        monkeypatch.setattr("src.protocols.osc_adapter.SimpleUDPClient", client_factory)

        adapter = OSCAdapter(host="127.0.0.1", port=9000)
        await adapter.connect()

        client_factory.assert_called_once_with("127.0.0.1", 9000)
        assert adapter.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect_clears_connection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("src.protocols.osc_adapter.SimpleUDPClient", Mock(return_value=Mock()))

        adapter = OSCAdapter(host="127.0.0.1", port=9000)
        await adapter.connect()
        assert adapter.is_connected() is True

        await adapter.disconnect()

        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_transmits_osc_message(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = Mock()
        monkeypatch.setattr("src.protocols.osc_adapter.SimpleUDPClient", Mock(return_value=mock_client))

        adapter = OSCAdapter(host="127.0.0.1", port=9000)
        await adapter.connect()
        adapter.send(OSCMessage(address="/lights/intensity", args=[1, 0.75, "go"]))

        mock_client.send_message.assert_called_once_with("/lights/intensity", [1, 0.75, "go"])

    @pytest.mark.asyncio
    async def test_send_in_dry_run_does_not_transmit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.osc_adapter.SimpleUDPClient", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.base.logger", mock_logger)

        adapter = OSCAdapter(host="127.0.0.1", port=9000, dry_run=True)
        await adapter.connect()
        adapter.send(OSCMessage(address="/lights/color", args=[255, 128, 64]))

        mock_client.send_message.assert_not_called()
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args.args[0] == "protocol_dry_run_send"

    def test_send_without_connection_is_safe(self) -> None:
        adapter = OSCAdapter(host="127.0.0.1", port=9000)

        adapter.send(OSCMessage(address="/lights/strobe", args=[127]))

        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_handles_client_errors_gracefully(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        mock_client.send_message.side_effect = RuntimeError("socket error")
        monkeypatch.setattr("src.protocols.osc_adapter.SimpleUDPClient", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.osc_adapter.logger", mock_logger)

        adapter = OSCAdapter(host="127.0.0.1", port=9000)
        await adapter.connect()
        adapter.send(OSCMessage(address="/lights/panic", args=[1]))

        assert mock_logger.error.call_args_list[-1].args[0] == "osc_adapter_send_failed"
