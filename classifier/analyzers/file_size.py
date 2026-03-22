"""Size-based heuristics per file category."""

from ..signals import AnalysisContext, Signal
from ..taxonomy import *  # noqa: F403, F401


def analyze(ctx: AnalysisContext):
    size = ctx.file_size
    cat = ctx.true_category

    if cat == "image":
        _analyze_image_size(ctx, size)
    elif cat == "video":
        _analyze_video_size(ctx, size)
    elif cat == "audio":
        _analyze_audio_size(ctx, size)


def _analyze_image_size(ctx: AnalysisContext, size: int):
    votes = {}
    if size < 10_000:  # < 10KB
        votes = {IMAGE_ICON: 0.4, IMAGE_THUMBNAIL: 0.2}
    elif size < 100_000:  # 10-100KB
        votes = {IMAGE_MEME: 0.15, IMAGE_DIAGRAM: 0.15, IMAGE_THUMBNAIL: 0.1}
    elif size < 1_000_000:  # 100KB-1MB
        votes = {}  # neutral
    elif size < 5_000_000:  # 1-5MB
        votes = {IMAGE_PHOTO_CAMERA: 0.1, IMAGE_PHOTO_PHONE: 0.1}
    elif size < 15_000_000:  # 5-15MB
        votes = {IMAGE_PHOTO_CAMERA: 0.2}
    elif size < 50_000_000:  # 15-50MB
        votes = {IMAGE_SCAN: 0.2, IMAGE_PHOTO_EDITED: 0.15}
    else:  # > 50MB
        votes = {IMAGE_PHOTO_RAW: 0.4}

    if votes:
        ctx.signals.append(Signal("image_file_size", size, votes))


def _analyze_video_size(ctx: AnalysisContext, size: int):
    votes = {}
    if size < 5_000_000:  # < 5MB
        votes = {VIDEO_GIF_VIDEO: 0.3, VIDEO_CLIP_SHORT: 0.2}
    elif size < 50_000_000:  # 5-50MB
        votes = {VIDEO_CLIP_SHORT: 0.15}
    elif size < 1_000_000_000:  # 50MB-1GB
        votes = {VIDEO_CAMERA: 0.1}
    elif size < 4_000_000_000:  # 1-4GB
        votes = {VIDEO_MOVIE: 0.2, VIDEO_DOWNLOADED: 0.15}
    else:  # > 4GB
        votes = {VIDEO_MOVIE: 0.3}

    if votes:
        ctx.signals.append(Signal("video_file_size", size, votes))


def _analyze_audio_size(ctx: AnalysisContext, size: int):
    votes = {}
    if size < 200_000:  # < 200KB
        votes = {AUDIO_SOUND_EFFECT: 0.4}
    elif size < 2_000_000:  # 200KB-2MB
        votes = {AUDIO_VOICE_MEMO: 0.2, AUDIO_RINGTONE: 0.15}
    elif size < 15_000_000:  # 2-15MB
        votes = {AUDIO_MUSIC: 0.2}
    elif size < 100_000_000:  # 15-100MB
        votes = {AUDIO_PODCAST: 0.15, AUDIO_MUSIC: 0.1}
    else:  # > 100MB
        votes = {AUDIO_PODCAST: 0.3}

    if votes:
        ctx.signals.append(Signal("audio_file_size", size, votes))
