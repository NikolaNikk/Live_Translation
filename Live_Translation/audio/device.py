# audio/devices.py

import sounddevice as sd


def list_audio_devices():
    """
    Prints all audio devices on your system.
    Shows which devices can be used as microphones.
    """

    devices = sd.query_devices()

    print("\nAvailable audio devices:\n")

    for index, device in enumerate(devices):
        name = device["name"]
        input_channels = device["max_input_channels"]
        output_channels = device["max_output_channels"]
        default_sample_rate = int(device["default_samplerate"])

        print(f"{index}: {name}")
        print(f"   Input channels:  {input_channels}")
        print(f"   Output channels: {output_channels}")
        print(f"   Sample rate:     {default_sample_rate}")

        if input_channels > 0:
            print("   ✅ Can be used as microphone")
        else:
            print("   ❌ Not a microphone input")

        print()


def list_input_devices_only():
    """
    Prints only devices that can be used as microphone input.
    """

    devices = sd.query_devices()

    print("\nMicrophone / input devices only:\n")

    for index, device in enumerate(devices):
        if device["max_input_channels"] > 0:
            name = device["name"]
            input_channels = device["max_input_channels"]
            default_sample_rate = int(device["default_samplerate"])

            print(f"{index}: {name}")
            print(f"   Input channels: {input_channels}")
            print(f"   Sample rate:    {default_sample_rate}")
            print()


if __name__ == "__main__":
    list_audio_devices()
    list_input_devices_only()