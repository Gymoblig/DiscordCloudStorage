"""Metadata persistence - stored as a pinned message attachment."""
from __future__ import annotations

import io
import json
from dataclasses import asdict, dataclass, field
from typing import Optional

import discord

METADATA_FILENAME = "cloudstorage_metadata.json"
METADATA_MARKER = "[CloudStorage metadata - do not delete]"


@dataclass
class FileEntry:
    id: str
    name: str
    size: int
    chunks: list[int]
    created: float
    path: str = ""  # parent folder path; "" means root


@dataclass
class Metadata:
    version: int = 2
    files: list[FileEntry] = field(default_factory=list)
    folders: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(
            {
                "version": self.version,
                "files": [asdict(f) for f in self.files],
                "folders": self.folders,
            },
            indent=2,
        )

    @classmethod
    def from_json(cls, raw: str) -> "Metadata":
        data = json.loads(raw)
        return cls(
            version=data.get("version", 1),
            files=[FileEntry(**f) for f in data.get("files", [])],
            folders=list(data.get("folders", [])),
        )

    def find(self, file_id: str) -> Optional[FileEntry]:
        for f in self.files:
            if f.id == file_id:
                return f
        return None

    def remove(self, file_id: str) -> Optional[FileEntry]:
        for i, f in enumerate(self.files):
            if f.id == file_id:
                return self.files.pop(i)
        return None


async def load_metadata(channel: discord.TextChannel) -> tuple[Metadata, Optional[discord.Message]]:
    pins = await channel.pins()
    for msg in pins:
        if msg.content.startswith(METADATA_MARKER) and msg.attachments:
            for att in msg.attachments:
                if att.filename == METADATA_FILENAME:
                    raw = (await att.read()).decode("utf-8")
                    return Metadata.from_json(raw), msg
    return Metadata(), None


async def save_metadata(
    channel: discord.TextChannel,
    metadata: Metadata,
    old_msg: Optional[discord.Message],
) -> discord.Message:
    raw = metadata.to_json().encode("utf-8")
    file = discord.File(io.BytesIO(raw), filename=METADATA_FILENAME)
    msg = await channel.send(content=METADATA_MARKER, file=file)
    await msg.pin()
    if old_msg is not None:
        try:
            await old_msg.delete()
        except discord.HTTPException:
            pass
    return msg
