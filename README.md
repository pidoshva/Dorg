# Dorg — Directory Organizer

A smart desktop app that organizes any messy directory using **advanced file detection** — not just file extensions, but magic bytes, image analysis, EXIF data, audio probing, and 40+ filename patterns.

Pick a preset. Preview the changes. Apply with one click. Undo anytime.

<br>

## Three Presets

### Dad's Choice
*The way Dad wants things organized.* Clean, human-friendly folder names that make sense to everyone.

```
Photos/
  March 2025 Photos/
    IMG_20250315_vacation.jpg
Screenshots/
  Screenshot 2025-03-15 at 10.30.22.png
Fun Stuff/
  when_you_finally_fix_the_bug.png
  GIFs/
    reaction.gif
Important Documents/
  invoice_march_2025.pdf
Music/
  summer_vibes.mp3
Voice Memos/
  New Recording 001.m4a
Computer Stuff/
  app.py
```

Photos are automatically grouped by month using EXIF dates, filename patterns, or file creation time.

---

### Productive
*Developer-standard structure.* Everything sorted by type and language — clean, lowercase, readable.

```
code/
  python/
    app.py
  build/
    bundle.min.js
config/
  config.yaml
assets/
  images/
    photos/
      IMG_20250315_vacation.jpg
    screenshots/
      Screenshot 2025-03-15 at 10.30.22.png
  audio/
    voice-memos/
      New Recording 001.m4a
docs/
  pdfs/
    invoice_march_2025.pdf
  notes/
    todo.txt
_unsorted/
  (anything that doesn't clearly fit)
README.md  <- auto-generated summary
```

Source code is sorted by language. Unimportant files go to `_unsorted/` for later review.

---

### Messy
*Pure chaos — for fun.* Files get randomly buried in absurdly named folders.

```
passwords_definitely_not/
  vacation_plans_mars/
    snack_ideas/
      new_folder_final_FINAL_v2/
        New Recording 001.m4a
definitely_not_homework/
  tax_returns_2077/
    app.py
area_51_leaked_docs/
  todo.txt
the_bermuda_folder/
  invoice_march_2025.pdf
```

55+ funny folder names. Random nesting depth (1-4 levels). Every run is different.

<br>

## Smart File Detection

The app doesn't just look at file extensions. It uses **8 independent analyzers** that vote on what each file actually is, then combines their scores:

| Analyzer | What it checks | Example |
|----------|---------------|---------|
| **Magic Bytes** | First 32 bytes of the file header | Detects a renamed `.txt` that's actually a JPEG |
| **File Size** | Size heuristics per category | <10KB image = icon, >50MB = RAW photo |
| **Filename Patterns** | 40+ regex patterns | `Screenshot 2025-...` = screenshot, `IMG_20250315` = phone photo |
| **Image Analysis** | Dimensions, entropy, colors, EXIF | Matches 25+ screen resolutions, low entropy = screenshot |
| **Video Probing** | Resolution, duration, codec | Screen res + short duration = screen recording |
| **Audio Probing** | Duration, bitrate, channels, ID3 tags | Mono + low bitrate = voice memo, has artist tag = music |
| **Document Analysis** | PDF page count, size per page | >500KB/page = scanned document |
| **Code Analysis** | Shebang, imports, line length | Avg line >500 chars = minified code |

### What it can distinguish

Not just "image" vs "video" — the classifier knows **40+ subtypes**:

- **Photos**: camera vs phone vs edited vs RAW vs panorama
- **Screenshots**: desktop vs mobile (matches exact screen resolutions)
- **Images**: meme vs diagram vs icon vs graphic design vs wallpaper
- **Videos**: camera vs screen recording vs short clip vs movie
- **Audio**: music vs voice memo vs podcast vs sound effect
- **Documents**: PDF vs ebook vs scanned document vs spreadsheet
- **Code**: source vs script vs config vs minified vs generated

<br>

## Getting Started

### Requirements

- **Python 3.10+**
- **Pillow** (optional, enables image analysis — dimensions, entropy, EXIF)
- **ffprobe** (optional, enables video/audio duration and codec detection)

Without optional dependencies, the app still works using magic bytes, file size, and filename patterns.

### Install and Run

```bash
# Clone the repo
git clone https://github.com/pidoshva/Dorg.git
cd Dorg

# Install Pillow (recommended)
pip install Pillow

# Run the app
python3 organizer.py
```

### Usage

1. Click **Choose Directory** and pick any folder
2. Select a preset (**Dad's Choice**, **Productive**, or **Messy**)
3. Review the preview tree — see exactly where every file will go
4. Click **Apply Changes**
5. Changed your mind? Click **Undo Last** to reverse everything

<br>

## Safety

- **Never deletes files** — only moves them
- **Full undo** — every operation is logged to a manifest file
- **Preview first** — see the complete plan before anything happens
- **Rollback on failure** — if any move fails mid-operation, all changes are reversed
- **Non-recursive** — only organizes top-level files, won't touch existing subfolders

<br>

## Project Structure

```
DirectoryOrganizer/
├── organizer.py                 # GUI application (tkinter)
├── engine.py                    # Plan execution, undo, manifest
├── classifier/
│   ├── __init__.py              # Public API: classify_file(path)
│   ├── taxonomy.py              # 40+ file subtype definitions
│   ├── signals.py               # Signal & FileClassification dataclasses
│   ├── capabilities.py          # Runtime detection (Pillow? ffprobe?)
│   ├── fusion.py                # Weighted scoring engine
│   └── analyzers/
│       ├── magic_bytes.py       # File signature detection
│       ├── file_size.py         # Size-based heuristics
│       ├── filename_patterns.py # 40+ regex patterns
│       ├── image.py             # Dimensions, entropy, EXIF
│       ├── video.py             # ffprobe: resolution, duration
│       ├── audio.py             # ffprobe: bitrate, ID3 tags
│       ├── document.py          # PDF page analysis
│       └── code.py              # Shebang, minification detection
└── presets/
    ├── __init__.py              # Base class & registry
    ├── dad.py                   # Dad's Choice preset
    ├── productive.py            # Productive preset
    └── messy.py                 # Messy preset
```

<br>

## License

MIT
