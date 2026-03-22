"""Weighted scoring engine that combines signals into a final classification."""

import math
from collections import defaultdict
from .signals import AnalysisContext, FileClassification, Signal
from .taxonomy import OTHER_UNKNOWN, OTHER_EMPTY


def fuse_signals(ctx: AnalysisContext) -> FileClassification:
    """Combine all signals into a final FileClassification."""
    # Handle empty files
    if ctx.file_size == 0:
        return FileClassification(
            category="other",
            subtype=OTHER_EMPTY,
            confidence=1.0,
            signals=ctx.signals,
            metadata=ctx.metadata,
        )

    base_category = ctx.true_category or "other"

    # Collect votes for subtypes within the correct category
    subtype_scores: dict[str, float] = defaultdict(float)

    for signal in ctx.signals:
        for subtype, weight in signal.category_votes.items():
            if subtype.startswith(base_category + "/"):
                subtype_scores[subtype] += weight

    if not subtype_scores:
        return FileClassification(
            category=base_category,
            subtype=f"{base_category}/generic",
            confidence=0.3,
            signals=ctx.signals,
            metadata=ctx.metadata,
        )

    # Hard override rules
    for signal in ctx.signals:
        # Animated GIF is definitive
        if signal.name == "animated_frames":
            from .taxonomy import IMAGE_GIF_ANIMATED
            return FileClassification(
                category="image",
                subtype=IMAGE_GIF_ANIMATED,
                confidence=0.95,
                signals=ctx.signals,
                metadata=ctx.metadata,
            )

    # Select winner
    best_subtype = max(subtype_scores, key=subtype_scores.get)
    best_score = subtype_scores[best_subtype]

    # Minimum threshold
    if best_score < 0.15:
        return FileClassification(
            category=base_category,
            subtype=f"{base_category}/generic",
            confidence=0.25,
            signals=ctx.signals,
            metadata=ctx.metadata,
        )

    # Runner up for margin calculation
    sorted_scores = sorted(subtype_scores.values(), reverse=True)
    runner_up_score = sorted_scores[1] if len(sorted_scores) > 1 else 0.0
    margin = best_score - max(runner_up_score, 0)

    # Sigmoid normalization: maps positive scores to 0.5-1.0
    confidence = 1.0 / (1.0 + math.exp(-1.5 * best_score))
    # Boost for clear winners
    confidence = min(1.0, confidence + margin * 0.1)

    return FileClassification(
        category=base_category,
        subtype=best_subtype,
        confidence=round(confidence, 3),
        signals=ctx.signals,
        metadata=ctx.metadata,
    )
