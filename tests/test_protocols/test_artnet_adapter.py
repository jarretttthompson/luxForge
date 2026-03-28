"""Tests for the Art-Net protocol adapter."""

from unittest.mock import Mock
import pytest

from src.protocols.artnet_adapter import ArtNetAdapter
from src.protocols.types import DMXFrame, OSCMessage


class TestArtNetAdapter:
    @pytest.mark.asyncio
    async def test_connect_creates_artnet_client(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = Mock()
        client_factory = Mock(return_value=mock_client)
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", client_factory)

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()

        client_factory.assert_called_once_with("127.0.0.1", 0, 512, port=6454)
        assert adapter.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect_blackouts_and_closes_client(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()
        await adapter.disconnect()

        mock_client.blackout.assert_called_once_with()
        mock_client.close.assert_called_once_with()
        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_updates_and_transmits_dmx_buffer(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()
        adapter.send(DMXFrame(universe=0, channels={1: 255, 3: 64}))

        mock_client.set.assert_called_once()
        transmitted = mock_client.set.call_args.args[0]
        assert isinstance(transmitted, bytearray)
        assert len(transmitted) == 512
        assert transmitted[0] == 255
        assert transmitted[1] == 0
        assert transmitted[2] == 64
        mock_client.show.assert_called_once_with()

    @pytest.mark.asyncio
    async def test_send_preserves_previous_channel_values(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()
        adapter.send(DMXFrame(universe=0, channels={1: 100, 2: 50}))
        adapter.send(DMXFrame(universe=0, channels={2: 200}))

        transmitted = mock_client.set.call_args.args[0]
        assert transmitted[0] == 100
        assert transmitted[1] == 200

    @pytest.mark.asyncio
    async def test_send_in_dry_run_does_not_transmit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.base.logger", mock_logger)

        adapter = ArtNetAdapter(host="127.0.0.1", dry_run=True)
        await adapter.connect()
        adapter.send(DMXFrame(universe=0, channels={1: 255}))

        mock_client.set.assert_not_called()
        mock_client.show.assert_not_called()
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args.args[0] == "protocol_dry_run_send"

    def test_send_without_connection_is_safe(self) -> None:
        adapter = ArtNetAdapter(host="127.0.0.1")

        adapter.send(DMXFrame(universe=0, channels={1: 255}))

        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_rejects_non_dmx_messages(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.artnet_adapter.logger", mock_logger)

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()
        adapter.send(OSCMessage(address="/lights/test", args=[]))

        mock_client.set.assert_not_called()
        mock_logger.error.assert_called_once()
        assert mock_logger.error.call_args.args[0] == "artnet_adapter_invalid_message"

    @pytest.mark.asyncio
    async def test_send_ignores_mismatched_universe(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.artnet_adapter.logger", mock_logger)

        adapter = ArtNetAdapter(host="127.0.0.1", universe=1)
        await adapter.connect()
        adapter.send(DMXFrame(universe=2, channels={1: 255}))

        mock_client.set.assert_not_called()
        mock_client.show.assert_not_called()
        assert mock_logger.warning.call_args.args[0] == "artnet_adapter_universe_mismatch"

    @pytest.mark.asyncio
    async def test_send_handles_client_errors_gracefully(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_client = Mock()
        mock_logger = Mock()
        mock_client.show.side_effect = RuntimeError("socket error")
        monkeypatch.setattr("src.protocols.artnet_adapter.StupidArtnet", Mock(return_value=mock_client))
        monkeypatch.setattr("src.protocols.artnet_adapter.logger", mock_logger)

        adapter = ArtNetAdapter(host="127.0.0.1")
        await adapter.connect()
        adapter.send(DMXFrame(universe=0, channels={1: 255}))

        assert mock_logger.error.call_args_list[-1].args[0] == "artnet_adapter_send_failed"
