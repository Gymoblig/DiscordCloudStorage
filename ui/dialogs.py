"""Custom themed dialogs matching the B&W design."""
from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from ui.theme import (
    ACCENT_FG,
    BG,
    BG_ELEV,
    BG_HOVER,
    BORDER,
    FONT_FAMILY,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
)


class FolderDialog(ctk.CTkToplevel):
    """Modal dialog for creating a new folder."""

    def __init__(self, parent: ctk.CTkBaseClass):
        super().__init__(parent)
        self.result: Optional[str] = None

        self.title("New Folder")
        self.configure(fg_color=BG)
        self.geometry("400x200")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        # center on parent
        self.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w, h = 400, 200
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        # content
        ctk.CTkLabel(
            self,
            text="Create new folder",
            text_color=TEXT,
            font=(FONT_FAMILY, 16, "bold"),
        ).pack(padx=28, pady=(28, 4), anchor="w")

        ctk.CTkLabel(
            self,
            text="Enter a name for the new folder",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 12),
        ).pack(padx=28, pady=(0, 12), anchor="w")

        self.entry = ctk.CTkEntry(
            self,
            fg_color=BG_ELEV,
            text_color=TEXT,
            border_color=BORDER,
            border_width=1,
            placeholder_text="Folder name",
            font=(FONT_FAMILY, 13),
            height=38,
            corner_radius=8,
        )
        self.entry.pack(fill="x", padx=28, pady=(0, 16))
        self.entry.focus_set()

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=28, pady=(0, 20))

        ctk.CTkButton(
            btn_row,
            text="Cancel",
            fg_color=BG_ELEV,
            text_color=TEXT,
            hover_color=BG_HOVER,
            border_width=1,
            border_color=BORDER,
            font=(FONT_FAMILY, 13),
            height=36,
            width=100,
            corner_radius=8,
            command=self._cancel,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            btn_row,
            text="Create",
            fg_color=TEXT,
            text_color=ACCENT_FG,
            hover_color="#cfcfcf",
            font=(FONT_FAMILY, 13, "bold"),
            height=36,
            width=100,
            corner_radius=8,
            command=self._create,
        ).pack(side="right")

        self.bind("<Return>", lambda _e: self._create())
        self.bind("<Escape>", lambda _e: self._cancel())

        self.wait_window()

    def _create(self) -> None:
        val = self.entry.get().strip()
        if val:
            self.result = val
        self.destroy()

    def _cancel(self) -> None:
        self.result = None
        self.destroy()
