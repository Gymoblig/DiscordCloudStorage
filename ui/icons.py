"""Programmatic B&W icon generation. No external PNGs needed."""
from __future__ import annotations

import sys
from functools import lru_cache

import customtkinter as ctk
from PIL import Image, ImageDraw, ImageFont

SZ = 128
WHITE = (255, 255, 255, 220)
SOFT = (255, 255, 255, 160)
MUTED = (180, 180, 180, 140)
DARK = (40, 40, 40, 240)

_img_cache: dict[str, ctk.CTkImage] = {}


@lru_cache(maxsize=4)
def _font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates: list[str] = []
    if sys.platform == "win32":
        candidates = [
            "C:/Windows/Fonts/segoeuib.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arialbd.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _new() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    img = Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def _center_text(d: ImageDraw.ImageDraw, text: str, size: int, fill=DARK, y_offset: int = 0):
    f = _font(size)
    bbox = d.textbbox((0, 0), text, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SZ - tw) // 2
    y = (SZ - th) // 2 + y_offset
    d.text((x, y), text, fill=fill, font=f)


def _page(d: ImageDraw.ImageDraw):
    d.rounded_rectangle((30, 12, 98, 116), radius=8, fill=WHITE)


# ---- Individual icon generators -----------------------------------

def _gen_folder() -> Image.Image:
    img, d = _new()
    d.rounded_rectangle((16, 30, 56, 46), radius=5, fill=WHITE)
    d.rounded_rectangle((16, 42, 112, 100), radius=8, fill=WHITE)
    d.line((16, 52, 112, 52), fill=MUTED, width=1)
    return img


def _gen_default() -> Image.Image:
    img, d = _new()
    _page(d)
    for y in range(44, 92, 10):
        w = 44 if y < 84 else 28
        d.rounded_rectangle((42, y, 42 + w, y + 3), radius=1, fill=MUTED)
    return img


def _gen_pdf() -> Image.Image:
    img, d = _new()
    _page(d)
    _center_text(d, "PDF", 24, y_offset=4)
    return img


def _gen_word() -> Image.Image:
    img, d = _new()
    _page(d)
    _center_text(d, "W", 36, y_offset=4)
    return img


def _gen_ppt() -> Image.Image:
    img, d = _new()
    _page(d)
    _center_text(d, "P", 36, y_offset=4)
    return img


def _gen_code() -> Image.Image:
    img, d = _new()
    _page(d)
    _center_text(d, "</>", 22, y_offset=4)
    return img


def _gen_zip() -> Image.Image:
    img, d = _new()
    _page(d)
    cx = 64
    for y in range(28, 100, 10):
        off = 6 if (y // 10) % 2 == 0 else -6
        d.rounded_rectangle((cx + off - 4, y, cx + off + 4, y + 6), radius=2, fill=MUTED)
    return img


def _gen_image() -> Image.Image:
    img, d = _new()
    d.rounded_rectangle((18, 24, 110, 104), radius=10, fill=WHITE)
    d.ellipse((30, 34, 50, 54), fill=SOFT)
    d.polygon([(26, 96), (56, 58), (86, 82), (106, 62), (106, 96)], fill=MUTED)
    return img


def _gen_audio() -> Image.Image:
    img, d = _new()
    d.ellipse((24, 16, 104, 96), outline=WHITE, width=4)
    d.ellipse((44, 62, 60, 78), fill=WHITE)
    d.ellipse((66, 54, 82, 70), fill=WHITE)
    d.rectangle((58, 32, 62, 68), fill=WHITE)
    d.rectangle((80, 26, 84, 60), fill=WHITE)
    d.line((60, 32, 82, 26), fill=WHITE, width=3)
    return img


def _gen_video() -> Image.Image:
    img, d = _new()
    d.rounded_rectangle((16, 26, 112, 102), radius=12, fill=WHITE)
    d.polygon([(52, 46), (52, 82), (84, 64)], fill=DARK)
    return img


def _gen_excel() -> Image.Image:
    img, d = _new()
    _page(d)
    _center_text(d, "X", 36, y_offset=4)
    return img


_GENERATORS: dict[str, callable] = {
    "folder":  _gen_folder,
    "default": _gen_default,
    "pdf":     _gen_pdf,
    "word":    _gen_word,
    "ppt":     _gen_ppt,
    "code":    _gen_code,
    "zip":     _gen_zip,
    "image":   _gen_image,
    "audio":   _gen_audio,
    "video":   _gen_video,
    "excel":   _gen_excel,
}


def _create_icon(name: str) -> Image.Image:
    gen = _GENERATORS.get(name, _GENERATORS["default"])
    return gen()


def get_icon(name: str, size: int = 48) -> ctk.CTkImage:
    key = f"{name}_{size}"
    if key in _img_cache:
        return _img_cache[key]
    img = _create_icon(name)
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    _img_cache[key] = ctk_img
    return ctk_img
