#!/usr/bin/env python3
"""Generate Stoa brand logo derivatives from source files."""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
LOGOS = ROOT / "public" / "images" / "logos"
SOURCE = LOGOS / "source"
APP = ROOT / "src" / "app"
PUBLIC = ROOT / "public"

TAGLINE = "Know your market. Ship faster."
BG = (248, 246, 242)  # #F8F6F2 — marketing/product surface
INK = (20, 20, 26)  # #14141A
MUTED = (107, 111, 125)  # #6B6F7D

SOURCE_STEMS = {
    "icon": "stoa-icon-1x1",
    "logo": "stoa-logo-horizontal",
}


def open_source(stem: str) -> Image.Image:
    for ext in (".jpeg", ".jpg", ".png", ".webp"):
        path = SOURCE / f"{stem}{ext}"
        if path.exists():
            return Image.open(path)
    raise FileNotFoundError(
        f"Missing source asset '{stem}' in {SOURCE}. "
        f"Expected one of: {stem}.jpeg, {stem}.jpg, {stem}.png"
    )


def remove_theme_bg(
    img: Image.Image,
    bg: tuple[int, int, int] = BG,
    tolerance: int = 20,
) -> Image.Image:
    """Make pixels near the app surface color transparent."""
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


def write_png_rgba(path: Path, width: int, height: int, rgba: bytes) -> None:
    # Minimal PNG writer for ICO composition without Pillow ICO limitations.
    raw = b""
    row_bytes = width * 4
    for y in range(height):
        raw += b"\x00" + rgba[y * row_bytes : (y + 1) * row_bytes]
    compressed = zlib.compress(raw, 9)
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n"
    png += write_png_chunk(b"IHDR", ihdr)
    png += write_png_chunk(b"IDAT", compressed)
    png += write_png_chunk(b"IEND", b"")
    path.write_bytes(png)


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
    canvas = Image.new("RGB", (1200, 675), BG)
    draw = ImageDraw.Draw(canvas)

    # Subtle radial-ish gradient bands
    for i in range(675):
        t = i / 675
        shade = tuple(int(BG[j] * (1 - 0.04 * (0.5 - abs(t - 0.5) * 2))) for j in range(3))
        draw.line([(0, i), (1200, i)], fill=shade)

    logo_h = 112
    logo_resized = resize_height(logo, logo_h)
    logo_w = logo_resized.width

    tag_font = load_font(28, bold=False)
    tag_bbox = draw.textbbox((0, 0), TAGLINE, font=tag_font)
    tag_w = tag_bbox[2] - tag_bbox[0]
    tag_h = tag_bbox[3] - tag_bbox[1]

    gap = 32
    block_h = logo_h + gap + tag_h
    block_top = (675 - block_h) // 2

    logo_x = (1200 - logo_w) // 2
    logo_y = block_top
    canvas.paste(logo_resized, (logo_x, logo_y), logo_resized)

    tag_x = (1200 - tag_w) // 2
    tag_y = logo_y + logo_h + gap
    draw.text((tag_x, tag_y), TAGLINE, font=tag_font, fill=MUTED)

    return canvas


def main() -> None:
    icon_src = open_source(SOURCE_STEMS["icon"])
    logo_src = open_source(SOURCE_STEMS["logo"])

    icon = trim_transparent(remove_theme_bg(icon_src))
    logo = trim_transparent(remove_theme_bg(logo_src))

    # Master assets (512px height — matches icon master for crisp downscales)
    icon_master = resize_height(icon, 512)
    logo_master = resize_height(logo, 512)
    save_png(icon_master, LOGOS / "stoa-icon.png")
    save_webp(icon_master, LOGOS / "stoa-icon.webp", quality=95, method=6)
    save_png(logo_master, LOGOS / "stoa-logo.png")
    save_webp(logo_master, LOGOS / "stoa-logo.webp", quality=100, lossless=True)

    # Icon sizes (1.5–2× typical display for retina)
    for size in (32, 48, 80):
        sized = resize_height(icon, size)
        save_webp(sized, LOGOS / f"stoa-icon-{size}.webp", quality=95, method=6)

    icon_180 = resize_height(icon, 180)
    icon_512 = resize_height(icon, 512)
    save_png(icon_180, LOGOS / "stoa-icon-180.png")
    save_png(icon_512, LOGOS / "stoa-icon-512.png")

    # Logo sizes at 2× display height for retina (text needs extra pixels)
    logo_display_heights = {"sm": 36, "md": 44, "lg": 56}
    for name, display_h in logo_display_heights.items():
        export_h = display_h * 2
        sized = resize_height(logo, export_h)
        save_webp(sized, LOGOS / f"stoa-logo-{name}.webp", quality=100, lossless=True)
        save_png(sized, LOGOS / f"stoa-logo-{name}.png")

    # Favicon
    icon_32 = resize_height(icon, 32)
    save_png(icon_32, LOGOS / "favicon-32.png")
    save_ico([(16, icon), (32, icon), (48, icon)], APP / "favicon.ico")

    # Next.js app icons
    save_png(resize_height(icon, 32), APP / "icon.png")
    save_png(icon_180, APP / "apple-icon.png")

    # OG image
    og = build_og_image(logo)
    save_webp(og, LOGOS / "og-stoa.webp", quality=92, method=6)

    print("Generated brand assets in", LOGOS)


if __name__ == "__main__":
    main()
