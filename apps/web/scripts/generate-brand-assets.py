#!/usr/bin/env python3
"""Generate Stoa brand logo derivatives from V3 source JPEGs."""

from __future__ import annotations

import shutil
import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGOS = ROOT / "public" / "images" / "logos"
SOURCE = LOGOS / "source"
APP = ROOT / "src" / "app"
IMAGES = ROOT / "public" / "images"

TAGLINE = "Know your market. Ship faster."
SURFACE_LIGHT = (249, 248, 246)  # #F9F8F6 — marketing/product canvas
SURFACE_DARK = (20, 20, 20)  # #141414 — dark band
INK = (10, 10, 10)  # #0A0A0A
MUTED = (107, 107, 107)  # #6B6B6B

SOURCE_FILES = {
    "icon_light": IMAGES / "STOA_icon_light.jpeg",
    "icon_dark": IMAGES / "STOA_icon_dark.jpeg",
    "logo_light": IMAGES / "STOA_logo_light.jpeg",
    "logo_dark": IMAGES / "STOA_logo_dark.jpeg",
}


def open_rgb(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(f"Missing source asset: {path}")
    return Image.open(path).convert("RGB")


def key_color_to_alpha(
    img: Image.Image,
    bg: tuple[int, int, int],
    tolerance: int = 28,
) -> Image.Image:
    """Make pixels near a solid background color transparent."""
    img = img.convert("RGBA")
    pixels = img.load()
    width, height = img.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if (
                abs(r - bg[0]) <= tolerance
                and abs(g - bg[1]) <= tolerance
                and abs(b - bg[2]) <= tolerance
            ):
                pixels[x, y] = (r, g, b, 0)
    return img


def trim_transparent(img: Image.Image, padding: int = 8) -> Image.Image:
    bbox = img.getbbox()
    if not bbox:
        return img
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def resize_height(img: Image.Image, height: int) -> Image.Image:
    ratio = height / img.height
    width = max(1, round(img.width * ratio))
    return img.resize((width, height), Image.Resampling.LANCZOS)


def save_webp(img: Image.Image, path: Path, **kwargs) -> None:
    img.save(path, format="WEBP", **kwargs)


def save_png(img: Image.Image, path: Path) -> None:
    img.save(path, format="PNG", optimize=True)


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def write_png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + chunk_type + data + struct.pack(">I", crc)


def save_ico(images: list[tuple[int, Image.Image]], path: Path) -> None:
    entries = []
    image_data_list = []
    offset = 6 + 16 * len(images)

    for size, img in images:
        rgba_img = img.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS)
        png_path = path.with_suffix(f".{size}.tmp.png")
        save_png(rgba_img, png_path)
        png_bytes = png_path.read_bytes()
        png_path.unlink(missing_ok=True)
        entries.append((size, len(png_bytes), offset))
        image_data_list.append(png_bytes)
        offset += len(png_bytes)

    ico = bytearray()
    ico += struct.pack("<HHH", 0, 1, len(entries))
    for size, data_len, data_offset in entries:
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        ico += struct.pack("<BBBBHHII", width, height, 0, 0, 1, 32, data_len, data_offset)
    for data in image_data_list:
        ico += data
    path.write_bytes(ico)


def build_og_image(logo: Image.Image) -> Image.Image:
    canvas = Image.new("RGB", (1200, 675), SURFACE_LIGHT)
    draw = ImageDraw.Draw(canvas)

    for i in range(675):
        t = i / 675
        shade = tuple(int(SURFACE_LIGHT[j] * (1 - 0.03 * (0.5 - abs(t - 0.5) * 2))) for j in range(3))
        draw.line([(0, i), (1200, i)], fill=shade)

    logo_h = 96
    logo_resized = resize_height(logo, logo_h)
    logo_w = logo_resized.width

    tag_font = load_font(26, bold=False)
    tag_bbox = draw.textbbox((0, 0), TAGLINE, font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_h = tag_bbox[3] - tag_bbox[1]

    gap = 28
    block_h = logo_h + gap + tag_h
    block_top = (675 - block_h) // 2

    logo_x = (1200 - logo_w) // 2
    logo_y = block_top
    canvas.paste(logo_resized, (logo_x, logo_y), logo_resized)

    tag_x = (1200 - tag_w) // 2
    tag_y = logo_y + logo_h + gap
    draw.text((tag_x, tag_y), TAGLINE, font=tag_font, fill=MUTED)

    return canvas


def archive_sources() -> None:
    SOURCE.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_FILES["icon_light"], SOURCE / "stoa-icon-1x1.jpeg")
    shutil.copy2(SOURCE_FILES["logo_light"], SOURCE / "stoa-logo-horizontal.jpeg")
    shutil.copy2(SOURCE_FILES["icon_dark"], SOURCE / "stoa-icon-1x1-dark.jpeg")
    shutil.copy2(SOURCE_FILES["logo_dark"], SOURCE / "stoa-logo-horizontal-dark.jpeg")


def main() -> None:
    archive_sources()

    icon_light = trim_transparent(key_color_to_alpha(open_rgb(SOURCE_FILES["icon_light"]), SURFACE_LIGHT))
    icon_dark = trim_transparent(key_color_to_alpha(open_rgb(SOURCE_FILES["icon_dark"]), SURFACE_DARK, tolerance=35))
    logo_light = trim_transparent(key_color_to_alpha(open_rgb(SOURCE_FILES["logo_light"]), SURFACE_LIGHT))
    logo_dark = trim_transparent(key_color_to_alpha(open_rgb(SOURCE_FILES["logo_dark"]), SURFACE_DARK, tolerance=35))

    # Master assets
    icon_master = resize_height(icon_light, 512)
    logo_master = resize_height(logo_light, 256)
    save_png(icon_master, LOGOS / "stoa-icon.png")
    save_webp(icon_master, LOGOS / "stoa-icon.webp", quality=95, method=6)
    save_png(logo_master, LOGOS / "stoa-logo.png")
    save_webp(logo_master, LOGOS / "stoa-logo.webp", quality=100, lossless=True)

    # Light icon sizes (retina-friendly)
    for size in (32, 48, 80):
        sized = resize_height(icon_light, size)
        save_webp(sized, LOGOS / f"stoa-icon-{size}.webp", quality=95, method=6)

    icon_180 = resize_height(icon_light, 180)
    icon_512 = resize_height(icon_light, 512)
    save_png(icon_180, LOGOS / "stoa-icon-180.png")
    save_png(icon_512, LOGOS / "stoa-icon-512.png")

    # Dark-surface icon (white mark)
    for size in (32, 48, 80):
        sized = resize_height(icon_dark, size)
        save_webp(sized, LOGOS / f"stoa-icon-on-dark-{size}.webp", quality=95, method=6)
    save_webp(resize_height(icon_dark, 80), LOGOS / "stoa-icon-on-dark.webp", quality=95, method=6)

    # Logo sizes at 2× display height for retina
    logo_display_heights = {"sm": 36, "md": 44, "lg": 56}
    for name, display_h in logo_display_heights.items():
        export_h = display_h * 2
        sized = resize_height(logo_light, export_h)
        save_webp(sized, LOGOS / f"stoa-logo-{name}.webp", quality=100, lossless=True)
        save_png(sized, LOGOS / f"stoa-logo-{name}.png")

    # Dark-surface wordmark
    for name, display_h in logo_display_heights.items():
        export_h = display_h * 2
        sized = resize_height(logo_dark, export_h)
        save_webp(sized, LOGOS / f"stoa-logo-on-dark-{name}.webp", quality=100, lossless=True)
        save_png(sized, LOGOS / f"stoa-logo-on-dark-{name}.png")

    # Favicon + Next.js app icons (from light icon)
    icon_32 = resize_height(icon_light, 32)
    save_png(icon_32, LOGOS / "favicon-32.png")
    save_ico([(16, icon_light), (32, icon_light), (48, icon_light)], APP / "favicon.ico")
    save_png(resize_height(icon_light, 32), APP / "icon.png")
    save_png(icon_180, APP / "apple-icon.png")

    # OG image
    og = build_og_image(logo_light)
    save_webp(og, LOGOS / "og-stoa.webp", quality=92, method=6)

    print("Generated brand assets in", LOGOS)
    print(f"  icon light: {icon_light.width}x{icon_light.height}")
    print(f"  logo light: {logo_light.width}x{logo_light.height}")


if __name__ == "__main__":
    main()
