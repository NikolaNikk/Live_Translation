import numpy as np
import soundfile as sf
import torch
from scipy.signal import resample_poly
from silero_vad import load_silero_vad, get_speech_timestamps

AUDIO_FILE = "test_audio.wav"
TARGET_SAMPLE_RATE = 16000

# 1. Load Silero VAD model
model = load_silero_vad()

# 2. Load audio using soundfile instead of silero's read_audio()
audio, original_sample_rate = sf.read(AUDIO_FILE)

print(f"Original sample rate: {original_sample_rate}")
print(f"Audio shape: {audio.shape}")

# 3. If stereo, convert to mono
if audio.ndim > 1:
    audio = audio.mean(axis=1)

# 4. Convert to float32
audio = audio.astype(np.float32)

# 5. Resample to 16 kHz if needed
if original_sample_rate != TARGET_SAMPLE_RATE:
    audio = resample_poly(
        audio,
        TARGET_SAMPLE_RATE,
        original_sample_rate
    ).astype(np.float32)

# 6. Make sure audio is inside safe range
audio = np.clip(audio, -1.0, 1.0)

# 7. Convert numpy array to torch tensor
wav = torch.from_numpy(audio)

# 8. Run VAD
speech_timestamps = get_speech_timestamps(
    wav,
    model,
    sampling_rate=TARGET_SAMPLE_RATE,
    return_seconds=True
)

print("\nSpeech timestamps:")
for ts in speech_timestamps:
    print(ts)