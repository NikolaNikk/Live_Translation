# asr/client.py

import socket
import threading
import time
import queue

import numpy as np
from scipy.signal import resample_poly

from audio.input import get_device, create_stream
from audio.vad import SpeechDetector
from utils.logger import log
from asr.parser import parse_transcript_line

# =========================
# CONFIG
# =========================
DEVICE_INDEX = 25
CHANNELS = 1

device_info = get_device(DEVICE_INDEX)
INPUT_SAMPLE_RATE = int(device_info["default_samplerate"])

SERVER_SAMPLE_RATE = 16000

# Main audio chunk size.
# Higher = more stable, more delay.
# Lower = faster, but more chance of cutting words.
CHUNK_SECONDS = 1.2

# Microphone callback size.
# 0.2 = sounddevice gives us about 200 ms of audio each callback.
BLOCKSIZE = int(INPUT_SAMPLE_RATE * 0.2)

# Keep a little audio before/after chunks.
# This helps avoid cutting words at chunk boundaries.
PRE_ROLL_SECONDS = 0.3
OVERLAP_SECONDS = 0.15

HOST = "127.0.0.1"
PORT = 43001

# =========================
# STATE
# =========================
sock = None
stop_event = threading.Event()

audio_queue = queue.Queue(maxsize=50)

audio_buffer = np.array([], dtype=np.float32)

# Convert seconds to samples at the microphone sample rate.
PRE_ROLL_SAMPLES = int(INPUT_SAMPLE_RATE * PRE_ROLL_SECONDS)
OVERLAP_SAMPLES = int(INPUT_SAMPLE_RATE * OVERLAP_SECONDS)

# Create Silero VAD once.
# These settings are softer so it is less likely to cut start/end words.
speech_detector = SpeechDetector(
    threshold=0.35,
    min_speech_duration_ms=150,
    min_silence_duration_ms=800,
    speech_pad_ms=300,
)


# =========================
# AUDIO CALLBACK
# =========================
def audio_callback(indata, frames, time_info, status):
    """
    Called automatically by sounddevice whenever microphone audio arrives.

    Keep this light:
    - copy audio
    - put it into the queue
    - do not run VAD here
    - do not send socket data here
    """

    if status:
        log(f"Audio status: {status}")

    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        # Drop audio instead of blocking the real-time callback.
        pass


# =========================
# SENDER THREAD
# =========================
def sender_thread():
    """
    Takes microphone audio from the queue,
    builds a chunk,
    resamples it to 16 kHz,
    checks it with Silero VAD,
    and sends only speech audio to SimulStreaming.
    """

    global sock, audio_buffer

    required_samples = int(INPUT_SAMPLE_RATE * CHUNK_SECONDS)

    while not stop_event.is_set():
        try:
            block = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        # If this appears often, the client is falling behind.
        if audio_queue.qsize() > 20:
            log(f"WARNING: audio queue backlog: {audio_queue.qsize()}")

        # block shape is usually: (frames, channels)
        # for mono, this is something like: (8820, 1)
        mono = block[:, 0].astype(np.float32)

        # Add this microphone block to the current audio buffer.
        audio_buffer = np.concatenate([audio_buffer, mono])

        # Wait until we have enough audio for one chunk.
        if len(audio_buffer) < required_samples:
            continue

        try:
            # Convert from microphone sample rate, usually 44100 Hz,
            # to 16000 Hz for Silero VAD and SimulStreaming.
            audio_16k = resample_poly(
                audio_buffer,
                SERVER_SAMPLE_RATE,
                INPUT_SAMPLE_RATE
            ).astype(np.float32)

            audio_16k = np.clip(audio_16k, -1.0, 1.0)

            # =========================
            # SILERO VAD GATE
            # =========================
            has_speech = speech_detector.is_speech(audio_16k)

            if not has_speech:
                # Music, silence, or noise:
                # do not send to SimulStreaming.
                #
                # Keep a tiny pre-roll instead of clearing everything.
                # This helps catch the beginning of speech that starts
                # right after a music/silence section.
                audio_buffer = audio_buffer[-PRE_ROLL_SAMPLES:]
                continue

            # Convert float32 audio [-1.0, 1.0]
            # to int16 PCM because SimulStreaming expects raw S16_LE audio.
            pcm16 = (audio_16k * 32767.0).astype("<i2")

            sock.sendall(pcm16.tobytes())

            # Keep a tiny overlap after sending.
            # This helps avoid cutting words at the end of a chunk.
            audio_buffer = audio_buffer[-OVERLAP_SAMPLES:]

        except Exception as e:
            log(f"Sender error: {e}")
            stop_event.set()
            break


# =========================
# RECEIVER THREAD
# =========================
def receive_text():
    """
    Receives transcript text from SimulStreaming,
    parses it, filters repeated output, and prints clean text.
    """

    global sock

    socket_buffer = b""
    last_text = ""
    repeat_counter = 0

    while not stop_event.is_set():
        try:
            data = sock.recv(4096)

            if not data:
                log("Server closed connection.")
                stop_event.set()
                break

            socket_buffer += data

            while b"\n" in socket_buffer:
                raw_line, socket_buffer = socket_buffer.split(b"\n", 1)
                raw_line = raw_line.decode("utf-8", errors="ignore").strip()

                if not raw_line:
                    continue

                event = parse_transcript_line(raw_line)

                if event is None:
                    continue

                text = event.text.strip()

                if not text:
                    continue

                # Basic repeated-output protection.
                # Important: compare parsed text, not raw timestamp line.
                if text == last_text:
                    repeat_counter += 1
                else:
                    repeat_counter = 0

                if repeat_counter > 3:
                    continue

                log(text)
                last_text = text

        except Exception as e:
            log(f"Receiver error: {e}")
            stop_event.set()
            break


# =========================
# MAIN
# =========================
def main():
    global sock

    log(f"Device: {device_info['name']}")
    log(f"Sample rate: {INPUT_SAMPLE_RATE}")
    log(f"Channels: {CHANNELS}")
    log(f"Chunk seconds: {CHUNK_SECONDS}")
    log(f"Pre-roll seconds: {PRE_ROLL_SECONDS}")
    log(f"Overlap seconds: {OVERLAP_SECONDS}")

    sock = socket.create_connection((HOST, PORT))

    log("Connected to ASR server")
    log("Listening...")

    threading.Thread(target=sender_thread, daemon=True).start()
    threading.Thread(target=receive_text, daemon=True).start()

    stream = create_stream(
        device_index=DEVICE_INDEX,
        samplerate=INPUT_SAMPLE_RATE,
        blocksize=BLOCKSIZE,
        channels=CHANNELS,
        callback=audio_callback,
    )

    try:
        with stream:
            while not stop_event.is_set():
                time.sleep(0.1)

    except KeyboardInterrupt:
        log("Stopped")

    finally:
        stop_event.set()

        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    main()