from __future__ import annotations

import re
from pathlib import PurePosixPath

from app.core.exceptions import ValidationError

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")

PNG = b"\x89PNG\r\n\x1a\n"
JPEG = b"\xff\xd8\xff"
GIF87 = b"GIF87a"
GIF89 = b"GIF89a"
PDF = b"%PDF"
ZIP = b"PK\x03\x04"
RIFF = b"RIFF"
WEBP = b"WEBP"

EXTENSION_CONTENT_TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".txt": "text/plain",
    ".csv": "text/csv",
}


def sanitize_filename(filename: str) -> str:
    raw = filename.replace("\\", "/")
    name = PurePosixPath(raw).name
    if not name or name in {".", ".."}:
        raise ValidationError("Invalid filename")
    cleaned = _SAFE_NAME.sub("_", name).strip("._")
    if not cleaned:
        raise ValidationError("Invalid filename")
    return cleaned[:200]


def detect_content_type(header: bytes, filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower()
    expected = EXTENSION_CONTENT_TYPES.get(suffix)
    if expected is None:
        raise ValidationError("File type not allowed")

    if suffix == ".png" and header.startswith(PNG):
        return expected
    if suffix in {".jpg", ".jpeg"} and header.startswith(JPEG):
        return expected
    if suffix == ".gif" and (header.startswith(GIF87) or header.startswith(GIF89)):
        return expected
    if suffix == ".webp" and header.startswith(RIFF) and WEBP in header[:16]:
        return expected
    if suffix == ".pdf" and header.startswith(PDF):
        return expected
    if suffix in {".docx", ".xlsx"} and header.startswith(ZIP):
        return expected
    if suffix in {".txt", ".csv"}:
        if b"\x00" in header:
            raise ValidationError("File type not allowed")
        return expected
    raise ValidationError("File type does not match its contents")
