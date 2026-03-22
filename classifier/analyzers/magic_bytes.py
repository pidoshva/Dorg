"""File signature detection via magic bytes."""

import zipfile
from ..signals import AnalysisContext, Signal
from ..taxonomy import (
    CATEGORY_IMAGE, CATEGORY_VIDEO, CATEGORY_AUDIO, CATEGORY_DOCUMENT,
    CATEGORY_CODE, CATEGORY_ARCHIVE, CATEGORY_OTHER,
    IMAGE_EXTENSIONS, VIDEO_EXTENSIONS, AUDIO_EXTENSIONS,
    DOCUMENT_EXTENSIONS, CODE_EXTENSIONS, CONFIG_EXTENSIONS,
    ARCHIVE_EXTENSIONS, FONT_EXTENSIONS, MODEL_3D_EXTENSIONS,
    DATABASE_EXTENSIONS, CONFIG_FILENAMES,
)

# (prefix_bytes, mime_type)
SIGNATURES = [
    (b'\xff\xd8\xff',            "image/jpeg"),
    (b'\x89PNG\r\n\x1a\n',      "image/png"),
    (b'GIF87a',                  "image/gif"),
    (b'GIF89a',                  "image/gif"),
    (b'BM',                      "image/bmp"),
    (b'\x00\x00\x01\x00',       "image/x-icon"),
    (b'II\x2a\x00',             "image/tiff"),
    (b'MM\x00\x2a',             "image/tiff"),
    (b'%PDF',                    "application/pdf"),
    (b'PK\x03\x04',             "_zip"),
    (b'\x1f\x8b',               "application/gzip"),
    (b'Rar!\x1a\x07',           "application/x-rar"),
    (b'7z\xbc\xaf\x27\x1c',    "application/x-7z"),
    (b'\xfd7zXZ\x00',           "application/x-xz"),
    (b'ID3',                     "audio/mpeg"),
    (b'\xff\xfb',               "audio/mpeg"),
    (b'\xff\xf3',               "audio/mpeg"),
    (b'\xff\xf2',               "audio/mpeg"),
    (b'fLaC',                    "audio/flac"),
    (b'OggS',                    "audio/ogg"),
    (b'RIFF',                    "_riff"),
    (b'\x1a\x45\xdf\xa3',      "video/webm"),
    (b'SQLite format 3',        "application/x-sqlite3"),
]

MIME_TO_CATEGORY = {
    "image/jpeg": CATEGORY_IMAGE,
    "image/png": CATEGORY_IMAGE,
    "image/gif": CATEGORY_IMAGE,
    "image/bmp": CATEGORY_IMAGE,
    "image/x-icon": CATEGORY_IMAGE,
    "image/tiff": CATEGORY_IMAGE,
    "image/webp": CATEGORY_IMAGE,
    "image/heic": CATEGORY_IMAGE,
    "image/avif": CATEGORY_IMAGE,
    "video/mp4": CATEGORY_VIDEO,
    "video/quicktime": CATEGORY_VIDEO,
    "video/avi": CATEGORY_VIDEO,
    "video/webm": CATEGORY_VIDEO,
    "audio/mpeg": CATEGORY_AUDIO,
    "audio/flac": CATEGORY_AUDIO,
    "audio/ogg": CATEGORY_AUDIO,
    "audio/wav": CATEGORY_AUDIO,
    "audio/mp4": CATEGORY_AUDIO,
    "application/pdf": CATEGORY_DOCUMENT,
    "application/zip": CATEGORY_ARCHIVE,
    "application/gzip": CATEGORY_ARCHIVE,
    "application/x-rar": CATEGORY_ARCHIVE,
    "application/x-7z": CATEGORY_ARCHIVE,
    "application/x-xz": CATEGORY_ARCHIVE,
    "application/x-sqlite3": CATEGORY_OTHER,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": CATEGORY_DOCUMENT,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": CATEGORY_DOCUMENT,
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": CATEGORY_DOCUMENT,
    "application/epub+zip": CATEGORY_DOCUMENT,
}


def _detect_riff(header: bytes) -> str:
    """Sub-detect RIFF format from bytes 8-12."""
    if len(header) >= 12:
        fourcc = header[8:12]
        if fourcc == b'WEBP':
            return "image/webp"
        elif fourcc == b'AVI ':
            return "video/avi"
        elif fourcc == b'WAVE':
            return "audio/wav"
    return "application/octet-stream"


def _detect_isobmff(header: bytes) -> str:
    """Detect ISO Base Media File Format (MP4, MOV, HEIC, etc.)."""
    # Look for 'ftyp' box — typically at offset 4
    ftyp_pos = header.find(b'ftyp')
    if ftyp_pos < 0:
        return "video/mp4"  # default guess
    brand_start = ftyp_pos + 4
    if brand_start + 4 <= len(header):
        brand = header[brand_start:brand_start + 4]
        brand_str = brand.decode("ascii", errors="ignore").strip()
        if brand_str in ("qt", "MQTF"):
            return "video/quicktime"
        elif brand_str in ("M4A", "M4B"):
            return "audio/mp4"
        elif brand_str in ("heic", "heix", "hevc", "mif1"):
            return "image/heic"
        elif brand_str == "avif":
            return "image/avif"
    return "video/mp4"


def _detect_zip_contents(path) -> str:
    """Peek inside a ZIP to distinguish DOCX, XLSX, PPTX, EPUB, etc."""
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            name_set = set(names)
            # Check for Office Open XML
            for name in names:
                if name.startswith("word/"):
                    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                if name.startswith("xl/"):
                    return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                if name.startswith("ppt/"):
                    return "application/vnd.openxmlformats-officedocument.presentationml.presentation"
            # EPUB
            if "META-INF/container.xml" in name_set:
                return "application/epub+zip"
            if "mimetype" in name_set:
                try:
                    mt = zf.read("mimetype").decode("utf-8", errors="ignore").strip()
                    if "epub" in mt.lower():
                        return "application/epub+zip"
                except Exception:
                    pass
    except Exception:
        pass
    return "application/zip"


def _category_from_extension(ext: str, filename: str) -> str:
    """Fallback category detection from file extension."""
    lower_name = filename.lower()
    if ext in IMAGE_EXTENSIONS:
        return CATEGORY_IMAGE
    if ext in VIDEO_EXTENSIONS:
        return CATEGORY_VIDEO
    if ext in AUDIO_EXTENSIONS:
        return CATEGORY_AUDIO
    if ext in DOCUMENT_EXTENSIONS:
        return CATEGORY_DOCUMENT
    if ext in CODE_EXTENSIONS or ext in CONFIG_EXTENSIONS:
        return CATEGORY_CODE
    if ext in ARCHIVE_EXTENSIONS:
        return CATEGORY_ARCHIVE
    if ext in FONT_EXTENSIONS:
        return CATEGORY_OTHER
    if ext in MODEL_3D_EXTENSIONS:
        return CATEGORY_OTHER
    if ext in DATABASE_EXTENSIONS:
        return CATEGORY_OTHER
    if lower_name in CONFIG_FILENAMES:
        return CATEGORY_CODE
    return CATEGORY_OTHER


def analyze(ctx: AnalysisContext):
    """Detect true file type from magic bytes."""
    try:
        with open(ctx.path, "rb") as f:
            header = f.read(64)
    except (OSError, PermissionError):
        ctx.true_category = _category_from_extension(ctx.extension, ctx.filename)
        return

    if not header:
        ctx.true_category = CATEGORY_OTHER
        ctx.magic_type = "application/x-empty"
        return

    detected = None

    # Check signatures
    for sig, mime in SIGNATURES:
        if header.startswith(sig):
            detected = mime
            break

    # Handle special cases
    if detected == "_riff":
        detected = _detect_riff(header)
    elif detected == "_zip":
        detected = _detect_zip_contents(ctx.path)
    elif detected is None:
        # Check for ISO Base Media (MP4/MOV/HEIC) — box-based format
        if len(header) >= 12 and b'ftyp' in header[:32]:
            detected = _detect_isobmff(header)

    if detected:
        ctx.magic_type = detected
        ctx.true_category = MIME_TO_CATEGORY.get(detected, CATEGORY_OTHER)

        # Check extension mismatch
        ext_category = _category_from_extension(ctx.extension, ctx.filename)
        if ext_category != CATEGORY_OTHER and ext_category != ctx.true_category:
            ctx.signals.append(Signal(
                "extension_mismatch",
                {"extension_says": ext_category, "magic_says": ctx.true_category},
                {},  # informational, no votes
            ))
            ctx.metadata["extension_mismatch"] = True
    else:
        # No magic match — use extension
        ctx.true_category = _category_from_extension(ctx.extension, ctx.filename)
        ctx.magic_type = None
