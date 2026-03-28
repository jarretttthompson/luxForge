"""Tests for the simulator console."""

import pytest

from src.console.simulator import SimulatorConsole
from src.console.types import ConsoleCapability, ConsoleCommand


class TestSimulatorConsole:
    def test_name(self):
        sim = SimulatorConsole()
        assert sim.name == "Simulator Console"

    def test_initial_faders_at_zero(self):
        sim = SimulatorConsole(num_playbacks=3)
        state = sim.get_state()
        for key, val in state["faders"].items():
            assert val == 0.0

    def test_fader_command_updates_state(self):
        sim = SimulatorConsole()
        cmd = ConsoleCommand(target="playback.1.fader", value=0.8, command_type=ConsoleCapability.PLAYBACK_FADER)
        messages = sim.translate(cmd)
        assert messages == []  # No real protocol messages
        assert sim.get_fader("playback.1.fader") == 0.8

    def test_go_command_activates_cuelist(self):
        sim = SimulatorConsole()
        cmd = ConsoleCommand(target="playback.2.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO)
        sim.translate(cmd)
        state = sim.get_state()
        assert state["cuelists"]["playback.2"] is True

    def test_stop_command_deactivates_cuelist(self):
        sim = SimulatorConsole()
        sim.translate(ConsoleCommand(target="playback.1.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO))
        sim.translate(ConsoleCommand(target="playback.1.stop", value=1.0, command_type=ConsoleCapability.PLAYBACK_STOP))
        state = sim.get_state()
        assert state["cuelists"]["playback.1"] is False

    def test_command_history_tracked(self):
        sim = SimulatorConsole()
        sim.translate(ConsoleCommand(target="playback.1.fader", value=0.5, command_type=ConsoleCapability.PLAYBACK_FADER))
        sim.translate(ConsoleCommand(target="playback.2.go", value=1.0, command_type=ConsoleCapability.PLAYBACK_GO))
        state = sim.get_state()
        assert len(state["last_commands"]) == 2

    def test_reset_clears_state(self):
        sim = SimulatorConsole()
        sim.translate(ConsoleCommand(target="playback.1.fader", value=0.9, command_type=ConsoleCapability.PLAYBACK_FADER))
        sim.reset()
        assert sim.get_fader("playback.1.fader") == 0.0
        state = sim.get_state()
        assert len(state["last_commands"]) == 0

    def test_output_parameters_generated(self):
        sim = SimulatorConsole(num_playbacks=5)
        params = sim.get_output_parameters()
        assert len(params) == 15  # 5 * 3 (fader, go, stop)
        assert "simulator.playback.1.fader" in params

    def test_capabilities(self):
        sim = SimulatorConsole()
        caps = sim.get_capabilities()
        assert ConsoleCapability.PLAYBACK_FADER in caps
        assert ConsoleCapability.PLAYBACK_GO in caps
