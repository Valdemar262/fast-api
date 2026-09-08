import logging

from redis.asyncio import Redis

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class Cache:
    def __init__(self, client: Redis) -> None:
        self._client = client

    async def get(self, key: str) -> str | None:
        if not settings.cache_enabled:
            return None
        try:
            value: str | None = await self._client.get(key)
        except Exception:
            logger.warning("Cache read failed for %s", key, exc_info=True)
            return None
        return value

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        if not settings.cache_enabled:
            return
        try:
            await self._client.set(key, value, ex=ttl or settings.cache_ttl_seconds)
        except Exception:
            logger.warning("Cache write failed for %s", key, exc_info=True)

    async def delete(self, *keys: str) -> None:
        if not keys or not settings.cache_enabled:
            return
        try:
            await self._client.delete(*keys)
        except Exception:
            logger.warning("Cache delete failed for %s", keys, exc_info=True)

    async def delete_prefix(self, prefix: str) -> None:
        if not settings.cache_enabled:
            return
        try:
            keys = [key async for key in self._client.scan_iter(match=f"{prefix}*")]
            if keys:
                await self._client.delete(*keys)
        except Exception:
            logger.warning("Cache prefix delete failed for %s", prefix, exc_info=True)


redis_client: Redis = Redis.from_url(settings.redis_url, decode_responses=True)
cache = Cache(redis_client)
