"""Icon loader with PIL-backed caching."""
from __future__ import annotations

from pathlib import Path

import customtkinter as ctk
from PIL import Image

ICONS_DIR = Path(__file__).resolve().parent.parent / "icons"
_cache: dict[str, ctk.CTkImage] = {}


def get_icon(name: str, size: int = 48) -> ctk.CTkImage:
    key = f"{name}_{size}"
    if key in _cache:
        return _cache[key]

    path = ICONS_DIR / f"{name}.png"
    if not path.exists():
        path = ICONS_DIR / "default.png"

    img = Image.open(path).convert("RGBA")
    ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))
    _cache[key] = ctk_img
    return ctk_img
