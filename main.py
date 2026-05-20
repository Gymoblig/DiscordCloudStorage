"""Entry point - launches Discord bot + UI together."""
from __future__ import annotations

import json
import sys
from pathlib import Path
from tkinter import messagebox

from bot import CloudBot
from ui.app import App

ROOT = Path(__file__).resolve().parent
CONFIG_PATH = ROOT / "config.json"
TOKEN_PATH = ROOT / "token.txt"


def _fatal(msg: str) -> None:
    try:
        messagebox.showerror("Discord Cloud Storage", msg)
    except Exception:
        pass
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_config() -> tuple[str, int, int]:
    if not TOKEN_PATH.exists():
        _fatal(f"Missing token.txt next to main.py.\nExpected at: {TOKEN_PATH}")
    token = TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not token:
        _fatal("token.txt is empty.")

    if not CONFIG_PATH.exists():
        _fatal(f"Missing config.json next to main.py.\nExpected at: {CONFIG_PATH}")
    try:
        cfg = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        _fatal(f"config.json is not valid JSON: {e}")

    channel_id = cfg.get("discord_channel_id")
    if not isinstance(channel_id, int) or channel_id <= 0:
        _fatal(
            "config.json must contain a numeric 'discord_channel_id'.\n"
            "Enable Developer Mode in Discord, right-click your storage channel,\n"
            "and choose 'Copy Channel ID'."
        )

    chunk_mb = cfg.get("chunk_size_mb", 25)
    if not isinstance(chunk_mb, int) or chunk_mb <= 0:
        chunk_mb = 25

    return token, channel_id, chunk_mb


def main() -> None:
    token, channel_id, chunk_mb = load_config()
    bot = CloudBot(token=token, channel_id=channel_id, chunk_size_mb=chunk_mb)
    bot.start()
    app = App(bot)
    app.mainloop()


if __name__ == "__main__":
    main()
