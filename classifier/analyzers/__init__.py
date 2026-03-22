"""Analyzer pipeline runner."""

from ..signals import AnalysisContext
from ..capabilities import ClassifierCapabilities
from . import magic_bytes, file_size, filename_patterns, image, video, audio, document, code


def run_pipeline(ctx: AnalysisContext, caps: ClassifierCapabilities):
    """Run all relevant analyzers on the file."""
    # Magic bytes always runs first — determines true category
    magic_bytes.analyze(ctx)

    # These always run
    file_size.analyze(ctx)
    filename_patterns.analyze(ctx)

    # Category-specific analyzers
    cat = ctx.true_category
    if cat == "image" and caps.has_pillow:
        image.analyze(ctx)
    elif cat == "video":
        video.analyze(ctx, caps)
    elif cat == "audio":
        audio.analyze(ctx, caps)
    elif cat == "document":
        document.analyze(ctx, caps)

    # Code analyzer runs on text files
    if cat in ("code", "text", None):
        code.analyze(ctx)
