# audio/vad.py

import numpy as np
import torch
from silero_vad import load_silero_vad, get_speech_timestamps


class SpeechDetector:

    def __init__(
        self,
        sample_rate: int = 16000,
        threshold: float = 0.45,
        min_speech_duration_ms: int = 150,
        min_silence_duration_ms: int = 800,
        speech_pad_ms: int = 300,

    ):
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms

        print("Loading Silero VAD...")
        self.model = load_silero_vad()
        print("Silero VAD loaded.")

    def is_speech(self, audio_16k: np.ndarray) -> bool:

        if audio_16k is None:
            return False

        if len(audio_16k) == 0:
            return False

        audio_16k = np.asarray(audio_16k, dtype=np.float32)
        audio_16k = np.clip(audio_16k, -1.0, 1.0)

        energy = np.mean(audio_16k ** 2)
        if energy < 0.00001:
            return False

        wav = torch.from_numpy(audio_16k)

        with torch.no_grad():
            speech_timestamps = get_speech_timestamps(
                wav,
                self.model,
                sampling_rate=self.sample_rate,
                threshold=self.threshold,
                min_speech_duration_ms=self.min_speech_duration_ms,
                min_silence_duration_ms=self.min_silence_duration_ms,
                speech_pad_ms=self.speech_pad_ms,
                return_seconds=False,
            )

        return len(speech_timestamps) > 0