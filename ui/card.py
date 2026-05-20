"""File card widget shown in the grid."""
from __future__ import annotations

from datetime import datetime
from typing import Callable

import customtkinter as ctk

from metadata import FileEntry
from storage import category_for, human_size
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
    TEXT_MUTED,
)


class FileCard(ctk.CTkFrame):
    WIDTH = 200
    HEIGHT = 220

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
        self.on_download = on_download
        self.on_delete = on_delete

        icon = get_icon(category_for(entry.name), size=56)
        self.icon_label = ctk.CTkLabel(self, text="", image=icon)
        self.icon_label.pack(pady=(22, 10))

        display_name = entry.name if len(entry.name) <= 24 else entry.name[:21] + "..."
        self.name_label = ctk.CTkLabel(
            self,
            text=display_name,
            text_color=TEXT,
            font=(FONT_FAMILY, 12, "bold"),
        )
        self.name_label.pack(padx=10)

        date = datetime.fromtimestamp(entry.created).strftime("%Y-%m-%d")
        meta = f"{human_size(entry.size)}  ·  {date}"
        self.meta_label = ctk.CTkLabel(
            self,
            text=meta,
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 10),
        )
        self.meta_label.pack(padx=10, pady=(2, 8))

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(side="bottom", fill="x", padx=10, pady=10)

        self.dl_btn = ctk.CTkButton(
            btn_row,
            text="Download",
            height=30,
            fg_color=TEXT,
            text_color=ACCENT_FG,
            hover_color="#cfcfcf",
            font=(FONT_FAMILY, 11, "bold"),
            corner_radius=8,
            command=lambda: self.on_download(self.entry),
        )
        self.dl_btn.pack(side="left", expand=True, fill="x", padx=(0, 6))

        self.del_btn = ctk.CTkButton(
            btn_row,
            text="×",
            height=30,
            width=34,
            fg_color=BG_ELEV2,
            text_color=TEXT,
            hover_color="#3a1a1a",
            font=(FONT_FAMILY, 16, "bold"),
            corner_radius=8,
            command=lambda: self.on_delete(self.entry),
        )
        self.del_btn.pack(side="right")

        for w in (self, self.icon_label, self.name_label, self.meta_label):
            w.bind("<Enter>", self._hover_in)
            w.bind("<Leave>", self._hover_out)

    def _hover_in(self, _event):
        self.configure(border_color=BORDER_HOVER, fg_color=BG_HOVER)

    def _hover_out(self, _event):
        self.configure(border_color=BORDER, fg_color=BG_ELEV)
