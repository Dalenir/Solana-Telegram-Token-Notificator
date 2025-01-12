import time
from abc import ABC, abstractmethod

from .models import Token


class TokenCacheProvider(ABC):
    """
    Basic cache provider for token data storage.
    Derive from it to make custom ones.
    """

    storage: dict[str, Token]

    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    async def cache_token_data(self, token: Token, expiration_seconds: int | None = None) -> None:
        pass

    @abstractmethod
    async def check_token_existance(self, address: str) -> bool:
        pass

    @abstractmethod
    async def get_cached_token(self, address: str) -> Token | None:
        pass

    async def add_cached_data_to_token(self, token: Token) -> Token:
        cached_token = await self.get_cached_token(token.address)
        if cached_token:
            print(f'TOKEN FOUND {token.address}: \n {cached_token}')
            thing_dict = token.model_dump()
            update_dict = {k: v for k, v in cached_token.model_dump().items() if thing_dict.get(k) is None}
            token = token.model_copy(update=update_dict)
        return token


class BasicTokenCache(TokenCacheProvider):
    """
    Basic cache provider for token data storage.
    Derive from it to make custom ones.
    """

    storage: dict[str, tuple]

    def __init__(self):
        self.storage = dict()

    async def cache_token_data(self, token: Token, expiration_seconds: int | None = None) -> None:
        expiration_time = time.time() + expiration_seconds
        self.storage[token.address] = (token, expiration_time)

    async def check_token_existance(self, address: str) -> bool:
        return address in self.storage

    async def get_cached_token(self, address: str) -> Token | None:
        current_time = time.time()
        token, ex_time = self.storage.get(address, (None, None))
        if current_time < ex_time:
            return token
        else:
            del self.storage[address]
