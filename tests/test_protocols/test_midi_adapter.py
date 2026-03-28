"""Tests for the MIDI protocol adapter."""

from unittest.mock import Mock
import pytest

from src.protocols.midi_adapter import MIDIAdapter
from src.protocols.types import MIDIMessage, OSCMessage


class TestMIDIAdapter:
    @pytest.mark.asyncio
    async def test_connect_opens_named_port(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_midi_out = Mock()
        mock_midi_out.get_ports.return_value = ["Controller A", "Synth B"]
        midi_factory = Mock(return_value=mock_midi_out)
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", midi_factory)

        adapter = MIDIAdapter(port_name="Synth B")
        await adapter.connect()

        midi_factory.assert_called_once_with()
        mock_midi_out.open_port.assert_called_once_with(1)
        assert adapter.is_connected() is True

    @pytest.mark.asyncio
    async def test_connect_creates_virtual_port_when_name_not_provided(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        adapter = MIDIAdapter()
        await adapter.connect()

        mock_midi_out.open_virtual_port.assert_called_once_with("lightingConsoleThing MIDI")
        assert adapter.is_connected() is True

    @pytest.mark.asyncio
    async def test_disconnect_closes_port_and_clears_connection(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        adapter = MIDIAdapter()
        await adapter.connect()
        assert adapter.is_connected() is True

        await adapter.disconnect()

        mock_midi_out.close_port.assert_called_once_with()
        assert adapter.is_connected() is False

    @pytest.mark.asyncio
    async def test_send_note_on_translates_to_midi_bytes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        adapter = MIDIAdapter()
        await adapter.connect()
        adapter.send(MIDIMessage(type="note_on", channel=2, note_or_cc=64, value=96))

        mock_midi_out.send_message.assert_called_once_with([0x92, 64, 96])

    @pytest.mark.asyncio
    async def test_send_note_off_translates_to_midi_bytes(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        adapter = MIDIAdapter()
        await adapter.connect()
        adapter.send(MIDIMessage(type="note_off", channel=3, note_or_cc=40, value=127))

        mock_midi_out.send_message.assert_called_once_with([0x83, 40, 0])

    @pytest.mark.asyncio
    async def test_send_cc_translates_to_midi_bytes(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_midi_out = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        adapter = MIDIAdapter()
        await adapter.connect()
        adapter.send(MIDIMessage(type="cc", channel=1, note_or_cc=10, value=127))

        mock_midi_out.send_message.assert_called_once_with([0xB1, 10, 127])

    @pytest.mark.asyncio
    async def test_send_in_dry_run_does_not_transmit(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))
        monkeypatch.setattr("src.protocols.base.logger", mock_logger)

        adapter = MIDIAdapter(dry_run=True)
        await adapter.connect()
        adapter.send(MIDIMessage(type="cc", channel=0, note_or_cc=7, value=100))

        mock_midi_out.send_message.assert_not_called()
        mock_logger.info.assert_called_once()
        assert mock_logger.info.call_args.args[0] == "protocol_dry_run_send"

    def test_send_without_connection_is_safe(self) -> None:
        adapter = MIDIAdapter(port_name="Missing Port")

        adapter.send(MIDIMessage(type="cc", channel=0, note_or_cc=1, value=64))

        assert adapter.is_connected() is False

    def test_send_rejects_invalid_message_type(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.logger", mock_logger)

        adapter = MIDIAdapter()
        adapter.send(OSCMessage(address="/not-midi", args=[1]))

        assert mock_logger.error.call_args.args[0] == "midi_adapter_invalid_message"

    def test_list_ports_returns_available_ports(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_midi_out = Mock()
        mock_midi_out.get_ports.return_value = ["Controller A", "Synth B"]
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))

        ports = MIDIAdapter.list_ports()

        assert ports == ["Controller A", "Synth B"]

    @pytest.mark.asyncio
    async def test_connect_missing_named_port_keeps_adapter_disconnected(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        mock_midi_out = Mock()
        mock_midi_out.get_ports.return_value = ["Controller A"]
        mock_logger = Mock()
        monkeypatch.setattr("src.protocols.midi_adapter.MidiOut", Mock(return_value=mock_midi_out))
        monkeypatch.setattr("src.protocols.midi_adapter.logger", mock_logger)

        adapter = MIDIAdapter(port_name="Synth B")
        await adapter.connect()

        mock_midi_out.open_port.assert_not_called()
        assert adapter.is_connected() is False
        assert mock_logger.error.call_args.args[0] == "midi_adapter_port_not_found"
