"""Simulator console for hardware-free development.

Implements ConsoleInterface with an in-memory virtual console.
Tracks fader positions and cuelist states without any real hardware.
"""

import structlog

from src.console.base import ConsoleInterface
from src.console.types import ConsoleCapability, ConsoleCommand, ParameterDef
from src.protocols.types import ProtocolMessage

logger = structlog.get_logger()


class SimulatorConsole(ConsoleInterface):
    """Virtual console that tracks state in memory.

    No real protocol messages are generated. Instead, commands update
    internal state which can be queried via get_state() for UI display.
    """

    def __init__(self, num_playbacks: int = 10):
        self._num_playbacks = num_playbacks

        # Virtual state
        self._fader_positions: dict[str, float] = {}
        self._cuelist_states: dict[str, bool] = {}  # True = running
        self._command_history: list[ConsoleCommand] = []
        self._max_history = 100

        # Initialize faders at 0
        for i in range(1, num_playbacks + 1):
            self._fader_positions[f"playback.{i}.fader"] = 0.0
            self._cuelist_states[f"playback.{i}"] = False

    @property
    def name(self) -> str:
        return "Simulator Console"

    def get_capabilities(self) -> list[ConsoleCapability]:
        return [
            ConsoleCapability.PLAYBACK_FADER,
            ConsoleCapability.PLAYBACK_GO,
            ConsoleCapability.PLAYBACK_STOP,
            ConsoleCapability.BUTTON,
        ]

    def translate(self, command: ConsoleCommand) -> list[ProtocolMessage]:
        """Update internal state instead of generating protocol messages."""
        self._command_history.append(command)
        if len(self._command_history) > self._max_history:
            self._command_history = self._command_history[-self._max_history:]

        parts = command.target.split(".")
        if len(parts) == 3 and parts[0] == "playback":
            playback_key = f"playback.{parts[1]}"
            action = parts[2]

            if action == "fader":
                self._fader_positions[command.target] = command.value
            elif action == "go":
                self._cuelist_states[playback_key] = True
            elif action == "stop":
                self._cuelist_states[playback_key] = False

        # Return empty list — no real protocol messages for the simulator
        return []

    def get_output_parameters(self) -> dict[str, ParameterDef]:
        """Same parameters as a real console — mapping engine doesn't know the difference."""
        params: dict[str, ParameterDef] = {}
        for i in range(1, self._num_playbacks + 1):
            fader_name = f"simulator.playback.{i}.fader"
            params[fader_name] = ParameterDef(
                name=fader_name,
                display_name=f"Sim Playback {i} Fader",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_FADER,
            )
            go_name = f"simulator.playback.{i}.go"
            params[go_name] = ParameterDef(
                name=go_name,
                display_name=f"Sim Playback {i} Go",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_GO,
            )
            stop_name = f"simulator.playback.{i}.stop"
            params[stop_name] = ParameterDef(
                name=stop_name,
                display_name=f"Sim Playback {i} Stop",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_STOP,
            )
        return params

    def get_state(self) -> dict:
        """Return the current virtual console state for UI display."""
        return {
            "faders": dict(self._fader_positions),
            "cuelists": dict(self._cuelist_states),
            "last_commands": [
                {"target": c.target, "value": c.value, "type": c.command_type.value}
                for c in self._command_history[-10:]
            ],
        }

    def get_fader(self, target: str) -> float:
        """Get a specific fader position."""
        return self._fader_positions.get(target, 0.0)

    def reset(self) -> None:
        """Reset all state to defaults."""
        for key in self._fader_positions:
            self._fader_positions[key] = 0.0
        for key in self._cuelist_states:
            self._cuelist_states[key] = False
        self._command_history.clear()
