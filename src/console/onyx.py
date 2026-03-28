"""Obsidian Onyx NX1 console interface.

Translates abstract console commands into OSC and MIDI messages
based on the Onyx OSC address space.
"""

import json
from pathlib import Path
import structlog

from src.console.base import ConsoleInterface
from src.console.types import ConsoleCapability, ConsoleCommand, ParameterDef
from src.protocols.types import ProtocolMessage, OSCMessage, MIDIMessage

logger = structlog.get_logger()

DEFAULT_OSC_MAP_PATH = Path(__file__).parent.parent.parent / "onyx_osc_map.json"


class OnyxConsole(ConsoleInterface):
    """Obsidian Onyx NX1 console interface.

    Supports OSC and MIDI output paths. The OSC address mapping is loaded
    from a JSON config file so it can be updated as Onyx firmware changes.
    """

    def __init__(
        self,
        osc_map_path: Path | str | None = None,
        use_osc: bool = True,
        use_midi: bool = False,
        num_playbacks: int = 10,
    ):
        self._use_osc = use_osc
        self._use_midi = use_midi
        self._num_playbacks = num_playbacks

        # Load OSC map
        map_path = Path(osc_map_path) if osc_map_path else DEFAULT_OSC_MAP_PATH
        if map_path.exists():
            with open(map_path) as f:
                self._osc_map = json.load(f)
            logger.info("onyx_osc_map_loaded", path=str(map_path))
        else:
            logger.warning("onyx_osc_map_not_found", path=str(map_path), using="defaults")
            self._osc_map = self._default_map()

        self._playback_config = self._osc_map.get("playbacks", {})
        self._midi_config = self._osc_map.get("midi", {})

    @property
    def name(self) -> str:
        return "Obsidian Onyx NX1"

    def get_capabilities(self) -> list[ConsoleCapability]:
        caps = [ConsoleCapability.PLAYBACK_FADER, ConsoleCapability.PLAYBACK_GO, ConsoleCapability.PLAYBACK_STOP]
        if self._use_midi:
            caps.append(ConsoleCapability.BUTTON)
        return caps

    def translate(self, command: ConsoleCommand) -> list[ProtocolMessage]:
        """Translate a console command into OSC/MIDI messages."""
        messages: list[ProtocolMessage] = []

        parts = command.target.split(".")
        # Expected format: "playback.{number}.{action}"
        if len(parts) != 3 or parts[0] != "playback":
            logger.warning("onyx_unknown_command", target=command.target)
            return messages

        try:
            playback_num = int(parts[1])
        except ValueError:
            logger.warning("onyx_invalid_playback_number", target=command.target)
            return messages

        action = parts[2]

        if action == "fader":
            messages.extend(self._translate_fader(playback_num, command.value))
        elif action == "go":
            messages.extend(self._translate_go(playback_num))
        elif action == "stop":
            messages.extend(self._translate_stop(playback_num))
        else:
            logger.warning("onyx_unknown_action", action=action, target=command.target)

        return messages

    def _translate_fader(self, playback_num: int, value: float) -> list[ProtocolMessage]:
        messages: list[ProtocolMessage] = []
        if self._use_osc:
            fader_id = self._playback_config.get("fader_id_offset", 100) + playback_num
            template = self._playback_config.get("fader_address_template", "/Mx/fader/{id}")
            address = template.replace("{id}", str(fader_id))
            messages.append(OSCMessage(address=address, args=[float(value)]))

        if self._use_midi:
            cc_num = self._midi_config.get("fader_cc_offset", 1) + playback_num - 1
            channel = self._midi_config.get("fader_channel", 0)
            midi_val = int(max(0, min(127, value * 127)))
            messages.append(MIDIMessage(type="cc", channel=channel, note_or_cc=cc_num, value=midi_val))

        return messages

    def _translate_go(self, playback_num: int) -> list[ProtocolMessage]:
        messages: list[ProtocolMessage] = []
        if self._use_osc:
            go_id = self._playback_config.get("go_id_offset", 4200) + playback_num
            template = self._playback_config.get("go_address_template", "/Mx/button/{id}")
            address = template.replace("{id}", str(go_id))
            messages.append(OSCMessage(address=address, args=[1]))

        if self._use_midi:
            note = self._midi_config.get("go_note_offset", 60) + playback_num - 1
            channel = self._midi_config.get("go_channel", 0)
            messages.append(MIDIMessage(type="note_on", channel=channel, note_or_cc=note, value=127))

        return messages

    def _translate_stop(self, playback_num: int) -> list[ProtocolMessage]:
        messages: list[ProtocolMessage] = []
        if self._use_osc:
            stop_id = self._playback_config.get("stop_id_offset", 4100) + playback_num
            template = self._playback_config.get("stop_address_template", "/Mx/button/{id}")
            address = template.replace("{id}", str(stop_id))
            messages.append(OSCMessage(address=address, args=[1]))
        return messages

    def get_output_parameters(self) -> dict[str, ParameterDef]:
        """Generate output parameters for all configured playbacks."""
        params: dict[str, ParameterDef] = {}
        count = self._playback_config.get("count", self._num_playbacks)

        for i in range(1, count + 1):
            # Fader
            fader_name = f"onyx.playback.{i}.fader"
            params[fader_name] = ParameterDef(
                name=fader_name,
                display_name=f"Playback {i} Fader",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_FADER,
            )
            # Go
            go_name = f"onyx.playback.{i}.go"
            params[go_name] = ParameterDef(
                name=go_name,
                display_name=f"Playback {i} Go",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_GO,
            )
            # Stop
            stop_name = f"onyx.playback.{i}.stop"
            params[stop_name] = ParameterDef(
                name=stop_name,
                display_name=f"Playback {i} Stop",
                min_val=0.0,
                max_val=1.0,
                default_val=0.0,
                command_type=ConsoleCapability.PLAYBACK_STOP,
            )

        return params

    @staticmethod
    def _default_map() -> dict:
        return {
            "playbacks": {
                "count": 10,
                "fader_address_template": "/Mx/fader/{id}",
                "fader_id_offset": 100,
                "go_address_template": "/Mx/button/{id}",
                "go_id_offset": 4200,
                "stop_address_template": "/Mx/button/{id}",
                "stop_id_offset": 4100,
            },
            "midi": {
                "fader_cc_offset": 1,
                "go_note_offset": 60,
                "go_channel": 0,
                "fader_channel": 0,
            },
        }
