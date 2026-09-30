from __future__ import annotations

import logging
from typing import Any

from aiogram.fsm.storage.base import BaseStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.storage.redis import RedisStorage

logger = logging.getLogger(__name__)


class StorageBundle:
    def __init__(self, redis_url: str | None) -> None:
        self.redis_url = redis_url
        self.storage: BaseStorage
        self.redis = None
        if redis_url:
            try:
                import redis.asyncio as redis_asyncio
                self.redis = redis_asyncio.from_url(redis_url, decode_responses=True)
                self.storage = RedisStorage(redis=self.redis)
            except Exception as exc:
                logger.exception("Redis initialization failed; falling back to MemoryStorage: %s", exc)
                self.storage = MemoryStorage()
        else:
            logger.warning("REDIS_URL is not set; using MemoryStorage")
            self.storage = MemoryStorage()

    async def ping(self) -> bool:
        if self.redis is None:
            return False
        try:
            return bool(await self.redis.ping())
        except Exception:
            return False

    async def close(self) -> None:
        if self.redis is not None:
            await self.redis.aclose()
