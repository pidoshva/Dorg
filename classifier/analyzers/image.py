"""Deep image analysis: dimensions, entropy, color stats, EXIF."""

import math
from collections import Counter
from ..signals import AnalysisContext, Signal
from ..taxonomy import *  # noqa: F403, F401

# Common screen resolutions (width, height)
SCREEN_RESOLUTIONS = {
    # Desktop
    (1920, 1080), (2560, 1440), (3840, 2160),
    (1440, 900), (2880, 1800),
    (1512, 982), (3024, 1964),
    (1728, 1117), (3456, 2234),
    (1680, 1050), (3360, 2100),
    (2560, 1600), (5120, 3200),
    (1366, 768), (1280, 800), (1280, 720),
    (2560, 1080), (3440, 1440),
    (5120, 1440),
    # Mobile (portrait)
    (1170, 2532), (1284, 2778),
    (1179, 2556), (1290, 2796),
    (1080, 2340), (1440, 3200),
    (1080, 2400), (1080, 1920),
    (828, 1792), (750, 1334),
    (1125, 2436), (1242, 2688),
    (1080, 2160), (1440, 2560),
}

PHONE_MAKERS = {
    "apple", "samsung", "google", "huawei", "xiaomi", "oneplus",
    "oppo", "vivo", "motorola", "lg", "sony", "pixel",
}

EDITING_SOFTWARE = {
    "adobe photoshop", "lightroom", "gimp", "affinity", "capture one",
    "darktable", "snapseed", "pixelmator", "acorn",
}


def _matches_screen_resolution(w: int, h: int) -> tuple[bool, bool]:
    """Returns (is_screen_res, is_mobile_res)."""
    for sw, sh in SCREEN_RESOLUTIONS:
        if abs(w - sw) <= 2 and abs(h - sh) <= 2:
            is_mobile = sh > sw * 1.5  # portrait orientation
            return True, is_mobile
        if abs(w - sh) <= 2 and abs(h - sw) <= 2:
            is_mobile = sw > sh * 1.5
            return True, is_mobile
    return False, False


def _compute_entropy(img) -> float:
    """Shannon entropy on quantized pixel colors."""
    thumb = img.resize((256, 256)).convert("RGB")
    pixels = list(thumb.getdata())
    quantized = Counter()
    for r, g, b in pixels:
        quantized[(r >> 4, g >> 4, b >> 4)] += 1
    total = len(pixels)
    entropy = 0.0
    for count in quantized.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _compute_color_stats(img) -> dict:
    """Unique color count and white/gray ratio."""
    thumb = img.resize((128, 128)).convert("RGB")
    pixels = list(thumb.getdata())
    unique_colors = len(set(pixels))
    white_gray_count = sum(
        1 for r, g, b in pixels
        if (r > 220 and g > 220 and b > 220)
        or (abs(r - g) < 10 and abs(g - b) < 10 and r > 180)
    )
    return {
        "unique_colors": unique_colors,
        "white_gray_ratio": white_gray_count / len(pixels) if pixels else 0,
    }


def _analyze_exif(img, ctx: AnalysisContext):
    """Extract EXIF signals."""
    try:
        exif = img._getexif()
    except (AttributeError, Exception):
        exif = None

    if exif is None:
        ctx.signals.append(Signal("exif_absent", True, {
            IMAGE_SCREENSHOT: 0.2,
            IMAGE_MEME: 0.1,
            IMAGE_DOWNLOADED: 0.15,
            IMAGE_DIAGRAM: 0.1,
            IMAGE_PHOTO_CAMERA: -0.2,
            IMAGE_PHOTO_PHONE: -0.15,
        }))
        return

    make = exif.get(0x010F, "")
    model = exif.get(0x0110, "")
    software = exif.get(0x0131, "")

    if make:
        make_lower = make.lower().strip()
        if any(p in make_lower for p in PHONE_MAKERS):
            ctx.signals.append(Signal("exif_phone_camera", make, {
                IMAGE_PHOTO_PHONE: 0.45,
                IMAGE_SCREENSHOT: -0.3,
                IMAGE_MEME: -0.2,
            }))
            ctx.metadata["camera_make"] = make
            ctx.metadata["camera_model"] = model
        else:
            ctx.signals.append(Signal("exif_camera", f"{make} {model}", {
                IMAGE_PHOTO_CAMERA: 0.45,
                IMAGE_SCREENSHOT: -0.3,
                IMAGE_MEME: -0.2,
            }))
            ctx.metadata["camera_make"] = make
            ctx.metadata["camera_model"] = model

    if software:
        sw_lower = software.lower()
        for editor in EDITING_SOFTWARE:
            if editor in sw_lower:
                ctx.signals.append(Signal("exif_edited", software, {
                    IMAGE_PHOTO_EDITED: 0.35,
                }))
                break

    # GPS
    gps_info = exif.get(0x8825)
    if gps_info:
        ctx.signals.append(Signal("exif_gps_present", True, {
            IMAGE_PHOTO_CAMERA: 0.15,
            IMAGE_PHOTO_PHONE: 0.15,
            IMAGE_SCREENSHOT: -0.2,
            IMAGE_MEME: -0.2,
        }))
        ctx.metadata["has_gps"] = True

    # DateTime
    datetime_original = exif.get(0x9003)
    if datetime_original:
        ctx.metadata["exif_datetime"] = datetime_original
        ctx.signals.append(Signal("exif_datetime", datetime_original, {
            IMAGE_PHOTO_CAMERA: 0.1,
            IMAGE_PHOTO_PHONE: 0.1,
        }))


def analyze(ctx: AnalysisContext):
    """Full image analysis using Pillow."""
    try:
        from PIL import Image
        img = Image.open(ctx.path)
    except Exception:
        return

    w, h = img.size
    ctx.metadata["width"] = w
    ctx.metadata["height"] = h
    ctx.metadata["aspect_ratio"] = round(w / h, 2) if h > 0 else 0

    # Dimension analysis
    is_screen, is_mobile = _matches_screen_resolution(w, h)
    if is_screen:
        if is_mobile:
            ctx.signals.append(Signal("screen_resolution_mobile", (w, h), {
                IMAGE_SCREENSHOT_MOBILE: 0.35,
                IMAGE_SCREENSHOT: 0.2,
            }))
        else:
            ctx.signals.append(Signal("screen_resolution_desktop", (w, h), {
                IMAGE_SCREENSHOT: 0.35,
            }))

    if max(w, h) < 256:
        ctx.signals.append(Signal("tiny_image", (w, h), {
            IMAGE_ICON: 0.4,
        }))
    elif max(w, h) < 512:
        ctx.signals.append(Signal("small_image", (w, h), {
            IMAGE_THUMBNAIL: 0.25,
        }))

    aspect = w / h if h > 0 else 1
    if aspect > 2.5 or (h > 0 and w / h < 0.4):
        ctx.signals.append(Signal("extreme_aspect_ratio", aspect, {
            IMAGE_PANORAMA: 0.5,
        }))

    # Animated GIF — definitive
    if getattr(img, "is_animated", False) or getattr(img, "n_frames", 1) > 1:
        ctx.signals.append(Signal("animated_frames", img.n_frames, {
            IMAGE_GIF_ANIMATED: 0.8,
        }))
        img.close()
        return  # no need for further analysis

    # Alpha channel (PNG with transparency)
    if img.mode in ("RGBA", "PA", "LA"):
        color_stats = _compute_color_stats(img)
        if color_stats["unique_colors"] < 1000:
            ctx.signals.append(Signal("png_alpha_few_colors", color_stats, {
                IMAGE_GRAPHIC_DESIGN: 0.25,
                IMAGE_ICON: 0.1,
            }))

    # Entropy
    try:
        entropy = _compute_entropy(img)
        ctx.metadata["entropy"] = round(entropy, 2)

        if entropy < 4.0:
            ctx.signals.append(Signal("very_low_entropy", entropy, {
                IMAGE_DIAGRAM: 0.35,
                IMAGE_ICON: 0.15,
            }))
        elif entropy < 6.5:
            ctx.signals.append(Signal("low_entropy", entropy, {
                IMAGE_SCREENSHOT: 0.15,
                IMAGE_GRAPHIC_DESIGN: 0.1,
            }))
        elif entropy > 8.5:
            ctx.signals.append(Signal("high_entropy", entropy, {
                IMAGE_PHOTO_CAMERA: 0.15,
                IMAGE_PHOTO_PHONE: 0.1,
            }))
    except Exception:
        pass

    # Color stats
    try:
        color_stats = _compute_color_stats(img)
        ctx.metadata["unique_colors"] = color_stats["unique_colors"]
        ctx.metadata["white_gray_ratio"] = round(color_stats["white_gray_ratio"], 2)

        if color_stats["white_gray_ratio"] > 0.6:
            ctx.signals.append(Signal("mostly_white", color_stats["white_gray_ratio"], {
                IMAGE_SCREENSHOT: 0.2,
                IMAGE_DIAGRAM: 0.2,
                IMAGE_SCAN: 0.15,
            }))
        if color_stats["unique_colors"] < 50:
            ctx.signals.append(Signal("very_few_colors", color_stats["unique_colors"], {
                IMAGE_DIAGRAM: 0.3,
                IMAGE_ICON: 0.2,
            }))
        elif color_stats["unique_colors"] < 500:
            ctx.signals.append(Signal("few_colors", color_stats["unique_colors"], {
                IMAGE_GRAPHIC_DESIGN: 0.15,
            }))
    except Exception:
        pass

    # EXIF
    _analyze_exif(img, ctx)

    img.close()
