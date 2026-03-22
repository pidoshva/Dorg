"""All file category and subtype constants."""

# Top-level categories
CATEGORY_IMAGE = "image"
CATEGORY_VIDEO = "video"
CATEGORY_AUDIO = "audio"
CATEGORY_DOCUMENT = "document"
CATEGORY_CODE = "code"
CATEGORY_ARCHIVE = "archive"
CATEGORY_OTHER = "other"

# Image subtypes
IMAGE_PHOTO_CAMERA = "image/photo_camera"
IMAGE_PHOTO_PHONE = "image/photo_phone"
IMAGE_PHOTO_EDITED = "image/photo_edited"
IMAGE_PHOTO_RAW = "image/photo_raw"
IMAGE_SCREENSHOT = "image/screenshot"
IMAGE_SCREENSHOT_MOBILE = "image/screenshot_mobile"
IMAGE_MEME = "image/meme"
IMAGE_DIAGRAM = "image/diagram"
IMAGE_ICON = "image/icon"
IMAGE_THUMBNAIL = "image/thumbnail"
IMAGE_GRAPHIC_DESIGN = "image/graphic_design"
IMAGE_SCAN = "image/scan"
IMAGE_WALLPAPER = "image/wallpaper"
IMAGE_PANORAMA = "image/panorama"
IMAGE_GIF_ANIMATED = "image/gif_animated"
IMAGE_DOWNLOADED = "image/downloaded"

# Video subtypes
VIDEO_CAMERA = "video/camera"
VIDEO_SCREEN_RECORDING = "video/screen_recording"
VIDEO_CLIP_SHORT = "video/clip_short"
VIDEO_MOVIE = "video/movie"
VIDEO_GIF_VIDEO = "video/gif_video"
VIDEO_DOWNLOADED = "video/downloaded"

# Audio subtypes
AUDIO_MUSIC = "audio/music"
AUDIO_VOICE_MEMO = "audio/voice_memo"
AUDIO_PODCAST = "audio/podcast"
AUDIO_SOUND_EFFECT = "audio/sound_effect"
AUDIO_RINGTONE = "audio/ringtone"

# Document subtypes
DOC_PDF = "document/pdf_document"
DOC_PDF_EBOOK = "document/pdf_ebook"
DOC_PDF_SCANNED = "document/pdf_scanned"
DOC_OFFICE_WORD = "document/office_word"
DOC_OFFICE_SPREADSHEET = "document/office_spreadsheet"
DOC_OFFICE_PRESENTATION = "document/office_presentation"
DOC_EBOOK = "document/ebook"
DOC_TEXT_NOTE = "document/text_note"
DOC_TEXT_LOG = "document/text_log"

# Code subtypes
CODE_SOURCE = "code/source"
CODE_SCRIPT = "code/script"
CODE_CONFIG = "code/config"
CODE_GENERATED = "code/generated"
CODE_MINIFIED = "code/minified"
CODE_DATA = "code/data"
CODE_BUILD_ARTIFACT = "code/build_artifact"
CODE_NOTEBOOK = "code/notebook"

# Archive subtypes
ARCHIVE_COMPRESSED = "archive/compressed"
ARCHIVE_DISK_IMAGE = "archive/disk_image"
ARCHIVE_PACKAGE = "archive/package"

# Other subtypes
OTHER_FONT = "other/font"
OTHER_3D_MODEL = "other/3d_model"
OTHER_DATABASE = "other/database"
OTHER_UNKNOWN = "other/unknown"
OTHER_EMPTY = "other/empty"

# Extension-to-category mapping (fallback when magic bytes unavailable)
IMAGE_EXTENSIONS = {
    "jpg", "jpeg", "png", "gif", "bmp", "tiff", "tif", "webp", "svg",
    "ico", "heic", "heif", "avif", "raw", "cr2", "nef", "arw", "dng",
    "orf", "rw2", "pef", "sr2",
}
VIDEO_EXTENSIONS = {
    "mp4", "mov", "avi", "mkv", "wmv", "flv", "webm", "m4v", "mpg",
    "mpeg", "3gp", "ogv", "ts", "mts", "m2ts",
}
AUDIO_EXTENSIONS = {
    "mp3", "wav", "aac", "flac", "ogg", "wma", "m4a", "opus", "aiff",
    "alac", "m4r", "mid", "midi",
}
DOCUMENT_EXTENSIONS = {
    "pdf", "doc", "docx", "odt", "rtf", "txt", "xls", "xlsx", "ods",
    "csv", "ppt", "pptx", "odp", "epub", "mobi", "pages", "numbers",
    "keynote", "log",
}
CODE_EXTENSIONS = {
    "py", "js", "jsx", "ts", "tsx", "java", "c", "cpp", "cc", "h",
    "hpp", "go", "rs", "rb", "php", "swift", "kt", "kts", "cs", "sh",
    "bash", "zsh", "fish", "sql", "r", "lua", "pl", "pm", "dart",
    "scala", "hs", "ex", "exs", "clj", "elm", "vue", "svelte",
}
CONFIG_EXTENSIONS = {
    "json", "yaml", "yml", "toml", "ini", "cfg", "conf", "env",
    "xml", "plist", "properties", "gradle",
}
ARCHIVE_EXTENSIONS = {
    "zip", "tar", "gz", "bz2", "xz", "7z", "rar", "tgz",
    "iso", "dmg", "img", "pkg", "deb", "rpm", "msi", "apk",
}
FONT_EXTENSIONS = {"ttf", "otf", "woff", "woff2", "eot"}
MODEL_3D_EXTENSIONS = {"obj", "stl", "fbx", "blend", "3ds", "dae"}
DATABASE_EXTENSIONS = {"sqlite", "sqlite3", "db", "mdb"}

# Config filenames (no extension)
CONFIG_FILENAMES = {
    "makefile", "dockerfile", "vagrantfile", "gemfile", "rakefile",
    "procfile", "brewfile", "justfile", "taskfile",
    ".gitignore", ".gitattributes", ".editorconfig", ".eslintrc",
    ".prettierrc", ".babelrc", ".npmrc", ".nvmrc", ".dockerignore",
}

# Code extensions mapped to language name
LANGUAGE_MAP = {
    "py": "python", "js": "javascript", "jsx": "javascript",
    "ts": "typescript", "tsx": "typescript", "java": "java",
    "c": "c", "cpp": "cpp", "cc": "cpp", "h": "c-header",
    "hpp": "cpp-header", "go": "go", "rs": "rust", "rb": "ruby",
    "php": "php", "swift": "swift", "kt": "kotlin", "kts": "kotlin",
    "cs": "csharp", "sh": "shell", "bash": "shell", "zsh": "shell",
    "fish": "shell", "sql": "sql", "r": "r", "lua": "lua",
    "pl": "perl", "pm": "perl", "dart": "dart", "scala": "scala",
    "hs": "haskell", "ex": "elixir", "exs": "elixir", "clj": "clojure",
    "elm": "elm", "vue": "vue", "svelte": "svelte",
}
