#!/usr/bin/env python3
"""List all available audio input devices."""

import sys


def main():
    try:
        from src.audio.capture import AudioCapture
    except ImportError:
        print("Error: Install the project first with 'pip install -e .'")
        sys.exit(1)

    devices = AudioCapture.list_devices()

    if not devices:
        print("No audio input devices found.")
        print("Tip: The audio simulator will be used by default when no hardware is connected.")
        return

    print(f"Found {len(devices)} audio input device(s):\n")
    for dev in devices:
        print(f"  [{dev['index']}] {dev['name']}")
        print(f"      Channels: {dev['channels']}, Default Sample Rate: {dev['sample_rate']} Hz")
        print()

    print("To use a specific device, set AUDIO_DEVICE_INDEX in your .env file.")


if __name__ == "__main__":
    main()
