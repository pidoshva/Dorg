"""Audio analysis: duration, bitrate, channels, ID3 tags."""

import json
import subprocess
from ..signals import AnalysisContext, Signal
from ..capabilities import ClassifierCapabilities
from ..taxonomy import *  # noqa: F403, F401


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


def analyze(ctx: AnalysisContext, caps: ClassifierCapabilities):
    """Analyze audio file."""
    if not caps.has_ffprobe:
        return

    info = _probe(ctx.path)
    if not info:
        return

    fmt = info.get("format", {})
    tags = fmt.get("tags", {})

    # Duration
    duration = None
    try:
        duration = float(fmt.get("duration", 0))
        ctx.metadata["duration"] = round(duration, 1)
    except (ValueError, TypeError):
        pass

    # Bitrate
    bitrate = None
    try:
        bitrate = int(fmt.get("bit_rate", 0))
        ctx.metadata["bitrate"] = bitrate
    except (ValueError, TypeError):
        pass

    # Audio stream info
    audio_stream = None
    for stream in info.get("streams", []):
        if stream.get("codec_type") == "audio":
            audio_stream = stream
            break

    channels = 2
    if audio_stream:
        channels = int(audio_stream.get("channels", 2))
        ctx.metadata["channels"] = channels
        ctx.metadata["audio_codec"] = audio_stream.get("codec_name", "")

    # ID3 / metadata tags
    artist = tags.get("artist", "") or tags.get("ARTIST", "")
    album = tags.get("album", "") or tags.get("ALBUM", "")
    title = tags.get("title", "") or tags.get("TITLE", "")

    if artist or album:
        ctx.signals.append(Signal("audio_has_tags", {"artist": artist, "album": album}, {
            AUDIO_MUSIC: 0.4,
        }))
        ctx.metadata["artist"] = artist
        ctx.metadata["album"] = album
        ctx.metadata["title"] = title

    if duration is None:
        return

    # Duration + bitrate + channels classification
    if duration < 10:
        ctx.signals.append(Signal("very_short_audio", duration, {
            AUDIO_SOUND_EFFECT: 0.4,
        }))
    elif duration < 40:
        ext = ctx.extension
        if ext == "m4r":
            ctx.signals.append(Signal("ringtone_format", ext, {
                AUDIO_RINGTONE: 0.5,
            }))
        else:
            ctx.signals.append(Signal("short_audio", duration, {
                AUDIO_RINGTONE: 0.15,
                AUDIO_SOUND_EFFECT: 0.1,
            }))
    elif 120 <= duration <= 480 and channels == 2:
        bps = (bitrate or 0) / 1000
        if bps > 128 or bps == 0:
            ctx.signals.append(Signal("music_duration_profile", duration, {
                AUDIO_MUSIC: 0.25,
            }))
    elif duration > 900:  # > 15 min
        if channels == 1 or (bitrate and bitrate / 1000 < 96):
            ctx.signals.append(Signal("speech_profile", duration, {
                AUDIO_PODCAST: 0.3,
                AUDIO_VOICE_MEMO: 0.15,
            }))
        else:
            ctx.signals.append(Signal("long_audio", duration, {
                AUDIO_PODCAST: 0.2,
                AUDIO_MUSIC: 0.1,
            }))

    # Mono + low bitrate = voice memo
    if channels == 1 and bitrate and bitrate / 1000 < 64:
        ctx.signals.append(Signal("voice_memo_profile", {"channels": channels, "bitrate": bitrate}, {
            AUDIO_VOICE_MEMO: 0.35,
        }))
