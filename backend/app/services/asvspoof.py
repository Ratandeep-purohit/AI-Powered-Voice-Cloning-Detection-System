"""ASVspoof 2019 LA protocol parsing for Phase 05.

The parser reads the official protocol text files without requiring the
large ASVspoof dataset to be copied into the repository. It only resolves
metadata; audio loading and ML inference are handled by later phases.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ASVspoofProtocolError(ValueError):
    """Raised when an ASVspoof protocol cannot be parsed safely."""


LABEL_MAP = {
    "bonafide": "REAL",
    "spoof": "SPOOF",
}

PROTOCOL_FILES = {
    "train": "ASVspoof2019.LA.cm.train.trn.txt",
    "dev": "ASVspoof2019.LA.cm.dev.trl.txt",
    "eval": "ASVspoof2019.LA.cm.eval.trl.txt",
}


@dataclass(frozen=True, slots=True)
class ASVspoofProtocolEntry:
    """One parsed ASVspoof 2019 LA logical access protocol row."""

    speaker_id: str
    audio_id: str
    label: str


class ASVspoofProtocolParser:
    """Parse ASVspoof 2019 LA CM protocol files."""

    def __init__(self, dataset_root: str | Path) -> None:
        root_value = str(dataset_root).strip()
        if not root_value:
            raise ASVspoofProtocolError("ASVspoof dataset root must not be empty.")
        self.dataset_root = Path(root_value).expanduser().resolve()

    def protocol_path(self, split: str) -> Path:
        """Return the protocol file path for a supported split."""
        normalized_split = split.strip().lower()
        try:
            filename = PROTOCOL_FILES[normalized_split]
        except KeyError as exc:
            supported = ", ".join(PROTOCOL_FILES)
            raise ASVspoofProtocolError(
                f"Unsupported ASVspoof split '{split}'. Supported splits: {supported}."
            ) from exc
        return self.dataset_root / "ASVspoof2019_LA_asv_protocols" / filename

    def parse_file(self, protocol_path: str | Path) -> list[ASVspoofProtocolEntry]:
        """Parse one ASVspoof CM protocol file."""
        path = Path(protocol_path).expanduser().resolve()
        if not path.is_file():
            raise ASVspoofProtocolError(f"ASVspoof protocol file does not exist: {path}")

        entries: list[ASVspoofProtocolEntry] = []
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue

                fields = line.split()
                if len(fields) != 5:
                    raise ASVspoofProtocolError(
                        f"Invalid protocol row at {path}:{line_number}: expected 5 fields, got {len(fields)}."
                    )

                speaker_id, audio_id, _attack_system, _attack_version, raw_label = fields
                label_key = raw_label.lower()
                try:
                    label = LABEL_MAP[label_key]
                except KeyError as exc:
                    raise ASVspoofProtocolError(
                        f"Unsupported ASVspoof label '{raw_label}' at {path}:{line_number}."
                    ) from exc

                entries.append(
                    ASVspoofProtocolEntry(
                        speaker_id=speaker_id,
                        audio_id=audio_id,
                        label=label,
                    )
                )

        return entries

    def load_split(self, split: str) -> list[ASVspoofProtocolEntry]:
        """Parse one of the train, dev, or eval protocol files."""
        return self.parse_file(self.protocol_path(split))

    def count_labels(self, entries: list[ASVspoofProtocolEntry]) -> dict[str, int]:
        """Return deterministic REAL/SPOOF counts for parsed entries."""
        counts = {"REAL": 0, "SPOOF": 0}
        for entry in entries:
            counts[entry.label] += 1
        return counts
