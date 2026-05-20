"""Discord bot client running in a background asyncio thread."""
from __future__ import annotations

import asyncio
import io
import os
import threading
import time
import uuid
from pathlib import Path
from typing import Callable, Optional

import discord

from metadata import FileEntry, Metadata, load_metadata, save_metadata
from storage import (
    chunk_size_bytes,
    count_chunks,
    iter_chunks,
    join_path,
    normalize_path,
)

ChunkProgressCb = Optional[Callable[[int, int], None]]
FolderProgressCb = Optional[Callable[[int, int, str], None]]
StatusCb = Optional[Callable[[str], None]]
ErrorCb = Optional[Callable[[Exception], None]]
ReadyCb = Optional[Callable[[], None]]


class CloudBot:
    def __init__(self, token: str, channel_id: int, chunk_size_mb: int = 25):
        self.token = token
        self.channel_id = channel_id
        self.chunk_size = chunk_size_bytes(chunk_size_mb)

        intents = discord.Intents.default()
        intents.message_content = True
        self.client = discord.Client(intents=intents)

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.thread: Optional[threading.Thread] = None
        self.channel: Optional[discord.TextChannel] = None
        self.metadata = Metadata()
        self._metadata_msg: Optional[discord.Message] = None
        self._write_lock: Optional[asyncio.Lock] = None

        self.on_ready: ReadyCb = None
        self.on_status: StatusCb = None
        self.on_error: ErrorCb = None

        @self.client.event
        async def on_ready():
            self._write_lock = asyncio.Lock()
            try:
                ch = self.client.get_channel(channel_id) or await self.client.fetch_channel(channel_id)
                if not isinstance(ch, discord.TextChannel):
                    raise RuntimeError("Configured channel is not a text channel")
                self.channel = ch
                self._status(f"Loading metadata from #{ch.name}...")
                self.metadata, self._metadata_msg = await load_metadata(ch)
                self._status(
                    f"Connected as {self.client.user} - {len(self.metadata.files)} file(s)"
                )
                if self.on_ready:
                    self.on_ready()
            except Exception as e:
                self._error(e)

    def _status(self, msg: str) -> None:
        if self.on_status:
            self.on_status(msg)

    def _error(self, err: Exception) -> None:
        if self.on_error:
            self.on_error(err)

    # ---- lifecycle ------------------------------------------------

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, daemon=True, name="discord-bot")
        self.thread.start()

    def _run(self) -> None:
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        try:
            self.loop.run_until_complete(self.client.start(self.token))
        except Exception as e:
            self._error(e)
        finally:
            try:
                self.loop.run_until_complete(self.loop.shutdown_asyncgens())
            except Exception:
                pass
            self.loop.close()

    def shutdown(self) -> None:
        if self.loop and not self.loop.is_closed():
            asyncio.run_coroutine_threadsafe(self.client.close(), self.loop)

    def submit(self, coro):
        if self.loop is None:
            raise RuntimeError("Bot loop not running")
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    # ---- file operations ------------------------------------------

    async def upload(
        self,
        local_path: str,
        dest_folder: str = "",
        on_progress: ChunkProgressCb = None,
    ) -> FileEntry:
        if self.channel is None or self._write_lock is None:
            raise RuntimeError("Bot not ready yet")

        file_id = uuid.uuid4().hex
        name = os.path.basename(local_path)
        size = os.path.getsize(local_path)
        total = count_chunks(size, self.chunk_size)
        dest = normalize_path(dest_folder)

        chunk_msg_ids: list[int] = []
        if size == 0:
            attachment = discord.File(io.BytesIO(b""), filename=f"{name}.part0000")
            msg = await self.channel.send(
                content=f"`{file_id}` chunk 1/1 (empty) - {name}",
                file=attachment,
            )
            chunk_msg_ids.append(msg.id)
            if on_progress:
                on_progress(1, 1)
        else:
            for idx, data in iter_chunks(local_path, self.chunk_size):
                attachment = discord.File(io.BytesIO(data), filename=f"{name}.part{idx:04d}")
                msg = await self.channel.send(
                    content=f"`{file_id}` chunk {idx + 1}/{total} - {name}",
                    file=attachment,
                )
                chunk_msg_ids.append(msg.id)
                if on_progress:
                    on_progress(idx + 1, total)

        async with self._write_lock:
            entry = FileEntry(
                id=file_id,
                name=name,
                size=size,
                chunks=chunk_msg_ids,
                created=time.time(),
                path=dest,
            )
            self.metadata.files.append(entry)
            self._metadata_msg = await save_metadata(self.channel, self.metadata, self._metadata_msg)
        return entry

    async def upload_folder(
        self,
        local_folder: str,
        dest_folder: str = "",
        on_progress: FolderProgressCb = None,
    ) -> list[FileEntry]:
        base = Path(local_folder)
        if not base.is_dir():
            raise ValueError(f"Not a directory: {local_folder}")

        target_root = join_path(dest_folder, base.name)
        items = sorted(p for p in base.rglob("*") if p.is_file())

        if not items:
            # empty directory - just register the folder so it appears in UI
            await self.create_folder(target_root)
            return []

        results: list[FileEntry] = []
        for i, fp in enumerate(items):
            rel_parent = fp.parent.relative_to(base).as_posix()
            sub = "" if rel_parent == "." else rel_parent
            dest = join_path(target_root, sub)
            if on_progress:
                on_progress(i + 1, len(items), fp.name)
            results.append(await self.upload(str(fp), dest_folder=dest))
        return results

    async def download(
        self,
        file_id: str,
        dest_path: str,
        on_progress: ChunkProgressCb = None,
    ) -> str:
        if self.channel is None:
            raise RuntimeError("Bot not ready yet")
        entry = self.metadata.find(file_id)
        if entry is None:
            raise ValueError(f"File {file_id} not in metadata")

        total = len(entry.chunks)
        with open(dest_path, "wb") as out:
            for i, msg_id in enumerate(entry.chunks):
                msg = await self.channel.fetch_message(msg_id)
                if not msg.attachments:
                    raise RuntimeError(f"Chunk message {msg_id} has no attachment")
                data = await msg.attachments[0].read()
                out.write(data)
                if on_progress:
                    on_progress(i + 1, total)
        return dest_path

    async def delete(self, file_id: str) -> None:
        if self.channel is None or self._write_lock is None:
            raise RuntimeError("Bot not ready yet")
        async with self._write_lock:
            entry = self.metadata.remove(file_id)
            if entry is None:
                return
            for msg_id in entry.chunks:
                try:
                    msg = await self.channel.fetch_message(msg_id)
                    await msg.delete()
                except (discord.NotFound, discord.HTTPException):
                    pass
            self._metadata_msg = await save_metadata(self.channel, self.metadata, self._metadata_msg)

    # ---- folder operations ----------------------------------------

    async def create_folder(self, path: str) -> None:
        if self.channel is None or self._write_lock is None:
            raise RuntimeError("Bot not ready yet")
        path = normalize_path(path)
        if not path:
            return
        async with self._write_lock:
            if path not in self.metadata.folders:
                self.metadata.folders.append(path)
                self._metadata_msg = await save_metadata(
                    self.channel, self.metadata, self._metadata_msg
                )

    async def delete_folder(self, path: str) -> int:
        if self.channel is None or self._write_lock is None:
            raise RuntimeError("Bot not ready yet")
        path = normalize_path(path)
        if not path:
            raise ValueError("Cannot delete root")
        async with self._write_lock:
            prefix = path + "/"
            targets = [
                f for f in list(self.metadata.files)
                if f.path == path or f.path.startswith(prefix)
            ]
            for entry in targets:
                for msg_id in entry.chunks:
                    try:
                        msg = await self.channel.fetch_message(msg_id)
                        await msg.delete()
                    except (discord.NotFound, discord.HTTPException):
                        pass
                self.metadata.files.remove(entry)
            self.metadata.folders = [
                fp for fp in self.metadata.folders
                if fp != path and not fp.startswith(prefix)
            ]
            self._metadata_msg = await save_metadata(
                self.channel, self.metadata, self._metadata_msg
            )
        return len(targets)

    async def refresh(self) -> None:
        if self.channel is None:
            raise RuntimeError("Bot not ready yet")
        self.metadata, self._metadata_msg = await load_metadata(self.channel)
