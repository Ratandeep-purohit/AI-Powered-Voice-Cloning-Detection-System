"""ASVspoof 2019 LA audio-path resolution for Phase 05."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.asvspoof import ASVspoofProtocolEntry, ASVspoofProtocolError, ASVspoofProtocolParser


SPLIT_AUDIO_DIRECTORIES = {
    "train": "ASVspoof2019_LA_train/flac",
    "dev": "ASVspoof2019_LA_dev/flac",
    "eval": "ASVspoof2019_LA_eval/flac",
}


@dataclass(frozen=True, slots=True)
class ASVspoofAudioResolution:
    """Resolved dataset audio path for one protocol entry."""

    split: str
    speaker_id: str
    audio_id: str
    label: str
    path: Path


class ASVspoofDatasetResolver:
    """Resolve ASVspoof protocol entries to their local FLAC files."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.parser = ASVspoofProtocolParser(dataset_root)
        self.dataset_root = self.parser.dataset_root

    def audio_path(self, split: str, audio_id: str) -> Path:
        """Build the expected FLAC path without requiring the file to exist."""
        normalized_split = split.strip().lower()
        try:
            directory = SPLIT_AUDIO_DIRECTORIES[normalized_split]
        except KeyError as exc:
            supported = ", ".join(SPLIT_AUDIO_DIRECTORIES)
            raise ASVspoofProtocolError(
                f"Unsupported ASVspoof split '{split}'. Supported splits: {supported}."
            ) from exc

        safe_audio_id = audio_id.strip()
        if not safe_audio_id or Path(safe_audio_id).name != safe_audio_id:
            raise ASVspoofProtocolError(f"Invalid ASVspoof audio ID: '{audio_id}'.")
        if Path(safe_audio_id).suffix.lower() == ".flac":
            safe_audio_id = Path(safe_audio_id).stem

        return (self.dataset_root / directory / f"{safe_audio_id}.flac").resolve()

    def resolve_entry(self, split: str, entry: ASVspoofProtocolEntry) -> ASVspoofAudioResolution:
        """Resolve one protocol entry and require its audio file to exist."""
        path = self.audio_path(split, entry.audio_id)
        if not path.is_file():
            raise ASVspoofProtocolError(
                f"ASVspoof audio file does not exist for {split}/{entry.audio_id}: {path}"
            )
        return ASVspoofAudioResolution(
            split=split.strip().lower(),
            speaker_id=entry.speaker_id,
            audio_id=entry.audio_id,
            label=entry.label,
            path=path,
        )

    def resolve_split(self, split: str, entries: list[ASVspoofProtocolEntry] | None = None) -> list[ASVspoofAudioResolution]:
        """Resolve every entry in a split, failing fast on a missing audio file."""
        protocol_entries = entries if entries is not None else self.parser.load_split(split)
        return [self.resolve_entry(split, entry) for entry in protocol_entries]
