# AR Glasses Software

Prototype software for live transcription and future AR smart glasses features.

## Project Layout

- `Live_Translation/` - main application code
- `Live_Translation/asr/` - speech recognition client and server integration
- `Live_Translation/audio/` - microphone input, device handling, and VAD
- `Live_Translation/subtitles/` - subtitle output and overlay logic
- `Live_Translation/translation/` - translation helpers
- `Live_Translation/vision/` - future vision features
- `Live_Translation/SimulStreaming/` - SimulStreaming integration

## Setup

Create a virtual environment and install the SimulStreaming dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r Live_Translation\SimulStreaming\requirements_whisper.txt
```

Additional translation dependencies are listed in:

```text
Live_Translation\SimulStreaming\requirements_translate.txt
```

## Run

```powershell
python Live_Translation\main.py
```

## Notes

Large model checkpoints, virtual environments, generated audio, cache files, and local IDE settings are intentionally excluded from git. Download or generate those locally as needed.
