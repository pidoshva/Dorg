"""40+ regex patterns for classifying files by name."""

import re
from ..signals import AnalysisContext, Signal
from ..taxonomy import *  # noqa: F403, F401

# (compiled_regex, votes_dict)
PATTERNS: list[tuple[re.Pattern, dict[str, float]]] = []


def _p(pattern: str, votes: dict[str, float], flags=re.IGNORECASE):
    PATTERNS.append((re.compile(pattern, flags), votes))


# === Screenshots ===
_p(r'screenshot[_ -]?\d', {IMAGE_SCREENSHOT: 0.5})
_p(r'^Screenshot \d{4}-\d{2}-\d{2}', {IMAGE_SCREENSHOT: 0.6})
_p(r'^Screen Shot \d{4}-\d{2}-\d{2}', {IMAGE_SCREENSHOT: 0.6})
_p(r'^Capture d.+cran', {IMAGE_SCREENSHOT: 0.5})  # French macOS
_p(r'^Bildschirmfoto', {IMAGE_SCREENSHOT: 0.5})    # German macOS
_p(r'^Captura de pantalla', {IMAGE_SCREENSHOT: 0.5})  # Spanish
_p(r'^Снимок экрана', {IMAGE_SCREENSHOT: 0.5})  # Russian
_p(r'^CleanShot', {IMAGE_SCREENSHOT: 0.5})
_p(r'^Simulator Screen Shot', {IMAGE_SCREENSHOT_MOBILE: 0.6})

# === Screen recordings ===
_p(r'screen.?record', {VIDEO_SCREEN_RECORDING: 0.5})
_p(r'^Screen Recording \d{4}', {VIDEO_SCREEN_RECORDING: 0.6})
_p(r'\.screenflow', {VIDEO_SCREEN_RECORDING: 0.3})

# === Camera files ===
_p(r'^DSC[_N]?\d{4,}', {IMAGE_PHOTO_CAMERA: 0.35})
_p(r'^IMG_\d{4,}', {IMAGE_PHOTO_PHONE: 0.3, IMAGE_PHOTO_CAMERA: 0.15})
_p(r'^DCIM', {IMAGE_PHOTO_CAMERA: 0.3})
_p(r'^P\d{7,}', {IMAGE_PHOTO_CAMERA: 0.25})
_p(r'^_DSC\d{4}', {IMAGE_PHOTO_CAMERA: 0.35})
_p(r'^DJI_\d{4}', {IMAGE_PHOTO_CAMERA: 0.3})
_p(r'^PXL_\d{8}', {IMAGE_PHOTO_PHONE: 0.4})
_p(r'^GOPR\d{4}', {IMAGE_PHOTO_CAMERA: 0.35})  # GoPro

# === Phone videos ===
_p(r'^VID_\d{8}_\d{6}', {VIDEO_CAMERA: 0.35})
_p(r'^MOV_\d{4}', {VIDEO_CAMERA: 0.3})
_p(r'^RPReplay', {VIDEO_SCREEN_RECORDING: 0.5})  # iOS screen recording

# === Messaging apps ===
_p(r'^WhatsApp (Image|Video|Audio)', {IMAGE_DOWNLOADED: 0.3, VIDEO_DOWNLOADED: 0.3, AUDIO_VOICE_MEMO: 0.2})
_p(r'^IMG-\d{8}-WA\d{4}', {IMAGE_DOWNLOADED: 0.4})
_p(r'^VID-\d{8}-WA\d{4}', {VIDEO_DOWNLOADED: 0.4})
_p(r'^PTT-\d{8}', {AUDIO_VOICE_MEMO: 0.4})
_p(r'^photo_\d{4}-\d{2}-\d{2}', {IMAGE_DOWNLOADED: 0.3})

# === Downloaded media ===
_p(r'S\d{1,2}E\d{1,2}', {VIDEO_DOWNLOADED: 0.5})
_p(r'\b(720p|1080p|2160p|4K|BRRip|WEBRip|BluRay)\b', {VIDEO_DOWNLOADED: 0.5})
_p(r'\b(x264|x265|HEVC|AAC|AC3)\b', {VIDEO_DOWNLOADED: 0.4})

# === Voice memos ===
_p(r'^(voice.?memo|recording|audio.?note)', {AUDIO_VOICE_MEMO: 0.45})
_p(r'^New Recording', {AUDIO_VOICE_MEMO: 0.5})
_p(r'^Voice \d{3}', {AUDIO_VOICE_MEMO: 0.5})

# === Documents ===
_p(r'(invoice|receipt|bill|statement)', {DOC_PDF: 0.2})
_p(r'(resume|cv|curriculum)', {DOC_PDF: 0.2})
_p(r'(contract|agreement|nda)', {DOC_PDF: 0.2})

# === Memes ===
_p(r'(meme|reaction|when.you|nobody.*:)', {IMAGE_MEME: 0.3})

# === Code artifacts ===
_p(r'\.(min|bundle)\.(js|css)$', {CODE_MINIFIED: 0.7})
_p(r'\.generated\.\w+$', {CODE_GENERATED: 0.6})
_p(r'\.d\.ts$', {CODE_BUILD_ARTIFACT: 0.6})
_p(r'\.map$', {CODE_BUILD_ARTIFACT: 0.5})

# === Config files ===
_p(r'^(Makefile|Dockerfile|Vagrantfile|Gemfile|Procfile)$', {CODE_CONFIG: 0.5})
_p(r'\.(env|ini|cfg|conf|toml|yaml|yml)$', {CODE_CONFIG: 0.5})
_p(r'^(\..+rc|\.editorconfig|tsconfig.*\.json|package\.json|Cargo\.toml)$', {CODE_CONFIG: 0.5})

# === Wallpapers ===
_p(r'(wallpaper|background|desktop)', {IMAGE_WALLPAPER: 0.35})

# === Notebooks ===
_p(r'\.ipynb$', {CODE_NOTEBOOK: 0.7})

# === Log files ===
_p(r'\.log$', {DOC_TEXT_LOG: 0.5})
_p(r'\.log\.\d+$', {DOC_TEXT_LOG: 0.6})


def analyze(ctx: AnalysisContext):
    """Run all filename patterns against the file."""
    name = ctx.filename
    for pattern, votes in PATTERNS:
        if pattern.search(name):
            ctx.signals.append(Signal(
                f"filename_{pattern.pattern[:30]}",
                name,
                votes,
            ))
