"""sACN protocol adapter."""

from typing import Any
import structlog

from src.protocols.base import ProtocolAdapter
from src.protocols.types import DMXFrame, ProtocolMessage

try:
    from sacn import sACNsender
except ImportError:  # pragma: no cover - exercised only in missing dependency environments
    sACNsender = None

logger = structlog.get_logger()


class SACNAdapter(ProtocolAdapter):
    """sACN transport backed by a sender instance."""

    def __init__(
        self,
        universe: int = 1,
        multicast: bool = True,
        unicast_dest: str | None = None,
        dry_run: bool = False,
    ) -> None:
        super().__init__(dry_run=dry_run)
        self._universe = universe
        self._multicast = multicast
        self._unicast_dest = unicast_dest
        self._sender: Any | None = None

    @property
    def name(self) -> str:
        return "sacn"

    async def connect(self) -> None:
        if sACNsender is None:
            logger.error(
                "sacn_adapter_dependency_missing",
                dependency="sacn",
                universe=self._universe,
            )
            return

        try:
            sender = sACNsender()
            sender.start()
            sender.activate_output(self._universe)

            output = sender[self._universe]
            output.multicast = self._multicast
            if self._unicast_dest is not None:
                output.destination = self._unicast_dest

            self._sender = sender
            logger.info(
                "sacn_adapter_connected",
                universe=self._universe,
                multicast=self._multicast,
                unicast_dest=self._unicast_dest,
                dry_run=self.dry_run,
            )
        except Exception as exc:
            self._sender = None
            logger.error(
                "sacn_adapter_connect_failed",
                universe=self._universe,
                multicast=self._multicast,
                unicast_dest=self._unicast_dest,
                error=str(exc),
            )

    async def disconnect(self) -> None:
        sender = self._sender
        self._sender = None

        if sender is None:
            logger.info("sacn_adapter_disconnected", universe=self._universe)
            return

        try:
            sender.deactivate_output(self._universe)
        except Exception as exc:
            logger.warning(
                "sacn_adapter_deactivate_failed",
                universe=self._universe,
                error=str(exc),
            )

        try:
            sender.stop()
        except Exception as exc:
            logger.warning(
                "sacn_adapter_stop_failed",
                universe=self._universe,
                error=str(exc),
            )

        logger.info("sacn_adapter_disconnected", universe=self._universe)

    def is_connected(self) -> bool:
        return self._sender is not None

    def send(self, message: ProtocolMessage) -> None:
        if not isinstance(message, DMXFrame):
            logger.error(
                "sacn_adapter_invalid_message",
                expected="DMXFrame",
                received=type(message).__name__,
            )
            return

        if self.dry_run:
            self._log_dry_run(message)
            return

        if self._sender is None:
            logger.warning(
                "sacn_adapter_not_connected",
                universe=self._universe,
                message_universe=message.universe,
            )
            return

        if message.universe not in (0, self._universe):
            logger.warning(
                "sacn_adapter_universe_mismatch",
                adapter_universe=self._universe,
                message_universe=message.universe,
            )

        dmx_data = self._build_dmx_data(message)

        try:
            self._sender[self._universe].dmx_data = dmx_data
        except Exception as exc:
            logger.error(
                "sacn_adapter_send_failed",
                universe=self._universe,
                error=str(exc),
            )

    def _build_dmx_data(self, message: DMXFrame) -> tuple[int, ...]:
        """Create a 512-channel DMX payload from sparse channel values."""
        dmx_data: list[int] = [0] * 512

        for channel, value in message.channels.items():
            if not 1 <= channel <= 512:
                logger.warning(
                    "sacn_adapter_channel_out_of_range",
                    universe=self._universe,
                    channel=channel,
                    value=value,
                )
                continue

            if not 0 <= value <= 255:
                logger.warning(
                    "sacn_adapter_value_out_of_range",
                    universe=self._universe,
                    channel=channel,
                    value=value,
                )
                continue

            dmx_data[channel - 1] = value

        return tuple(dmx_data)
