from collections.abc import AsyncIterator
from pathlib import Path

import structlog

from app.core.exceptions import NotFoundError

logger = structlog.get_logger("app.storage")


class LocalFilesystemStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _resolve(self, dest_key: str) -> Path:
        path = (self.root / dest_key).resolve()
        root = self.root.resolve()
        if path != root and root not in path.parents:
            raise ValueError("storage path escapes upload directory")
        return path

    async def save(self, chunks: AsyncIterator[bytes], dest_key: str) -> str:
        dest = self._resolve(dest_key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        with dest.open("wb") as handle:
            async for chunk in chunks:
                handle.write(chunk)
        return str(dest)

    async def stream(self, path: str) -> AsyncIterator[bytes]:
        dest = Path(path)
        if not dest.is_file():
            raise NotFoundError("Attachment file is missing")
        with dest.open("rb") as handle:
            while True:
                chunk = handle.read(64 * 1024)
                if not chunk:
                    break
                yield chunk

    async def delete(self, path: str) -> None:
        dest = Path(path)
        try:
            dest.unlink(missing_ok=True)
        except OSError:
            logger.warning("attachment_file_delete_failed", path=path, exc_info=True)
