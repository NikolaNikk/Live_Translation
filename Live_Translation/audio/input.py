
import sounddevice as sd


def get_device(device_index):
    return sd.query_devices(device_index)


def create_stream(device_index, samplerate, blocksize, channels, callback):
    return sd.InputStream(
        device=device_index,
        samplerate=samplerate,
        blocksize=blocksize,
        channels=channels,
        dtype="float32",
        latency="low",
        callback=callback,
    )