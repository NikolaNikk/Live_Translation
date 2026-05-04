import sounddevice as sd
import soundfile as sf

# =========================
# SETTINGS
# =========================
DEVICE_INDEX = 25          # change this if needed
CHANNELS = 1               # mono
DURATION = 30              # seconds
OUTPUT_FILE = "test_audio.wav"

# Use the real/default sample rate of the selected device
device_info = sd.query_devices(DEVICE_INDEX)
SAMPLE_RATE = int(device_info["default_samplerate"])


def main():
    print(f"Using device: {device_info['name']}")
    print(f"Sample rate: {SAMPLE_RATE}")
    print(f"Recording for {DURATION} seconds...")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="float32",
        device=DEVICE_INDEX
    )

    sd.wait()

    sf.write(OUTPUT_FILE, audio, SAMPLE_RATE)

    print("Recording finished.")
    print(f"Saved as: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()