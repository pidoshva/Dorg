"""Video analysis: resolution, duration, codec via ffprobe."""

import json
import subprocess
from ..signals import AnalysisContext, Signal
from ..capabilities import ClassifierCapabilities
from ..taxonomy import *  # noqa: F403, F401

# Reuse screen resolution set from image analyzer
from .image import SCREEN_RESOLUTIONS


def _probe(path: str) -> dict | None:
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", "-show_streams", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        pass
    return None


def _matches_screen_res(w: int, h: int) -> bool:
    for sw, sh in SCREEN_RESOLUTIONS:
        if abs(w - sw) <= 2 and abs(h - sh) <= 2:
            return True
        if abs(w - sh) <= 2 and abs(h - sw) <= 2:
            return True
    return False


def analyze(ctx: AnalysisContext, caps: ClassifierCapabilities):
    """Analyze video file."""
    if not caps.has_ffprobe:
        return  # file_size analyzer handles fallback

    info = _probe(ctx.path)
    if not info:
        return

    # Find video stream
    video_stream = None
    audio_stream = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "video" and video_stream is None:
            video_stream = stream
        elif stream.get("codec_type") == "audio" and audio_stream is None:
            audio_stream = stream

    fmt = info.get("format", {})

    # Duration
    duration = None
    try:
        duration = float(fmt.get("duration", 0))
        ctx.metadata["duration"] = round(duration, 1)
    except (ValueError, TypeError):
        pass

    if video_stream:
        w = int(video_stream.get("width", 0))
        h = int(video_stream.get("height", 0))
        ctx.metadata["video_width"] = w
        ctx.metadata["video_height"] = h
        codec = video_stream.get("codec_name", "")
        ctx.metadata["video_codec"] = codec

        # Screen recording detection
        if _matches_screen_res(w, h):
            ctx.signals.append(Signal("video_screen_resolution", (w, h), {
                VIDEO_SCREEN_RECORDING: 0.35,
            }))

        # Check encoder/tags for screen recording hints
        encoder = fmt.get("tags", {}).get("encoder", "")
        major_brand = fmt.get("tags", {}).get("major_brand", "")
        if "screen" in encoder.lower() or "capture" in encoder.lower():
            ctx.signals.append(Signal("screen_capture_encoder", encoder, {
                VIDEO_SCREEN_RECORDING: 0.4,
            }))

        # Camera metadata
        make = fmt.get("tags", {}).get("com.apple.quicktime.make", "")
        if not make:
            make = fmt.get("tags", {}).get("make", "")
        if make:
            ctx.signals.append(Signal("video_camera_make", make, {
                VIDEO_CAMERA: 0.35,
            }))
            ctx.metadata["camera_make"] = make

    # Duration-based classification
    if duration is not None and duration > 0:
        if duration < 15:
            ctx.signals.append(Signal("very_short_video", duration, {
                VIDEO_GIF_VIDEO: 0.2,
                VIDEO_CLIP_SHORT: 0.15,
            }))
        elif duration < 60:
            ctx.signals.append(Signal("short_video", duration, {
                VIDEO_CLIP_SHORT: 0.25,
            }))
        elif duration > 2400:  # > 40 min
            ctx.signals.append(Signal("long_video", duration, {
                VIDEO_MOVIE: 0.25,
            }))
        if duration > 10800:  # > 3 hours
            ctx.signals.append(Signal("very_long_video", duration, {
                VIDEO_MOVIE: 0.3,
            }))

    # Audio channels (mono = possible screen recording hint)
    if audio_stream:
        channels = int(audio_stream.get("channels", 2))
        if channels == 1 and video_stream:
            ctx.signals.append(Signal("mono_audio_video", channels, {
                VIDEO_SCREEN_RECORDING: 0.1,
            }))
