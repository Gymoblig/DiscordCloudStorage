"""Local file chunking, path helpers, and folder enumeration."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, TYPE_CHECKING

if TYPE_CHECKING:
    from metadata import FileEntry

SAFETY_BYTES = 256 * 1024


def chunk_size_bytes(mb: int) -> int:
    return max(1, mb * 1024 * 1024 - SAFETY_BYTES)


def iter_chunks(path: str, chunk_size: int) -> Iterator[tuple[int, bytes]]:
    with open(path, "rb") as f:
        idx = 0
        while True:
            data = f.read(chunk_size)
            if not data:
                return
            yield idx, data
            idx += 1


def count_chunks(file_size: int, chunk_size: int) -> int:
    if file_size == 0:
        return 1
    return (file_size + chunk_size - 1) // chunk_size


def human_size(num_bytes: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num_bytes)
    for u in units:
        if size < 1024 or u == units[-1]:
            return f"{int(size)} B" if u == "B" else f"{size:.1f} {u}"
        size /= 1024
    return f"{num_bytes} B"


def normalize_path(path: str) -> str:
    """Canonical forward-slash path. '' for root. No leading/trailing slashes."""
    if not path:
        return ""
    p = path.replace("\\", "/")
    parts = [seg for seg in p.split("/") if seg and seg != "."]
    return "/".join(parts)


def join_path(*parts: str) -> str:
    return normalize_path("/".join(p for p in parts if p))


def parent_of(path: str) -> str:
    path = normalize_path(path)
    if "/" not in path:
        return ""
    return path.rsplit("/", 1)[0]


def basename_of(path: str) -> str:
    path = normalize_path(path)
    if "/" not in path:
        return path
    return path.rsplit("/", 1)[1]


CATEGORY_BY_EXT = {
    "audio": {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"},
    "image": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"},
    "pdf":   {".pdf"},
    "word":  {".doc", ".docx", ".odt", ".rtf"},
    "ppt":   {".ppt", ".pptx", ".odp"},
    "zip":   {".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"},
    "code":  {".py", ".js", ".ts", ".java", ".c", ".cpp", ".cs", ".rb", ".go",
              ".rs", ".php", ".html", ".css", ".json", ".xml", ".yaml", ".yml",
              ".sh", ".ps1", ".sql"},
}


def category_for(filename: str) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    for category, exts in CATEGORY_BY_EXT.items():
        if ext in exts:
            return category
    return "default"


@dataclass
class FolderInfo:
    """A folder derived from file paths or explicit folder entries."""
    name: str       # display name (last segment)
    path: str       # full canonical path
    file_count: int
    total_size: int


def folders_at(
    files: list["FileEntry"],
    explicit_folders: list[str],
    current_path: str,
) -> list[FolderInfo]:
    """Immediate sub-folders inside `current_path`, aggregated recursively."""
    current_path = normalize_path(current_path)
    prefix = current_path + "/" if current_path else ""
    found: dict[str, FolderInfo] = {}

    def ensure(full_path: str) -> FolderInfo:
        info = found.get(full_path)
        if info is None:
            info = FolderInfo(name=basename_of(full_path), path=full_path, file_count=0, total_size=0)
            found[full_path] = info
        return info

    for f in files:
        if not f.path:
            continue
        if current_path and not (f.path == current_path or f.path.startswith(prefix)):
            continue
        if not current_path:
            rest = f.path
        else:
            if f.path == current_path:
                continue
            rest = f.path[len(prefix):]
        first = rest.split("/", 1)[0]
        full = join_path(current_path, first)
        info = ensure(full)
        info.file_count += 1
        info.total_size += f.size

    for fp in explicit_folders:
        fp = normalize_path(fp)
        if not fp:
            continue
        if current_path:
            if not fp.startswith(prefix):
                continue
            rest = fp[len(prefix):]
        else:
            rest = fp
        first = rest.split("/", 1)[0]
        full = join_path(current_path, first)
        ensure(full)

    return sorted(found.values(), key=lambda i: i.name.lower())


def files_at(files: list["FileEntry"], current_path: str) -> list["FileEntry"]:
    current_path = normalize_path(current_path)
    return [f for f in files if normalize_path(f.path) == current_path]
