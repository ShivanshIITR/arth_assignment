from pathlib import Path

import pytest

from app.core.exceptions import NotFoundError, ValidationError
from app.core.storage.local_storage import LocalFilesystemStorage
from app.core.storage.validation import detect_content_type, sanitize_filename


def test_sanitize_filename_strips_path_traversal() -> None:
    assert sanitize_filename("../../etc/passwd") == "passwd"
    assert sanitize_filename("C:\\\\Windows\\\\photo.png") == "photo.png"
    with pytest.raises(ValidationError):
        sanitize_filename("..")


def test_magic_bytes_accept_matching_types() -> None:
    assert detect_content_type(b"\x89PNG\r\n\x1a\nrest", "a.png") == "image/png"
    assert detect_content_type(b"\xff\xd8\xff\xe0rest", "a.jpg") == "image/jpeg"
    assert detect_content_type(b"%PDF-1.7 rest", "spec.pdf") == "application/pdf"
    assert detect_content_type(b"PK\x03\x04rest", "doc.docx").endswith("wordprocessingml.document")
    assert detect_content_type(b"hello,world", "data.csv") == "text/csv"


def test_magic_bytes_reject_mismatched_extension() -> None:
    with pytest.raises(ValidationError, match="match"):
        detect_content_type(b"\x89PNG\r\n\x1a\nrest", "not-a-png.jpg")
    with pytest.raises(ValidationError, match="not allowed"):
        detect_content_type(b"MZ\x90\x00", "malware.exe")


@pytest.mark.asyncio
async def test_local_storage_round_trip(tmp_path: Path) -> None:
    storage = LocalFilesystemStorage(tmp_path)

    async def chunks():
        yield b"hello "
        yield b"world"

    path = await storage.save(chunks(), "task-1/file.txt")
    collected = b""
    async for piece in storage.stream(path):
        collected += piece
    assert collected == b"hello world"
    await storage.delete(path)
    with pytest.raises(NotFoundError):
        async for _ in storage.stream(path):
            pass
