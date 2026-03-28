"""Tests for the Onyx NX1 console interface."""

import pytest

from src.console.onyx import OnyxConsole
from src.console.types import ConsoleCapability, ConsoleCommand
from src.protocols.types import OSCMessage, MIDIMessage


class TestOnyxTranslateFader:
    def test_fader_produces_osc_message(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        cmd = ConsoleCommand(target="playback.1.fader", value=0.75, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = onyx.translate(cmd)
        assert len(messages) == 1
        msg = messages[0]
        assert isinstance(msg, OSCMessage)
        assert msg.address == "/Mx/fader/101"
        assert msg.args == [0.75]

    def test_fader_5_address(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        cmd = ConsoleCommand(target="playback.5.fader", value=0.5, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = onyx.translate(cmd)
        assert messages[0].address == "/Mx/fader/105"

    def test_fader_with_midi(self):
        onyx = OnyxConsole(use_osc=True, use_midi=True)
        cmd = ConsoleCommand(target="playback.1.fader", value=1.0, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = onyx.translate(cmd)
        assert len(messages) == 2
        osc_msg = messages[0]
        midi_msg = messages[1]
        assert isinstance(osc_msg, OSCMessage)
        assert isinstance(midi_msg, MIDIMessage)
        assert midi_msg.type == "cc"
        assert midi_msg.value == 127

    def test_fader_midi_value_scaling(self):
        onyx = OnyxConsole(use_osc=False, use_midi=True)
        cmd = ConsoleCommand(target="playback.1.fader", value=0.5, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = onyx.translate(cmd)
        assert len(messages) == 1
        assert messages[0].value == 63  # int(0.5 * 127)


class TestOnyxTranslateGo:
    def test_go_produces_osc_message(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        cmd = ConsoleCommand(target="playback.1.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO)
        messages = onyx.translate(cmd)
        assert len(messages) == 1
        msg = messages[0]
        assert isinstance(msg, OSCMessage)
        assert msg.address == "/Mx/button/4201"
        assert msg.args == [1]

    def test_go_playback_3(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        cmd = ConsoleCommand(target="playback.3.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO)
        messages = onyx.translate(cmd)
        assert messages[0].address == "/Mx/button/4203"

    def test_go_with_midi(self):
        onyx = OnyxConsole(use_osc=False, use_midi=True)
        cmd = ConsoleCommand(target="playback.1.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO)
        messages = onyx.translate(cmd)
        assert len(messages) == 1
        assert isinstance(messages[0], MIDIMessage)
        assert messages[0].type == "note_on"
        assert messages[0].note_or_cc == 60
        assert messages[0].value == 127


class TestOnyxTranslateStop:
    def test_stop_produces_osc_message(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        cmd = ConsoleCommand(target="playback.1.stop", value=1.0, command_type=ConsoleCapability.PLAYBACK_STOP)
        messages = onyx.translate(cmd)
        assert len(messages) == 1
        assert messages[0].address == "/Mx/button/4101"


class TestOnyxEdgeCases:
    def test_unknown_target_returns_empty(self):
        onyx = OnyxConsole()
        cmd = ConsoleCommand(target="something.weird", value=1.0, command_type=ConsoleCapability.BUTTON)
        messages = onyx.translate(cmd)
        assert messages == []

    def test_unknown_action_returns_empty(self):
        onyx = OnyxConsole()
        cmd = ConsoleCommand(target="playback.1.flash", value=1.0, command_type=ConsoleCapability.BUTTON)
        messages = onyx.translate(cmd)
        assert messages == []

    def test_invalid_playback_number_returns_empty(self):
        onyx = OnyxConsole()
        cmd = ConsoleCommand(target="playback.abc.fader", value=0.5, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = onyx.translate(cmd)
        assert messages == []


class TestOnyxOutputParameters:
    def test_generates_parameters_for_all_playbacks(self):
        onyx = OnyxConsole(num_playbacks=10)
        params = onyx.get_output_parameters()
        # 10 playbacks * 3 actions (fader, go, stop) = 30 params
        assert len(params) == 30

    def test_parameter_names_format(self):
        onyx = OnyxConsole(num_playbacks=2)
        params = onyx.get_output_parameters()
        assert "onyx.playback.1.fader" in params
        assert "onyx.playback.1.go" in params
        assert "onyx.playback.1.stop" in params
        assert "onyx.playback.2.fader" in params

    def test_capabilities(self):
        onyx = OnyxConsole(use_osc=True, use_midi=False)
        caps = onyx.get_capabilities()
        assert ConsoleCapability.PLAYBACK_FADER in caps
        assert ConsoleCapability.PLAYBACK_GO in caps
