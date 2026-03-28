"""MIDI protocol adapter."""

from typing import Any
import structlog

from src.protocols.base import ProtocolAdapter
from src.protocols.types import MIDIMessage, ProtocolMessage

try:
    from rtmidi import MidiOut
except ImportError:  # pragma: no cover - exercised only in missing dependency environments
    MidiOut = None

logger = structlog.get_logger()


class MIDIAdapter(ProtocolAdapter):
    """MIDI transport backed by python-rtmidi."""

    def __init__(self, port_name: str | None = None, dry_run: bool = False) -> None:
        super().__init__(dry_run=dry_run)
        self._port_name = port_name
        self._midi_out: Any | None = None
        self._connected_port_name: str | None = None

    @property
    def name(self) -> str:
        return "midi"

    async def connect(self) -> None:
        if MidiOut is None:
            logger.error(
                "midi_adapter_dependency_missing",
                dependency="python-rtmidi",
                port_name=self._port_name,
            )
            return

        try:
            midi_out = MidiOut()
            if self._port_name is None:
                virtual_port_name = "lightingConsoleThing MIDI"
                midi_out.open_virtual_port(virtual_port_name)
                self._connected_port_name = virtual_port_name
            else:
                ports = midi_out.get_ports()
                try:
                    port_index = ports.index(self._port_name)
                except ValueError:
                    logger.error(
                        "midi_adapter_port_not_found",
                        port_name=self._port_name,
                        available_ports=ports,
                    )
                    return

                midi_out.open_port(port_index)
                self._connected_port_name = self._port_name

            self._midi_out = midi_out
            logger.info(
                "midi_adapter_connected",
                port_name=self._connected_port_name,
                dry_run=self.dry_run,
            )
        except Exception as exc:
            self._midi_out = None
            self._connected_port_name = None
            logger.error(
                "midi_adapter_connect_failed",
                port_name=self._port_name,
                error=str(exc),
            )

    async def disconnect(self) -> None:
        if self._midi_out is not None:
            try:
                self._midi_out.close_port()
            except Exception as exc:
                logger.error(
                    "midi_adapter_disconnect_failed",
                    port_name=self._connected_port_name,
                    error=str(exc),
                )

        self._midi_out = None
        self._connected_port_name = None
        logger.info("midi_adapter_disconnected", port_name=self._port_name)

    def is_connected(self) -> bool:
        return self._midi_out is not None

    def send(self, message: ProtocolMessage) -> None:
        if not isinstance(message, MIDIMessage):
            logger.error(
                "midi_adapter_invalid_message",
                expected="MIDIMessage",
                received=type(message).__name__,
            )
            return

        if self.dry_run:
            self._log_dry_run(message)
            return

        if self._midi_out is None:
            logger.warning(
                "midi_adapter_not_connected",
                port_name=self._port_name,
                message_type=message.type,
            )
            return

        midi_bytes = self._message_to_bytes(message)
        if midi_bytes is None:
            logger.error(
                "midi_adapter_unsupported_message_type",
                message_type=message.type,
            )
            return

        try:
            self._midi_out.send_message(midi_bytes)
        except Exception as exc:
            logger.error(
                "midi_adapter_send_failed",
                port_name=self._connected_port_name or self._port_name,
                message_type=message.type,
                error=str(exc),
            )

    @staticmethod
    def list_ports() -> list[str]:
        if MidiOut is None:
            logger.error("midi_adapter_dependency_missing", dependency="python-rtmidi")
            return []

        try:
            midi_out = MidiOut()
            return list(midi_out.get_ports())
        except Exception as exc:
            logger.error("midi_adapter_list_ports_failed", error=str(exc))
            return []

    @staticmethod
    def _message_to_bytes(message: MIDIMessage) -> list[int] | None:
        if message.type == "note_on":
            return [0x90 + message.channel, message.note_or_cc, message.value]
        if message.type == "note_off":
            return [0x80 + message.channel, message.note_or_cc, 0]
        if message.type == "cc":
            return [0xB0 + message.channel, message.note_or_cc, message.value]
        return None
