"""OSC protocol adapter."""

from typing import Any
import structlog

from src.protocols.base import ProtocolAdapter
from src.protocols.types import OSCMessage, ProtocolMessage

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:  # pragma: no cover - exercised only in missing dependency environments
    SimpleUDPClient = None

logger = structlog.get_logger()


class OSCAdapter(ProtocolAdapter):
    """OSC transport backed by a UDP client."""

    def __init__(self, host: str, port: int, dry_run: bool = False) -> None:
        super().__init__(dry_run=dry_run)
        self._host = host
        self._port = port
        self._client: Any | None = None

    @property
    def name(self) -> str:
        return "osc"

    async def connect(self) -> None:
        if SimpleUDPClient is None:
            logger.error(
                "osc_adapter_dependency_missing",
                dependency="python-osc",
                host=self._host,
                port=self._port,
            )
            return

        try:
            self._client = SimpleUDPClient(self._host, self._port)
            logger.info(
                "osc_adapter_connected",
                host=self._host,
                port=self._port,
                dry_run=self.dry_run,
            )
        except Exception as exc:
            self._client = None
            logger.error(
                "osc_adapter_connect_failed",
                host=self._host,
                port=self._port,
                error=str(exc),
            )

    async def disconnect(self) -> None:
        self._client = None
        logger.info("osc_adapter_disconnected", host=self._host, port=self._port)

    def is_connected(self) -> bool:
        return self._client is not None

    def send(self, message: ProtocolMessage) -> None:
        if not isinstance(message, OSCMessage):
            logger.error(
                "osc_adapter_invalid_message",
                expected="OSCMessage",
                received=type(message).__name__,
            )
            return

        if self.dry_run:
            self._log_dry_run(message)
            return

        if self._client is None:
            logger.warning(
                "osc_adapter_not_connected",
                host=self._host,
                port=self._port,
                address=message.address,
            )
            return

        try:
            self._client.send_message(message.address, message.args)
        except Exception as exc:
            logger.error(
                "osc_adapter_send_failed",
                host=self._host,
                port=self._port,
                address=message.address,
                error=str(exc),
            )
