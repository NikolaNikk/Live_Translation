from dataclasses import dataclass
import re


@dataclass
class TranscriptEvent:

    start_ms: int
    end_ms: int
    text: str

    @property
    def start_seconds(self) -> float:
        return self.start_ms / 1000.0

    @property
    def end_seconds(self) -> float:
        return self.end_ms / 1000.0


def parse_transcript_line(line: str) -> TranscriptEvent | None:

    if not line:
        return None

    line = line.strip()

    if not line:
        return None

    match = re.match(r"^(\d+)\s+(\d+)\s+(.*)$", line)

    if not match:
        return None

    start_ms = int(match.group(1))
    end_ms = int(match.group(2))
    text = match.group(3).strip()

    if not text:
        return None

    return TranscriptEvent(
        start_ms=start_ms,
        end_ms=end_ms,
        text=text,
    )