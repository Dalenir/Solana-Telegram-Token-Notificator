import asyncio
import time
from abc import ABC
from collections.abc import Awaitable
from datetime import datetime
from typing import Callable

import aiohttp
from aiohttp import ContentTypeError

from .models import Token
from .CacheProvider import BasicTokenCache, TokenCacheProvider


class CoinDataProvider(ABC):
    url: str
    api_key: str | None

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    async def add_marketdata_to_token(self, token: Token) -> Token:
        pass


class CoinGeckoProvider(CoinDataProvider):
    url = "https://api.coingecko.com/api/v3"

    async def add_marketdata_to_token(self, token: Token) -> Token:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"{self.url}/coins/solana/contract/{token.address}?x_cg_demo_api_key={self.api_key}"
            ) as response:
                try:
                    data = await response.json()
                except ContentTypeError:
                    print('Coingecko returned not json for token', token.address, await response.read())
                else:
                    token.symbol = data.get('symbol', token.symbol)
                    token.name = data.get("name", token.name)
                    token.price_usd = float(data.get("market_data", {}).get("current_price", {})
                                            .get("usd", 0)) or token.price_usd
                    token.market_cap = data.get("market_data", {}).get("market_cap", {}).get("usd", token.market_cap)
        return token


class DexScreenerProvider(CoinDataProvider):
    url = "https://api.dexscreener.com"

    async def add_marketdata_to_token(self, token: Token) -> Token:
        async with aiohttp.ClientSession() as session:
            headers = {
                "Cache-Control": "no-cache",
                "Pragma": "no-cache",
            }
            async with session.get(f"{self.url}/latest/dex/tokens/{token.address}", headers=headers) as response:
                data = await response.json()
                pairs = data.get("pairs")
                if pairs:
                    token_data = pairs[0]
                    token.name = token_data.get("baseToken", {}).get("name", token.name)
                    token.symbol = token_data.get("baseToken", {}).get("symbol", token.symbol)
                    token.price_usd = float(token_data.get("priceUsd", 0)) or token.price_usd
                    token.market_cap = token_data.get("marketCap", token.market_cap)
                    if not token.created_timestamp:
                        token.created_timestamp = token_data.get("pairCreatedAt")
                    if 'pump' in token.address:
                        print("PUMPFUN DEX RETURNED:", token_data.get("marketCap"))
                else:
                    print(data)
                    if token.created_timestamp:
                        print('Created', datetime.now().timestamp() - token.created_timestamp)
        return token


class BirdeyeProvider(CoinDataProvider):
    url = 'https://public-api.birdeye.so/defi'

    token: Token

    async def add_marketdata_to_token(self, token: Token) -> Token:
        self.token = token

        urls = {
            f"{self.url}/token_overview?address={token.address}": self._add_metadata,
            f"{self.url}/v3/token/market-data?address={token.address}": self._add_market_data,
            f"{self.url}/token_creation_info?address={token.address}": self._add_creation_data
        }

        async with aiohttp.ClientSession() as session:
            tasks = []
            for url, processor in urls.items():
                tasks.append(self.fetch_and_process(url, session, processor))
            await asyncio.gather(*tasks)
            return token

    async def _add_metadata(self, data: dict):
        self.token.name = data.get("name", self.token.name)
        self.token.symbol = data.get("symbol", self.token.symbol)

    async def _add_market_data(self, data: dict):
        self.token.market_cap = data.get("marketcap", self.token.market_cap)
        print(data)
        self.token.price_usd = data.get("price", self.token.price_usd)
        print(self.token.price_usd)

    async def _add_creation_data(self, data: dict):
        self.token.created_timestamp = data.get('blockUnixTime')

    async def fetch_and_process(self,
                                url,
                                session,
                                processor: Callable[[dict], Awaitable[None]] | None = None):
        headers = {
            "x-chain": "solana",
            'X-API-KEY': self.api_key,
            'accept': 'application/json'
        }
        async with session.get(url, headers=headers) as response:
            data = (await response.json()).get("data", {})
            if data is None:
                return
            if processor:
                return await processor(data)
            else:
                return data

    async def start_watching_fresh_tokens(self, cache: TokenCacheProvider):

        async def new_tokens_hunt():
            url = f'{self.url}/v2/tokens/new_listing?limit=10&meme_platform_enabled=true'
            async with aiohttp.ClientSession() as session:
                new_tokens: list[dict] = (await self.fetch_and_process(session=session, url=url)).get("items")
                for token_data in new_tokens:
                    token_address = token_data.get('address')
                    if not await cache.get_cached_token(token_address):
                        token_name = token_data.get('name')
                        token_symbol = token_data.get("symbol")
                        if (token_name is None) or (token_symbol is None):
                            print(f"WRONG FRESH TOKEN FORMING {token_data}")
                        time_of_creation = token_data.get("liquidityAddedAt")
                        if time_of_creation:
                            timestamp = int(datetime.fromisoformat(time_of_creation).timestamp())
                        else:
                            timestamp = None
                        token = Token(address=token_address, symbol=token_symbol,
                                      name=token_name, created_timestamp=timestamp)
                        await cache.cache_token_data(token)

        async def loop():
            while True:
                asyncio.create_task(new_tokens_hunt())
                await asyncio.sleep(0.5)

        asyncio.create_task(loop())
