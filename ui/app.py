"""Main application window."""
from __future__ import annotations

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from bot import CloudBot
from metadata import FileEntry
from ui.card import FileCard
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


class _CtkDndRoot(ctk.CTk, TkinterDnD.DnDWrapper):
    """CustomTkinter root window with TkinterDnD2 drag-and-drop support."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class App(_CtkDndRoot):
    CARD_GAP = 12

    def __init__(self, bot: CloudBot):
        super().__init__()
        self.bot = bot

        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG)
        self.title("Discord Cloud Storage")
        self.geometry("1120x720")
        self.minsize(820, 520)

        self._cards: list[FileCard] = []
        self._last_cols = 0

        self._build_ui()
        self._wire_bot()

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_resize)

    # ---- UI construction ------------------------------------------

    def _build_ui(self) -> None:
        # ---- Header
        header = ctk.CTkFrame(self, fg_color=BG, height=64, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header,
            text="CLOUD  STORAGE",
            text_color=TEXT,
            font=(FONT_FAMILY, 18, "bold"),
        ).pack(side="left", padx=24)

        self.status_dot = ctk.CTkLabel(
            header, text="●", text_color=TEXT_DIM, font=(FONT_FAMILY, 14)
        )
        self.status_dot.pack(side="right", padx=(0, 8))
        self.status_label = ctk.CTkLabel(
            header,
            text="Connecting...",
            text_color=TEXT_MUTED,
            font=(FONT_FAMILY, 12),
        )
        self.status_label.pack(side="right", padx=(24, 0))

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # ---- Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=BG, height=72, corner_radius=0)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        self.upload_btn = ctk.CTkButton(
            toolbar,
            text="+  Upload",
            command=self._on_upload_click,
            fg_color=TEXT,
            text_color=ACCENT_FG,
            hover_color="#cfcfcf",
            font=(FONT_FAMILY, 13, "bold"),
            height=38,
            width=128,
            corner_radius=10,
        )
        self.upload_btn.pack(side="left", padx=(24, 8), pady=17)

        self.refresh_btn = ctk.CTkButton(
            toolbar,
            text="Refresh",
            command=self._on_refresh_click,
            fg_color=BG_ELEV,
            text_color=TEXT,
            hover_color=BG_HOVER,
            border_width=1,
            border_color=BORDER,
            font=(FONT_FAMILY, 13),
            height=38,
            width=104,
            corner_radius=10,
        )
        self.refresh_btn.pack(side="left", pady=17)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search files...",
            fg_color=BG_ELEV,
            text_color=TEXT,
            border_color=BORDER,
            border_width=1,
            font=(FONT_FAMILY, 12),
            height=38,
            width=260,
            corner_radius=10,
        )
        self.search_entry.pack(side="right", padx=24, pady=17)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._render_cards())

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # ---- Grid area
        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=BG,
            corner_radius=0,
            scrollbar_button_color=BG_HOVER,
            scrollbar_button_hover_color=BORDER,
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=12)

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="No files yet\n\nDrag files here or press  +  Upload",
            text_color=TEXT_DIM,
            font=(FONT_FAMILY, 14),
            justify="center",
        )

        # ---- Status bar
        statusbar = ctk.CTkFrame(self, fg_color=BG_ELEV, height=30, corner_radius=0)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)
        self.progress_label = ctk.CTkLabel(
            statusbar, text="", text_color=TEXT_MUTED, font=(FONT_FAMILY, 11)
        )
        self.progress_label.pack(side="left", padx=16)

        self.count_label = ctk.CTkLabel(
            statusbar, text="", text_color=TEXT_DIM, font=(FONT_FAMILY, 11)
        )
        self.count_label.pack(side="right", padx=16)

    # ---- Bot wiring -----------------------------------------------

    def _wire_bot(self) -> None:
        self.bot.on_status = lambda msg: self.after(0, lambda: self._set_status(msg))
        self.bot.on_error = lambda err: self.after(0, lambda: self._show_error(err))
        self.bot.on_ready = lambda: self.after(0, self._render_cards)

    def _set_status(self, msg: str, connected: bool = True) -> None:
        self.status_label.configure(text=msg)
        self.status_dot.configure(text_color=TEXT if connected else TEXT_DIM)

    def _show_error(self, err: Exception) -> None:
        self._set_status(f"Error: {err}", connected=False)
        messagebox.showerror("Bot error", f"{type(err).__name__}: {err}")

    def _set_progress(self, msg: str) -> None:
        self.progress_label.configure(text=msg)

    # ---- Rendering ------------------------------------------------

    def _render_cards(self) -> None:
        for c in self._cards:
            c.destroy()
        self._cards.clear()
        self.empty_label.pack_forget()

        files = list(self.bot.metadata.files)
        query = self.search_entry.get().lower().strip()
        if query:
            files = [f for f in files if query in f.name.lower()]
        files.sort(key=lambda f: f.created, reverse=True)

        total = len(self.bot.metadata.files)
        self.count_label.configure(
            text=f"{len(files)} of {total} file(s)" if query else f"{total} file(s)"
        )

        if not files:
            self.empty_label.pack(expand=True, pady=80)
            return

        width = self.scroll.winfo_width()
        if width <= 1:
            width = self.winfo_width() - 60
        cols = max(1, width // (FileCard.WIDTH + self.CARD_GAP))
        self._last_cols = cols

        for i, f in enumerate(files):
            card = FileCard(
                self.scroll,
                entry=f,
                on_download=self._on_download_card,
                on_delete=self._on_delete_card,
            )
            card.grid(
                row=i // cols,
                column=i % cols,
                padx=self.CARD_GAP // 2,
                pady=self.CARD_GAP // 2,
                sticky="n",
            )
            self._cards.append(card)

    def _on_resize(self, event) -> None:
        if event.widget is not self:
            return
        if not self._cards:
            return
        width = self.scroll.winfo_width()
        if width <= 1:
            return
        cols = max(1, width // (FileCard.WIDTH + self.CARD_GAP))
        if cols != self._last_cols:
            self._render_cards()

    # ---- Actions --------------------------------------------------

    def _on_upload_click(self) -> None:
        paths = filedialog.askopenfilenames(title="Choose file(s) to upload")
        for p in paths:
            self._start_upload(p)

    def _start_upload(self, path: str) -> None:
        name = os.path.basename(path)
        self._set_status(f"Uploading {name}...")

        def progress(cur: int, total: int) -> None:
            self.after(0, lambda: self._set_progress(f"Uploading {name}: {cur}/{total} chunks"))

        future = self.bot.submit(self.bot.upload(path, on_progress=progress))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._render_cards)
                self.after(0, lambda: self._set_status(f"Uploaded {name}"))
            except Exception as e:
                self.after(0, lambda: self._set_progress(""))
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _on_download_card(self, entry: FileEntry) -> None:
        dest = filedialog.asksaveasfilename(initialfile=entry.name, title="Save as...")
        if not dest:
            return
        self._set_status(f"Downloading {entry.name}...")

        def progress(cur: int, total: int) -> None:
            self.after(0, lambda: self._set_progress(f"Downloading {entry.name}: {cur}/{total} chunks"))

        future = self.bot.submit(self.bot.download(entry.id, dest, on_progress=progress))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, lambda: self._set_progress(""))
                self.after(0, lambda: self._set_status(f"Saved to {dest}"))
            except Exception as e:
                self.after(0, lambda: self._set_progress(""))
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _on_delete_card(self, entry: FileEntry) -> None:
        if not messagebox.askyesno(
            "Delete file",
            f"Delete '{entry.name}' from cloud storage?\n\nThis removes all chunks from Discord.",
        ):
            return
        self._set_status(f"Deleting {entry.name}...")
        future = self.bot.submit(self.bot.delete(entry.id))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, self._render_cards)
                self.after(0, lambda: self._set_status(f"Deleted {entry.name}"))
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _on_refresh_click(self) -> None:
        self._set_status("Refreshing...")
        future = self.bot.submit(self.bot.refresh())

        def done(f) -> None:
            try:
                f.result()
                self.after(0, self._render_cards)
                self.after(
                    0,
                    lambda: self._set_status(
                        f"Loaded {len(self.bot.metadata.files)} file(s)"
                    ),
                )
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _on_drop(self, event) -> None:
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            paths = [event.data]
        for p in paths:
            p = p.strip().strip("{").strip("}")
            if os.path.isfile(p):
                self._start_upload(p)

    # ---- Shutdown -------------------------------------------------

    def _on_close(self) -> None:
        try:
            self.bot.shutdown()
        except Exception:
            pass
        self.destroy()
