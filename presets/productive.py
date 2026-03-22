"""Productive preset: developer-friendly, clean organization."""

from pathlib import Path

from classifier.signals import FileClassification
from classifier.taxonomy import LANGUAGE_MAP
from engine import MoveAction
from . import BasePreset, register

# Subtype -> folder mapping
FOLDER_MAP = {
    # Images by subtype
    "image/photo_camera": "assets/images/photos",
    "image/photo_phone": "assets/images/photos",
    "image/photo_edited": "assets/images/edited",
    "image/photo_raw": "assets/images/raw",
    "image/screenshot": "assets/images/screenshots",
    "image/screenshot_mobile": "assets/images/screenshots",
    "image/meme": "assets/images/misc",
    "image/diagram": "assets/images/diagrams",
    "image/icon": "assets/images/icons",
    "image/thumbnail": "assets/images/thumbnails",
    "image/graphic_design": "assets/images/graphics",
    "image/scan": "assets/images/scans",
    "image/wallpaper": "assets/images/wallpapers",
    "image/panorama": "assets/images/photos",
    "image/gif_animated": "assets/images/gifs",
    "image/downloaded": "assets/images/misc",

    # Videos
    "video/camera": "assets/videos",
    "video/screen_recording": "assets/videos/screen-recordings",
    "video/clip_short": "assets/videos/clips",
    "video/movie": "assets/videos/movies",
    "video/gif_video": "assets/videos/clips",
    "video/downloaded": "assets/videos/downloaded",

    # Audio
    "audio/music": "assets/audio/music",
    "audio/voice_memo": "assets/audio/voice-memos",
    "audio/podcast": "assets/audio/podcasts",
    "audio/sound_effect": "assets/audio/sfx",
    "audio/ringtone": "assets/audio/ringtones",

    # Documents
    "document/pdf_document": "docs/pdfs",
    "document/pdf_ebook": "docs/ebooks",
    "document/pdf_scanned": "docs/scanned",
    "document/office_word": "docs/word",
    "document/office_spreadsheet": "docs/spreadsheets",
    "document/office_presentation": "docs/presentations",
    "document/ebook": "docs/ebooks",
    "document/text_note": "docs/notes",
    "document/text_log": "logs",

    # Code subtypes
    "code/config": "config",
    "code/generated": "code/generated",
    "code/minified": "code/build",
    "code/build_artifact": "code/build",
    "code/data": "data",
    "code/notebook": "notebooks",
    "code/script": "scripts",

    # Archives
    "archive/compressed": "archives",
    "archive/disk_image": "archives/disk-images",
    "archive/package": "archives/packages",

    # Other
    "other/font": "assets/fonts",
    "other/3d_model": "assets/3d-models",
    "other/database": "data/databases",
}


@register
class ProductivePreset(BasePreset):
    name = "Productive"
    description = "Dev-standard structure — clean, sorted, readable"
    icon = "💻"

    def organize(
        self,
        files: list[tuple[Path, FileClassification]],
        base_dir: Path,
    ) -> list[MoveAction]:
        actions = []
        category_counts: dict[str, int] = {}

        for file_path, classification in files:
            subtype = classification.subtype
            folder = FOLDER_MAP.get(subtype)

            # Source code → sort by language
            if subtype == "code/source":
                ext = file_path.suffix.lstrip(".").lower()
                lang = LANGUAGE_MAP.get(ext, "other")
                folder = f"code/{lang}"

            # Fallback for unmapped subtypes
            if folder is None:
                cat = classification.category
                folder = {
                    "image": "assets/images",
                    "video": "assets/videos",
                    "audio": "assets/audio",
                    "document": "docs",
                    "code": "code",
                    "archive": "archives",
                    "other": "_unsorted",
                }.get(cat, "_unsorted")

            dest = base_dir / folder / file_path.name
            actions.append(MoveAction(
                source=file_path,
                destination=dest,
                classification=classification,
            ))

            # Track counts for README
            cat_label = folder.split("/")[0]
            category_counts[cat_label] = category_counts.get(cat_label, 0) + 1

        # Generate README.md
        if actions:
            readme_lines = ["# Directory Organization Summary\n"]
            readme_lines.append(f"Organized **{len(actions)}** files into the following structure:\n")
            for cat, count in sorted(category_counts.items()):
                readme_lines.append(f"- `{cat}/` — {count} file{'s' if count != 1 else ''}")
            readme_lines.append(f"\n_Organized with the Productive preset._\n")
            readme_content = "\n".join(readme_lines)

            actions.append(MoveAction(
                source=base_dir / "README.md",
                destination=base_dir / "README.md",
                classification=FileClassification(
                    category="other", subtype="other/generated",
                    confidence=1.0, signals=[], metadata={},
                ),
                content=readme_content,
            ))

        return actions
