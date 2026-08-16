from collections.abc import AsyncIterator
from typing import Protocol


class StorageBackend(Protocol):
    async def save(self, chunks: AsyncIterator[bytes], dest_key: str) -> str: ...

    def stream(self, path: str) -> AsyncIterator[bytes]: ...

    async def delete(self, path: str) -> None: ...
