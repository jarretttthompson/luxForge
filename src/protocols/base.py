"""Abstract base classes for outbound protocol adapters."""

from abc import ABC, abstractmethod
import structlog

from src.protocols.types import ProtocolMessage

logger = structlog.get_logger()


class ProtocolAdapter(ABC):
    """Common interface for protocol transports."""

    def __init__(self, dry_run: bool = False) -> None:
        self._dry_run = dry_run

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name."""

    @abstractmethod
    async def connect(self) -> None:
        """Initialize transport resources."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Release transport resources."""

    @abstractmethod
    def is_connected(self) -> bool:
        """Return whether the adapter is ready to transmit."""

    @abstractmethod
    def send(self, message: ProtocolMessage) -> None:
        """Send a message synchronously and return quickly."""

    @property
    def dry_run(self) -> bool:
        """Return whether the adapter is running in dry-run mode."""
        return self._dry_run

    def _log_dry_run(self, message: ProtocolMessage) -> None:
        """Log a dry-run send without transmitting."""
        logger.info(
            "protocol_dry_run_send",
            adapter=self.name,
            message_type=type(message).__name__,
            message=message,
        )
