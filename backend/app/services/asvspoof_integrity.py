"""ASVspoof 2019 LA dataset integrity validation for Phase 05."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.services.asvspoof import ASVspoofProtocolEntry, ASVspoofProtocolError, ASVspoofProtocolParser
from app.services.asvspoof_dataset import ASVspoofDatasetResolver


@dataclass(frozen=True, slots=True)
class ASVspoofSplitIntegrity:
    """Integrity summary for one ASVspoof split."""

    split: str
    total: int
    real: int
    spoof: int
    missing: int
    duplicate_audio_ids: int

    @property
    def passed(self) -> bool:
        return self.missing == 0 and self.duplicate_audio_ids == 0


@dataclass(frozen=True, slots=True)
class ASVspoofIntegrityReport:
    """Complete integrity report for train/dev/eval."""

    splits: tuple[ASVspoofSplitIntegrity, ...]

    @property
    def passed(self) -> bool:
        return all(split.passed for split in self.splits)


class ASVspoofIntegrityValidator:
    """Validate protocol entries against the expected local FLAC files."""

    def __init__(self, dataset_root: str | Path) -> None:
        self.parser = ASVspoofProtocolParser(dataset_root)
        self.resolver = ASVspoofDatasetResolver(dataset_root)

    def validate_split(self, split: str) -> ASVspoofSplitIntegrity:
        entries = self.parser.load_split(split)
        counts = self.parser.count_labels(entries)
        seen: set[str] = set()
        duplicate_count = 0
        missing_count = 0

        for entry in entries:
            if entry.audio_id in seen:
                duplicate_count += 1
            else:
                seen.add(entry.audio_id)

            if not self.resolver.audio_path(split, entry.audio_id).is_file():
                missing_count += 1

        normalized_split = split.strip().lower()
        return ASVspoofSplitIntegrity(
            split=normalized_split,
            total=len(entries),
            real=counts["REAL"],
            spoof=counts["SPOOF"],
            missing=missing_count,
            duplicate_audio_ids=duplicate_count,
        )

    def validate(self) -> ASVspoofIntegrityReport:
        return ASVspoofIntegrityReport(
            splits=tuple(self.validate_split(split) for split in ("train", "dev", "eval"))
        )
