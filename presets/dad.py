"""Dad's Choice preset: warm, human-readable folder organization."""

import re
from datetime import datetime
from pathlib import Path

from classifier.signals import FileClassification
from engine import MoveAction
from . import BasePreset, register

# Subtype -> folder mapping
FOLDER_MAP = {
    # Photos
    "image/photo_camera": "Photos",
    "image/photo_phone": "Photos",
    "image/photo_edited": "Edited Photos",
    "image/photo_raw": "RAW Photos",
    "image/panorama": "Photos/Panoramas",
    "image/scan": "Scanned Documents",

    # Screenshots
    "image/screenshot": "Screenshots",
    "image/screenshot_mobile": "Screenshots",

    # Fun
    "image/meme": "Fun Stuff",
    "image/gif_animated": "Fun Stuff/GIFs",
    "image/downloaded": "Downloaded Pictures",

    # Design & work
    "image/diagram": "Work Stuff/Diagrams",
    "image/graphic_design": "Work Stuff/Graphics",
    "image/icon": "Work Stuff/Icons",
    "image/thumbnail": "Misc Pictures",
    "image/wallpaper": "Wallpapers",

    # Videos
    "video/camera": "Home Videos",
    "video/screen_recording": "Screen Recordings",
    "video/clip_short": "Video Clips",
    "video/movie": "Movies",
    "video/gif_video": "Fun Stuff/Short Videos",
    "video/downloaded": "Downloaded Videos",

    # Audio
    "audio/music": "Music",
    "audio/voice_memo": "Voice Memos",
    "audio/podcast": "Podcasts",
    "audio/sound_effect": "Music/Sound Effects",
    "audio/ringtone": "Music/Ringtones",

    # Documents
    "document/pdf_document": "Important Documents",
    "document/pdf_ebook": "Books",
    "document/pdf_scanned": "Scanned Documents",
    "document/office_word": "Important Documents",
    "document/office_spreadsheet": "Important Documents/Spreadsheets",
    "document/office_presentation": "Important Documents/Presentations",
    "document/ebook": "Books",
    "document/text_note": "Notes",
    "document/text_log": "Computer Stuff/Logs",

    # Code
    "code/source": "Computer Stuff",
    "code/script": "Computer Stuff",
    "code/config": "Computer Stuff",
    "code/generated": "Computer Stuff",
    "code/minified": "Computer Stuff",
    "code/data": "Computer Stuff/Data Files",
    "code/build_artifact": "Computer Stuff",
    "code/notebook": "Computer Stuff/Notebooks",

    # Archives
    "archive/compressed": "Downloads & Archives",
    "archive/disk_image": "Downloads & Archives/Installers",
    "archive/package": "Downloads & Archives/Installers",

    # Other
    "other/font": "Computer Stuff/Fonts",
    "other/3d_model": "3D Models",
    "other/database": "Computer Stuff/Databases",
}

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Patterns to extract dates from filenames
DATE_PATTERNS = [
    re.compile(r'(\d{4})-(\d{2})-(\d{2})'),
    re.compile(r'(\d{4})(\d{2})(\d{2})'),
    re.compile(r'(\d{2})-(\d{2})-(\d{4})'),
]


def _extract_date(file_path: Path, classification: FileClassification) -> datetime | None:
    """Extract best date from EXIF, filename, or file stats."""
    # 1. EXIF datetime
    exif_dt = classification.metadata.get("exif_datetime")
    if exif_dt:
        try:
            return datetime.strptime(exif_dt, "%Y:%m:%d %H:%M:%S")
        except ValueError:
            pass

    # 2. Filename patterns
    name = file_path.stem
    for pattern in DATE_PATTERNS:
        m = pattern.search(name)
        if m:
            groups = m.groups()
            try:
                if len(groups[0]) == 4:
                    y, mo, d = int(groups[0]), int(groups[1]), int(groups[2])
                else:
                    mo, d, y = int(groups[0]), int(groups[1]), int(groups[2])
                if 1900 < y < 2100 and 1 <= mo <= 12 and 1 <= d <= 31:
                    return datetime(y, mo, d)
            except (ValueError, IndexError):
                continue

    # 3. File creation time (macOS st_birthtime)
    try:
        stat = file_path.stat()
        if hasattr(stat, "st_birthtime"):
            return datetime.fromtimestamp(stat.st_birthtime)
        return datetime.fromtimestamp(stat.st_mtime)
    except OSError:
        return None


def _get_date_folder(dt: datetime) -> str:
    """Create a warm, date-based folder name like 'March 2025 Photos'."""
    if 1 <= dt.month <= 12:
        return f"{MONTH_NAMES[dt.month]} {dt.year} Photos"
    return f"{dt.year} Photos"


@register
class DadPreset(BasePreset):
    name = "Dad's Choice"
    description = "Clean, human-friendly folders — the way Dad likes it"
    icon = "👨"

    def organize(
        self,
        files: list[tuple[Path, FileClassification]],
        base_dir: Path,
    ) -> list[MoveAction]:
        actions = []

        for file_path, classification in files:
            subtype = classification.subtype
            folder = FOLDER_MAP.get(subtype)

            # Fallback for generic subtypes
            if folder is None:
                cat = classification.category
                folder = {
                    "image": "Pictures",
                    "video": "Videos",
                    "audio": "Music",
                    "document": "Important Documents",
                    "code": "Computer Stuff",
                    "archive": "Downloads & Archives",
                    "other": "Other Files",
                }.get(cat, "Other Files")

            # For photos, sub-group by date
            if subtype in ("image/photo_camera", "image/photo_phone",
                           "image/photo_edited"):
                dt = _extract_date(file_path, classification)
                if dt:
                    date_folder = _get_date_folder(dt)
                    folder = f"Photos/{date_folder}"

            dest = base_dir / folder / file_path.name
            actions.append(MoveAction(
                source=file_path,
                destination=dest,
                classification=classification,
            ))

        return actions
