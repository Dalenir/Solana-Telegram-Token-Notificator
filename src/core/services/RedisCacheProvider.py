from redis.asyncio import Redis

from core.services.solana import Token
from core.services.solana.CacheProvider import TokenCacheProvider


class RedisCacheProvider(TokenCacheProvider):
    cache: Redis
    token_key = 'tokens'

    def __init__(self, redis_client: Redis):
        self.cache = redis_client

    def _get_key(self, address: str):
        return f"{self.token_key}: {address}"

    async def cache_token_data(self, token: Token, expiration_seconds: int | None = None):
        await self.cache.set(self._get_key(token.address), token.model_dump_json(), ex=expiration_seconds or 1200)

    async def check_token_existance(self, address: str):
        return await self.cache.exists(self._get_key(address))

    async def get_cached_token(self, address: str) -> Token:
        data: str | None = await self.cache.get(self._get_key(address))
        if data:
            token = Token.model_validate_json(data)
            return token
