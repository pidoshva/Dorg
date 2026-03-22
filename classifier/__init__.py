"""
Multi-signal file classifier.
Public API: classify_file(path) -> FileClassification
"""

from pathlib import Path
from .signals import FileClassification, AnalysisContext, Signal
from .capabilities import ClassifierCapabilities
from .analyzers import run_pipeline
from .fusion import fuse_signals

_capabilities = None


def get_capabilities() -> ClassifierCapabilities:
    global _capabilities
    if _capabilities is None:
        _capabilities = ClassifierCapabilities()
    return _capabilities


def classify_file(path: Path) -> FileClassification:
    """Classify a single file using all available analyzers."""
    import os
    ctx = AnalysisContext(
        path=path,
        stat=os.stat(path),
        magic_type=None,
        true_category=None,
        signals=[],
        metadata={},
    )
    caps = get_capabilities()
    run_pipeline(ctx, caps)
    return fuse_signals(ctx)
