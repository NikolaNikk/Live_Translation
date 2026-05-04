import queue
import socket
import threading
import time

import numpy as np
import sounddevice as sd
from scipy.signal import resample_poly

# =========================
# AUDIO SETTINGS
# =========================
DEVICE_INDEX = 25
CHANNELS = 1

device_info = sd.query_devices(DEVICE_INDEX)
INPUT_SAMPLE_RATE = int(device_info["default_samplerate"])

SERVER_SAMPLE_RATE = 16000

CHUNK_SECONDS = 1
BLOCKSIZE = int(INPUT_SAMPLE_RATE * 0.2)

# =========================
# SERVER SETTINGS
# =========================
HOST = "127.0.0.1"
PORT = 43001

# =========================
# STATE
# =========================
sock = None
stop_event = threading.Event()

audio_queue = queue.Queue(maxsize=50)

audio_buffer = np.array([], dtype=np.float32)
last_voice_time = time.time()

# =========================
# TIMER (ADDED)
# =========================
start_time = None

# =========================
# AUDIO CALLBACK
# =========================
def audio_callback(indata, frames, time_info, status):
    if status:
        print("Audio status:", status)

    try:
        audio_queue.put_nowait(indata.copy())
    except queue.Full:
        pass


# =========================
# SENDER THREAD
# =========================
def sender_thread():
    global sock, audio_buffer, last_voice_time

    SILENCE_THRESHOLD = 0.003
    RESET_SILENCE_SEC = 1.5

    while not stop_event.is_set():
        try:
            block = audio_queue.get(timeout=0.1)
        except queue.Empty:
            continue

        mono = block[:, 0]
        volume = np.abs(mono).mean()

        if volume < SILENCE_THRESHOLD:
            if time.time() - last_voice_time > RESET_SILENCE_SEC:
                audio_buffer = np.array([], dtype=np.float32)
            continue
        else:
            last_voice_time = time.time()

        audio_buffer = np.concatenate([audio_buffer, mono])

        if len(audio_buffer) < INPUT_SAMPLE_RATE * CHUNK_SECONDS:
            continue

        try:
            audio_16k = resample_poly(
                audio_buffer,
                SERVER_SAMPLE_RATE,
                INPUT_SAMPLE_RATE
            ).astype(np.float32)

            audio_16k = np.clip(audio_16k, -1.0, 1.0)

            pcm16 = (audio_16k * 32767.0).astype("<i2")

            sock.sendall(pcm16.tobytes())

            audio_buffer = np.array([], dtype=np.float32)

        except Exception as e:
            print("Sender error:", e)
            stop_event.set()
            break


# =========================
# RECEIVER THREAD
# =========================
def receive_text():
    global sock

    buffer = b""
    last_line = ""
    repeat_counter = 0

    while not stop_event.is_set():
        try:
            data = sock.recv(4096)
            if not data:
                print("Server closed connection.")
                stop_event.set()
                break

            buffer += data

            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                line = line.decode("utf-8", errors="ignore").strip()

                if not line:
                    continue

                if line == last_line:
                    repeat_counter += 1
                else:
                    repeat_counter = 0

                if repeat_counter > 3:
                    continue

                if len(line) < 5:
                    continue

                print(line)
                last_line = line

        except Exception as e:
            print("Receiver error:", e)
            stop_event.set()
            break


# =========================
# MAIN
# =========================
def main():
    global sock, start_time

    start_time = time.time()  # START TIMER

    print(f"Device: {device_info['name']}")
    print(f"Sample rate: {INPUT_SAMPLE_RATE}")

    sock = socket.create_connection((HOST, PORT))

    print("Connected to ASR server")
    print("Listening...")

    threading.Thread(target=sender_thread, daemon=True).start()
    threading.Thread(target=receive_text, daemon=True).start()

    try:
        with sd.InputStream(
            samplerate=INPUT_SAMPLE_RATE,
            blocksize=BLOCKSIZE,
            device=DEVICE_INDEX,
            channels=CHANNELS,
            dtype="float32",
            latency="low",
            callback=audio_callback,
        ):
            while not stop_event.is_set():
                time.sleep(0.1)

    except KeyboardInterrupt:
        print("Stopped")

    finally:
        stop_event.set()

        # CLOSE SOCKET
        try:
            sock.close()
        except:
            pass

        # TIMER OUTPUT (ADDED)
        if start_time is not None:
            total = time.time() - start_time
            print(f"\n🕒 Session runtime: {total:.2f} seconds ({total/60:.2f} minutes)")


if __name__ == "__main__":
    main()