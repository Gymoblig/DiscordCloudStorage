"""File card and folder card widgets for the grid."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from metadata import FileEntry
from storage import FolderInfo, category_for, human_size
from ui.icons import get_icon
from ui.theme import (
    ACCENT_FG,
    BG_ELEV,
    BG_ELEV2,
    BG_HOVER,
    BORDER,
    BORDER_HOVER,
    FONT_FAMILY,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
)

CARD_W = 200
CARD_H = 220


class FileCard(ctk.CTkFrame):
    WIDTH = CARD_W
    HEIGHT = CARD_H

    def __init__(
        self,
        master,
        entry: FileEntry,
        on_download: Callable[[FileEntry], None],
        on_delete: Callable[[FileEntry], None],
    ):
        super().__init__(
            master,
            width=self.WIDTH,
            height=self.HEIGHT,
            fg_color=BG_ELEV,
            border_color=BORDER,
            border_width=1,
            corner_radius=14,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.entry = entry

        icon = get_icon(category_for(entry.name), size=56)
        self._icon = ctk.CTkLabel(self, text="", image=icon)
        self._icon.pack(pady=(22, 10))

        display = entry.name if len(entry.name) <= 24 else entry.name[:21] + "..."
        self._name = ctk.CTkLabel(
            self, text=display, text_color=TEXT, font=(FONT_FAMILY, 12, "bold"),
        )
        self._name.pack(padx=10)

        date = datetime.fromtimestamp(entry.created).strftime("%Y-%m-%d")
        self._meta = ctk.CTkLabel(
            self,
            text=f"{human_size(entry.size)}  ·  {date}",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 10),
        )
        self._meta.pack(padx=10, pady=(2, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_row,
            text="Download",
            height=30,
            fg_color=TEXT,
            text_color=ACCENT_FG,
            hover_color="#cfcfcf",
            font=(FONT_FAMILY, 11, "bold"),
            corner_radius=8,
            command=lambda: on_download(entry),
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="x",
            height=30,
            width=34,
            fg_color=BG_ELEV2,
            text_color=TEXT,
            hover_color="#3a1a1a",
            font=(FONT_FAMILY, 14, "bold"),
            corner_radius=8,
            command=lambda: on_delete(entry),
        ).pack(side="right")

        for w in (self, self._icon, self._name, self._meta):
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)

    def _hover_in(self, _e):
        self.configure(border_color=BORDER_HOVER, fg_color=BG_HOVER)

    def _hover_out(self, _e):
        self.configure(border_color=BORDER, fg_color=BG_ELEV)


class FolderCard(ctk.CTkFrame):
    WIDTH = CARD_W
    HEIGHT = CARD_H

    def __init__(
        self,
        master,
        info: FolderInfo,
        on_open: Callable[[FolderInfo], None],
        on_delete: Callable[[FolderInfo], None],
    ):
        super().__init__(
            master,
            width=self.WIDTH,
            height=self.HEIGHT,
            fg_color=BG_ELEV,
            border_color=BORDER,
            border_width=1,
            corner_radius=14,
        )
        self.pack_propagate(False)
        self.grid_propagate(False)

        self.info = info

        icon = get_icon("folder", size=56)
        self._icon = ctk.CTkLabel(self, text="", image=icon)
        self._icon.pack(pady=(22, 10))

        display = info.name if len(info.name) <= 24 else info.name[:21] + "..."
        self._name = ctk.CTkLabel(
            self, text=display, text_color=TEXT, font=(FONT_FAMILY, 12, "bold"),
        )
        self._name.pack(padx=10)

        sub = f"{info.file_count} file(s)"
        if info.total_size > 0:
            sub += f"  ·  {human_size(info.total_size)}"
        self._meta = ctk.CTkLabel(
            self, text=sub, text_color=TEXT_MUTED, font=(FONT_FAMILY, 10),
        )
        self._meta.pack(padx=10, pady=(2, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=10, pady=10)

        ctk.CTkButton(
            btn_row,
            text="Open",
            height=30,
            fg_color=TEXT,
            text_color=ACCENT_FG,
            hover_color="#cfcfcf",
            font=(FONT_FAMILY, 11, "bold"),
            corner_radius=8,
            command=lambda: on_open(info),
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        ctk.CTkButton(
            btn_row,
            text="x",
            height=30,
            width=34,
            fg_color=BG_ELEV2,
            text_color=TEXT,
            hover_color="#3a1a1a",
            font=(FONT_FAMILY, 14, "bold"),
            corner_radius=8,
            command=lambda: on_delete(info),
        ).pack(side="right")

        # double-click to open
        for w in (self, self._icon, self._name, self._meta):
            w.bind("<Double-Button-1>", lambda _e: on_open(info))
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)

    def _hover_in(self, _e):
        self.configure(border_color=BORDER_HOVER, fg_color=BG_HOVER)

    def _hover_out(self, _e):
        self.configure(border_color=BORDER, fg_color=BG_ELEV)
