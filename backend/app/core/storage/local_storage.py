import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

import structlog

from app.core.exceptions import NotFoundError

logger = structlog.get_logger("app.storage")

_CHUNK = 64 * 1024


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
        await asyncio.to_thread(dest.parent.mkdir, parents=True, exist_ok=True)
        handle = await asyncio.to_thread(dest.open, "wb")
        try:
            async for chunk in chunks:
                await asyncio.to_thread(handle.write, chunk)
        finally:
            await asyncio.to_thread(handle.close)
        return str(dest)

    async def stream(self, path: str) -> AsyncIterator[bytes]:
        dest = Path(path)
        if not await asyncio.to_thread(dest.is_file):
            raise NotFoundError("Attachment file is missing")
        handle = await asyncio.to_thread(dest.open, "rb")
        try:
            while True:
                chunk = await asyncio.to_thread(handle.read, _CHUNK)
                if not chunk:
                    break
                yield chunk
        finally:
            await asyncio.to_thread(handle.close)

    async def delete(self, path: str) -> None:
        dest = Path(path)
        try:
            await asyncio.to_thread(dest.unlink, missing_ok=True)
        except OSError:
            logger.warning("attachment_file_delete_failed", path=path, exc_info=True)
