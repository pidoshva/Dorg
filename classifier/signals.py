"""Core data structures for the classification pipeline."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import os


@dataclass
class Signal:
    """One piece of evidence from an analyzer."""
    name: str
    value: Any
    category_votes: dict[str, float]  # subtype -> confidence contribution


@dataclass
class FileClassification:
    """Final classification result for a file."""
    category: str       # "image", "video", etc.
    subtype: str        # "image/screenshot", "audio/music", etc.
    confidence: float   # 0.0 - 1.0
    signals: list[Signal]
    metadata: dict      # extracted metadata (dimensions, duration, dates, etc.)

    @property
    def subtype_name(self) -> str:
        """Get just the subtype part after the slash."""
        return self.subtype.split("/", 1)[1] if "/" in self.subtype else self.subtype


@dataclass
class AnalysisContext:
    """Shared state passed through the analyzer pipeline."""
    path: Path
    stat: os.stat_result
    magic_type: Optional[str] = None
    true_category: Optional[str] = None
    signals: list[Signal] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def extension(self) -> str:
        """Lowercase extension without dot."""
        return self.path.suffix.lstrip(".").lower()

    @property
    def filename(self) -> str:
        return self.path.name

    @property
    def file_size(self) -> int:
        return self.stat.st_size
