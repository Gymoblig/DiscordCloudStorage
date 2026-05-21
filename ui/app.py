"""Main application window with folder navigation."""
from __future__ import annotations

import os
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from tkinterdnd2 import DND_FILES, TkinterDnD

from bot import CloudBot
from metadata import FileEntry
from storage import FolderInfo, files_at, folders_at, join_path
from ui.card import CARD_W, FileCard, FolderCard
from ui.dialogs import FolderDialog
from ui.theme import (
    ACCENT_FG,
    BG,
    BG_ELEV,
    BG_ELEV2,
    BG_HOVER,
    BORDER,
    FONT_FAMILY,
    TEXT,
    TEXT_DIM,
    TEXT_MUTED,
)

_ICO_PATH = Path(__file__).resolve().parent.parent / "icons" / "icon.ico"


class _CtkDndRoot(ctk.CTk, TkinterDnD.DnDWrapper):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.TkdndVersion = TkinterDnD._require(self)


class App(_CtkDndRoot):
    CARD_GAP = 12

    def __init__(self, bot: CloudBot):
        super().__init__()
        self.bot = bot
        self.current_path: str = ""

        ctk.set_appearance_mode("dark")
        self.configure(fg_color=BG)
        self.title("Discord Cloud Storage")
        self.geometry("1120x720")
        self.minsize(820, 520)
        self.after(50, lambda: self.state("zoomed"))

        if _ICO_PATH.exists():
            self.after(100, lambda: self.iconbitmap(str(_ICO_PATH)))

        self._widgets: list[ctk.CTkBaseClass] = []
        self._last_cols = 0

        self._build_ui()
        self._wire_bot()

        self.drop_target_register(DND_FILES)
        self.dnd_bind("<<Drop>>", self._on_drop)

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Configure>", self._on_resize)

    # ---- UI construction ------------------------------------------

    def _build_ui(self) -> None:
        # -- Header
        header = ctk.CTkFrame(self, fg_color=BG, height=64, corner_radius=0)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        ctk.CTkLabel(
            header, text="CLOUD  STORAGE",
            text_color=TEXT, font=(FONT_FAMILY, 18, "bold"),
        ).pack(side="left", padx=24)

        self.status_dot = ctk.CTkLabel(
            header, text="*", text_color=TEXT_DIM, font=(FONT_FAMILY, 14),
        )
        self.status_dot.pack(side="right", padx=(0, 8))
        self.status_label = ctk.CTkLabel(
            header, text="Connecting...",
            text_color=TEXT_MUTED, font=(FONT_FAMILY, 12),
        )
        self.status_label.pack(side="right", padx=(24, 0))

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # -- Toolbar
        toolbar = ctk.CTkFrame(self, fg_color=BG, height=72, corner_radius=0)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        self.upload_btn = ctk.CTkButton(
            toolbar, text="+  Upload", command=self._on_upload_click,
            fg_color=TEXT, text_color=ACCENT_FG, hover_color="#cfcfcf",
            font=(FONT_FAMILY, 13, "bold"), height=38, width=120, corner_radius=10,
        )
        self.upload_btn.pack(side="left", padx=(24, 8), pady=17)

        self.folder_btn = ctk.CTkButton(
            toolbar, text="+  Folder", command=self._on_new_folder,
            fg_color=BG_ELEV, text_color=TEXT, hover_color=BG_HOVER,
            border_width=1, border_color=BORDER,
            font=(FONT_FAMILY, 13), height=38, width=110, corner_radius=10,
        )
        self.folder_btn.pack(side="left", padx=(0, 8), pady=17)

        self.refresh_btn = ctk.CTkButton(
            toolbar, text="Refresh", command=self._on_refresh_click,
            fg_color=BG_ELEV, text_color=TEXT, hover_color=BG_HOVER,
            border_width=1, border_color=BORDER,
            font=(FONT_FAMILY, 13), height=38, width=96, corner_radius=10,
        )
        self.refresh_btn.pack(side="left", pady=17)

        self.search_entry = ctk.CTkEntry(
            toolbar, placeholder_text="Search files...",
            fg_color=BG_ELEV, text_color=TEXT, border_color=BORDER, border_width=1,
            font=(FONT_FAMILY, 12), height=38, width=260, corner_radius=10,
        )
        self.search_entry.pack(side="right", padx=24, pady=17)
        self.search_entry.bind("<KeyRelease>", lambda _e: self._render_grid())

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).pack(fill="x")

        # -- Breadcrumb bar
        self.breadcrumb_frame = ctk.CTkFrame(self, fg_color=BG, height=40, corner_radius=0)
        self.breadcrumb_frame.pack(fill="x", side="top")
        self.breadcrumb_frame.pack_propagate(False)
        self._breadcrumb_inner = ctk.CTkFrame(self.breadcrumb_frame, fg_color="transparent")
        self._breadcrumb_inner.pack(side="left", padx=24, fill="y")

        # -- Grid area
        self.scroll = ctk.CTkScrollableFrame(
            self, fg_color=BG, corner_radius=0,
            scrollbar_button_color=BG_HOVER,
            scrollbar_button_hover_color=BORDER,
        )
        self.scroll.pack(fill="both", expand=True, padx=12, pady=(4, 12))

        self.empty_label = ctk.CTkLabel(
            self.scroll,
            text="No files yet\n\nDrag files here or press  +  Upload",
            text_color=TEXT_DIM, font=(FONT_FAMILY, 14), justify="center",
        )

        # -- Status bar
        statusbar = ctk.CTkFrame(self, fg_color=BG_ELEV, height=30, corner_radius=0)
        statusbar.pack(fill="x", side="bottom")
        statusbar.pack_propagate(False)
        self.progress_label = ctk.CTkLabel(
            statusbar, text="", text_color=TEXT_MUTED, font=(FONT_FAMILY, 11),
        )
        self.progress_label.pack(side="left", padx=16)
        self.progress_bar = ctk.CTkProgressBar(
            statusbar, height=6, width=220, corner_radius=3,
            fg_color=BORDER, progress_color=TEXT, border_width=0,
        )
        self.progress_bar.set(0)
        # hidden by default — shown only during upload/download
        self.progress_pct = ctk.CTkLabel(
            statusbar, text="", text_color=TEXT_MUTED, font=(FONT_FAMILY, 11),
        )
        self.count_label = ctk.CTkLabel(
            statusbar, text="", text_color=TEXT_DIM, font=(FONT_FAMILY, 11),
        )
        self.count_label.pack(side="right", padx=16)

    # ---- Bot wiring -----------------------------------------------

    def _wire_bot(self) -> None:
        self.bot.on_status = lambda msg: self.after(0, lambda: self._set_status(msg))
        self.bot.on_error = lambda err: self.after(0, lambda: self._show_error(err))
        self.bot.on_ready = lambda: self.after(0, self._on_bot_ready)

    def _on_bot_ready(self) -> None:
        self._render_breadcrumb()
        self._render_grid()

    def _set_status(self, msg: str, connected: bool = True) -> None:
        self.status_label.configure(text=msg)
        self.status_dot.configure(text_color=TEXT if connected else TEXT_DIM)

    def _show_error(self, err: Exception) -> None:
        self._set_status(f"Error: {err}", connected=False)
        messagebox.showerror("Bot error", f"{type(err).__name__}: {err}")

    def _set_progress(self, msg: str) -> None:
        self.progress_label.configure(text=msg)

    def _show_progress_bar(self, value: float = 0, pct_text: str = "") -> None:
        """Show and update the progress bar. value: 0.0 - 1.0."""
        self.progress_bar.pack(side="left", padx=(0, 8))
        self.progress_pct.pack(side="left", padx=(0, 8))
        self.progress_bar.set(value)
        self.progress_pct.configure(text=pct_text)

    def _hide_progress_bar(self) -> None:
        self.progress_bar.pack_forget()
        self.progress_pct.pack_forget()
        self.progress_bar.set(0)

    # ---- Breadcrumb -----------------------------------------------

    def _render_breadcrumb(self) -> None:
        for w in self._breadcrumb_inner.winfo_children():
            w.destroy()

        parts: list[tuple[str, str]] = [("Home", "")]
        if self.current_path:
            segments = self.current_path.split("/")
            for i, seg in enumerate(segments):
                path = "/".join(segments[: i + 1])
                parts.append((seg, path))

        for idx, (label, path) in enumerate(parts):
            if idx > 0:
                ctk.CTkLabel(
                    self._breadcrumb_inner, text="  /  ",
                    text_color=TEXT_DIM, font=(FONT_FAMILY, 12),
                ).pack(side="left")

            is_active = idx == len(parts) - 1
            btn = ctk.CTkButton(
                self._breadcrumb_inner,
                text=label,
                fg_color="transparent",
                text_color=TEXT if is_active else TEXT_MUTED,
                hover_color=BG_HOVER,
                font=(FONT_FAMILY, 12, "bold" if is_active else "normal"),
                height=28,
                width=len(label) * 9 + 16,
                corner_radius=6,
                command=lambda p=path: self._navigate_to(p),
            )
            btn.pack(side="left")

    def _navigate_to(self, path: str) -> None:
        self.current_path = path
        self._render_breadcrumb()
        self._render_grid()

    # ---- Grid rendering -------------------------------------------

    def _render_grid(self) -> None:
        for w in self._widgets:
            w.destroy()
        self._widgets.clear()
        self.empty_label.pack_forget()

        query = self.search_entry.get().lower().strip()
        meta = self.bot.metadata

        if query:
            matched = [f for f in meta.files if query in f.name.lower()]
            folder_cards: list[FolderInfo] = []
            file_cards = matched
        else:
            folder_cards = folders_at(meta.files, meta.folders, self.current_path)
            file_cards = files_at(meta.files, self.current_path)
            file_cards.sort(key=lambda f: f.created, reverse=True)

        total = len(folder_cards) + len(file_cards)
        all_files = len(meta.files)
        if query:
            self.count_label.configure(text=f"{total} result(s) of {all_files} file(s)")
        else:
            self.count_label.configure(text=f"{total} item(s) here  |  {all_files} file(s) total")

        if total == 0:
            self.empty_label.pack(expand=True, pady=80)
            return

        cols = self._calc_cols()
        self._last_cols = cols
        idx = 0

        for info in folder_cards:
            card = FolderCard(
                self.scroll, info=info,
                on_open=self._on_open_folder,
                on_delete=self._on_delete_folder,
            )
            card.grid(
                row=idx // cols, column=idx % cols,
                padx=self.CARD_GAP // 2, pady=self.CARD_GAP // 2, sticky="n",
            )
            self._widgets.append(card)
            idx += 1

        for f in file_cards:
            card = FileCard(
                self.scroll, entry=f,
                on_download=self._on_download_card,
                on_delete=self._on_delete_card,
            )
            card.grid(
                row=idx // cols, column=idx % cols,
                padx=self.CARD_GAP // 2, pady=self.CARD_GAP // 2, sticky="n",
            )
            self._widgets.append(card)
            idx += 1

    def _calc_cols(self) -> int:
        """Calculate how many card columns fit, accounting for DPI scaling."""
        self.update_idletasks()
        window_w = self.winfo_width()
        if window_w <= 1:
            window_w = 1120
        # CustomTkinter scales widget dimensions by the Windows DPI factor.
        # CARD_W is the logical width, but physical pixels = CARD_W * scaling.
        try:
            scaling = ctk.ScalingTracker.get_widget_scaling(self)
        except Exception:
            scaling = 1.0
        # window_w from winfo_width() is in physical pixels.
        usable_phys = window_w - 80  # scroll padx + scrollbar + safety
        card_slot_phys = (CARD_W + self.CARD_GAP) * scaling
        return max(1, int(usable_phys / card_slot_phys))

    def _on_resize(self, event) -> None:
        if event.widget is not self or not self._widgets:
            return
        cols = self._calc_cols()
        if cols != self._last_cols:
            self._render_grid()

    # ---- Upload ---------------------------------------------------

    def _on_upload_click(self) -> None:
        paths = filedialog.askopenfilenames(title="Choose file(s) to upload")
        for p in paths:
            self._start_upload(p)

    def _start_upload(self, path: str) -> None:
        name = os.path.basename(path)
        self._set_status(f"Uploading {name}...")

        def progress(cur: int, total: int) -> None:
            pct = cur / total if total else 1
            self.after(0, lambda: (
                self._set_progress(f"Uploading {name}: {cur}/{total} chunks"),
                self._show_progress_bar(pct, f"{int(pct * 100)}%"),
            ))

        future = self.bot.submit(
            self.bot.upload(path, dest_folder=self.current_path, on_progress=progress)
        )

        def done(f) -> None:
            try:
                f.result()
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(f"Uploaded {name}"))
            except Exception as e:
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _start_upload_folder(self, path: str) -> None:
        name = os.path.basename(path)
        self._set_status(f"Uploading folder {name}...")

        def progress(cur: int, total: int, fname: str) -> None:
            pct = cur / total if total else 1
            self.after(0, lambda: (
                self._set_progress(f"Uploading {name}: {cur}/{total} files ({fname})"),
                self._show_progress_bar(pct, f"{int(pct * 100)}%"),
            ))

        future = self.bot.submit(
            self.bot.upload_folder(path, dest_folder=self.current_path, on_progress=progress)
        )

        def done(f) -> None:
            try:
                results = f.result()
                count = len(results)
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(
                    f"Uploaded folder {name} ({count} file(s))"
                ))
            except Exception as e:
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    # ---- Download -------------------------------------------------

    def _on_download_card(self, entry: FileEntry) -> None:
        dest = filedialog.asksaveasfilename(initialfile=entry.name, title="Save as...")
        if not dest:
            return
        self._set_status(f"Downloading {entry.name}...")

        def progress(cur: int, total: int) -> None:
            pct = cur / total if total else 1
            self.after(0, lambda: (
                self._set_progress(f"Downloading {entry.name}: {cur}/{total} chunks"),
                self._show_progress_bar(pct, f"{int(pct * 100)}%"),
            ))

        future = self.bot.submit(self.bot.download(entry.id, dest, on_progress=progress))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, lambda: self._set_status(f"Saved to {dest}"))
            except Exception as e:
                self.after(0, lambda: self._set_progress(""))
                self.after(0, self._hide_progress_bar)
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    # ---- Delete ---------------------------------------------------

    def _on_delete_card(self, entry: FileEntry) -> None:
        if not messagebox.askyesno(
            "Delete file",
            f"Delete '{entry.name}' from cloud storage?\n\nAll chunks will be removed from Discord.",
        ):
            return
        self._set_status(f"Deleting {entry.name}...")
        future = self.bot.submit(self.bot.delete(entry.id))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(f"Deleted {entry.name}"))
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    # ---- Folder actions -------------------------------------------

    def _on_open_folder(self, info: FolderInfo) -> None:
        self._navigate_to(info.path)

    def _on_new_folder(self) -> None:
        dialog = FolderDialog(self)
        name = dialog.result
        if not name:
            return
        name = name.replace("/", "-").replace("\\", "-")
        target = join_path(self.current_path, name)
        self._set_status(f"Creating folder {name}...")
        future = self.bot.submit(self.bot.create_folder(target))

        def done(f) -> None:
            try:
                f.result()
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(f"Created folder {name}"))
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    def _on_delete_folder(self, info: FolderInfo) -> None:
        msg = f"Delete folder '{info.name}'?"
        if info.file_count > 0:
            msg += f"\n\nThis will permanently delete {info.file_count} file(s) inside it."
        if not messagebox.askyesno("Delete folder", msg):
            return
        self._set_status(f"Deleting folder {info.name}...")
        future = self.bot.submit(self.bot.delete_folder(info.path))

        def done(f) -> None:
            try:
                count = f.result()
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(
                    f"Deleted folder {info.name} ({count} file(s) removed)"
                ))
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    # ---- Refresh --------------------------------------------------

    def _on_refresh_click(self) -> None:
        self._set_status("Refreshing...")
        future = self.bot.submit(self.bot.refresh())

        def done(f) -> None:
            try:
                f.result()
                self.after(0, self._render_grid)
                self.after(0, lambda: self._set_status(
                    f"Loaded {len(self.bot.metadata.files)} file(s)"
                ))
            except Exception as e:
                self.after(0, lambda: self._show_error(e))

        future.add_done_callback(done)

    # ---- Drag & drop ----------------------------------------------

    def _on_drop(self, event) -> None:
        try:
            paths = self.tk.splitlist(event.data)
        except Exception:
            paths = [event.data]
        for p in paths:
            p = p.strip().strip("{").strip("}")
            if os.path.isdir(p):
                self._start_upload_folder(p)
            elif os.path.isfile(p):
                self._start_upload(p)

    # ---- Shutdown -------------------------------------------------

    def _on_close(self) -> None:
        try:
            self.bot.shutdown()
        except Exception:
            pass
        self.destroy()
