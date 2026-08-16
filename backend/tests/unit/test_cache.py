from unittest.mock import AsyncMock

import pytest

from app.core.cache import delete_key, get_or_set


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}
        self.fail = False

    async def get(self, key: str) -> str | None:
        if self.fail:
            raise ConnectionError("redis down")
        return self.store.get(key)

    async def setex(self, key: str, ttl: int, value: str) -> None:
        if self.fail:
            raise ConnectionError("redis down")
        self.store[key] = value

    async def delete(self, key: str) -> None:
        if self.fail:
            raise ConnectionError("redis down")
        self.store.pop(key, None)


@pytest.mark.asyncio
async def test_get_or_set_miss_loads_and_stores() -> None:
    redis = FakeRedis()
    loader = AsyncMock(return_value={"n": 1})

    result = await get_or_set(
        "dashboard:u1",
        60,
        loader,
        redis,  # type: ignore[arg-type]
        dumps=lambda v: str(v["n"]),
        loads=lambda raw: {"n": int(raw)},
    )
    assert result == {"n": 1}
    loader.assert_awaited_once()
    assert redis.store["dashboard:u1"] == "1"


@pytest.mark.asyncio
async def test_get_or_set_hit_skips_loader() -> None:
    redis = FakeRedis()
    redis.store["dashboard:u1"] = "7"
    loader = AsyncMock(return_value={"n": 99})

    result = await get_or_set(
        "dashboard:u1",
        60,
        loader,
        redis,  # type: ignore[arg-type]
        dumps=lambda v: str(v["n"]),
        loads=lambda raw: {"n": int(raw)},
    )
    assert result == {"n": 7}
    loader.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_or_set_falls_back_when_redis_raises() -> None:
    redis = FakeRedis()
    redis.fail = True
    loader = AsyncMock(return_value={"n": 3})

    result = await get_or_set(
        "dashboard:u1",
        60,
        loader,
        redis,  # type: ignore[arg-type]
        dumps=lambda v: str(v["n"]),
        loads=lambda raw: {"n": int(raw)},
    )
    assert result == {"n": 3}
    loader.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_or_set_corrupt_cache_is_treated_as_miss() -> None:
    redis = FakeRedis()
    redis.store["dashboard:u1"] = "not-an-int"
    loader = AsyncMock(return_value={"n": 4})

    result = await get_or_set(
        "dashboard:u1",
        60,
        loader,
        redis,  # type: ignore[arg-type]
        dumps=lambda v: str(v["n"]),
        loads=lambda raw: {"n": int(raw)},
    )
    assert result == {"n": 4}
    loader.assert_awaited_once()
    assert redis.store["dashboard:u1"] == "4"


@pytest.mark.asyncio
async def test_get_or_set_without_redis_uses_loader() -> None:
    loader = AsyncMock(return_value={"n": 5})
    result = await get_or_set(
        "dashboard:u1",
        60,
        loader,
        None,
        dumps=lambda v: str(v["n"]),
        loads=lambda raw: {"n": int(raw)},
    )
    assert result == {"n": 5}
    loader.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_key_swallows_redis_errors() -> None:
    redis = FakeRedis()
    redis.fail = True
    await delete_key("dashboard:u1", redis)  # type: ignore[arg-type]
