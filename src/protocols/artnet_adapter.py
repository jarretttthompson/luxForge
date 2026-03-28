"""Art-Net protocol adapter."""

from typing import Protocol
import structlog

from src.protocols.base import ProtocolAdapter
from src.protocols.types import DMXFrame, ProtocolMessage

try:
    from stupidArtnet import StupidArtnet
except ImportError:  # pragma: no cover - exercised only in missing dependency environments
    StupidArtnet = None

logger = structlog.get_logger()

DMX_UNIVERSE_SIZE = 512
DMX_MIN_CHANNEL = 1
DMX_MAX_CHANNEL = 512
DMX_MIN_VALUE = 0
DMX_MAX_VALUE = 255


class ArtNetClient(Protocol):
    """Minimal interface used from the stupidArtnet transport."""

    def set(self, packet: bytearray) -> None:
        """Set the outgoing DMX packet."""

    def show(self) -> None:
        """Transmit the configured DMX packet."""

    def blackout(self) -> None:
        """Transmit a blackout frame."""

    def close(self) -> None:
        """Release socket resources."""


class ArtNetAdapter(ProtocolAdapter):
    """Art-Net transport backed by stupidArtnet."""

    def __init__(
        self,
        host: str,
        port: int = 6454,
        universe: int = 0,
        dry_run: bool = False,
    ) -> None:
        super().__init__(dry_run=dry_run)
        self._host = host
        self._port = port
        self._universe = universe
        self._client: ArtNetClient | None = None
        self._dmx_buffer = bytearray(DMX_UNIVERSE_SIZE)

    @property
    def name(self) -> str:
        return "artnet"

    async def connect(self) -> None:
        if StupidArtnet is None:
            logger.error(
                "artnet_adapter_dependency_missing",
                dependency="stupidArtnet",
                host=self._host,
                port=self._port,
                universe=self._universe,
            )
            return

        try:
            self._client = StupidArtnet(
                self._host,
                self._universe,
                DMX_UNIVERSE_SIZE,
                port=self._port,
            )
            logger.info(
                "artnet_adapter_connected",
                host=self._host,
                port=self._port,
                universe=self._universe,
                dry_run=self.dry_run,
            )
        except Exception as exc:
            self._client = None
            logger.error(
                "artnet_adapter_connect_failed",
                host=self._host,
                port=self._port,
                universe=self._universe,
                error=str(exc),
            )

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                self._client.blackout()
            except Exception as exc:
                logger.error(
                    "artnet_adapter_blackout_failed",
                    host=self._host,
                    port=self._port,
                    universe=self._universe,
                    error=str(exc),
                )

            try:
                self._client.close()
            except Exception as exc:
                logger.error(
                    "artnet_adapter_close_failed",
                    host=self._host,
                    port=self._port,
                    universe=self._universe,
                    error=str(exc),
                )

        self._client = None
        logger.info(
            "artnet_adapter_disconnected",
            host=self._host,
            port=self._port,
            universe=self._universe,
        )

    def is_connected(self) -> bool:
        return self._client is not None

    def send(self, message: ProtocolMessage) -> None:
        if not isinstance(message, DMXFrame):
            logger.error(
                "artnet_adapter_invalid_message",
                expected="DMXFrame",
                received=type(message).__name__,
            )
            return

        if message.universe != self._universe:
            logger.warning(
                "artnet_adapter_universe_mismatch",
                configured_universe=self._universe,
                message_universe=message.universe,
            )
            return

        if self.dry_run:
            self._log_dry_run(message)
            return

        if self._client is None:
            logger.warning(
                "artnet_adapter_not_connected",
                host=self._host,
                port=self._port,
                universe=self._universe,
            )
            return

        try:
            for channel, value in message.channels.items():
                if not DMX_MIN_CHANNEL <= channel <= DMX_MAX_CHANNEL:
                    logger.warning(
                        "artnet_adapter_channel_out_of_range",
                        channel=channel,
                        min_channel=DMX_MIN_CHANNEL,
                        max_channel=DMX_MAX_CHANNEL,
                    )
                    continue

                if not DMX_MIN_VALUE <= value <= DMX_MAX_VALUE:
                    logger.warning(
                        "artnet_adapter_value_out_of_range",
                        channel=channel,
                        value=value,
                        min_value=DMX_MIN_VALUE,
                        max_value=DMX_MAX_VALUE,
                    )
                    continue

                self._dmx_buffer[channel - 1] = value

            self._client.set(self._dmx_buffer)
            self._client.show()
        except Exception as exc:
            logger.error(
                "artnet_adapter_send_failed",
                host=self._host,
                port=self._port,
                universe=self._universe,
                error=str(exc),
            )
