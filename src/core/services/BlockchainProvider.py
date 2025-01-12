import asyncio
from datetime import datetime, timedelta
from typing import Callable, Awaitable, List, Coroutine

from pydantic import BaseModel
from solana.rpc.async_api import AsyncClient

from config import SolanaNetworkMode
from core.models import Wallet
from core.services.solana import SolanaEventType, SolanaManager, BasicTokenCache
from core.services.solana.CacheProvider import TokenCacheProvider
from core.services.solana.CoinDataProvider import CoinDataProvider
from core.services.solana.handlers import SolanaHeliusTransactionHandler


class BlockchainProvider:
    mode: SolanaNetworkMode
    solana_manager: SolanaManager
    max_rpc_in_sec: int = 10
    _pending_updates: List[Coroutine] = []  # Def must be higher in the hierarchy, maybe some global rate limiter

    def __init__(self, rpc_hostname: str, mode: SolanaNetworkMode):
        self.solana_manager = SolanaManager(rpc_host=rpc_hostname)
        self.mode = mode

    async def connect(self):
        await self.solana_manager.start_listening()
        loop = asyncio.get_event_loop()
        loop.create_task(self.__listen_for_updates(interval=(1 / self.max_rpc_in_sec) * 1.2))

    async def disconnect(self):
        await self.solana_manager.stop_listening()

    async def __listen_for_updates(self, interval: float):
        last_request_time = datetime.now() - timedelta(seconds=interval)
        batch_size = 10

        while True:
            if self._pending_updates:
                for _ in range(min(batch_size, len(self._pending_updates))):
                    elapsed = (datetime.now() - last_request_time).total_seconds()
                    if elapsed < interval:
                        await asyncio.sleep(interval - elapsed)
                    await self._pending_updates.pop(0)
                    last_request_time = datetime.now()

                    # Yield control after processing a batch
                    await asyncio.sleep(0)
            else:
                await asyncio.sleep(0.1)

    async def subscribe_wallets(self, wallets: List[Wallet], processor: Callable[[BaseModel], Awaitable[None]]) -> None:
        for wallet in wallets:
            self._pending_updates.append(
                self.solana_manager.address_subscribe_event(
                    address=wallet.address,
                    event_type=SolanaEventType.TRANSACTION,
                    handler=SolanaSOLTransactionHandler(processor, self.solana_manager.client)
                )
            )

    async def unsubscribe_wallet(self, wallet: Wallet) -> None:
        await self.solana_manager.address_unsubscribe_event(wallet.address)


class HeliusBlockchainProvider(BlockchainProvider):
    _api_url: str
    _api_key: str
    coin_data_providers: list[CoinDataProvider] = []
    client: AsyncClient

    cache: BasicTokenCache | None = None

    def __init__(self, rpc_hostname: str, api_url: str, api_key: str, mode: SolanaNetworkMode,
                 coin_data_providers: list[CoinDataProvider] | None = None, cache: TokenCacheProvider | None = None):
        if coin_data_providers:
            self.coin_data_providers = coin_data_providers
        connection_string = rpc_hostname + '/?api-key=' + api_key if 'helius' in rpc_hostname else rpc_hostname
        super().__init__(connection_string, mode=mode)
        self.client = AsyncClient("https://" + connection_string)
        self._api_url = api_url
        self._api_key = api_key
        self.cache = cache

    async def subscribe_wallets(self, wallets: List[Wallet], processor: Callable[[BaseModel], Awaitable[None]]) -> None:
        for wallet in wallets:
            self._pending_updates.append(
                self.solana_manager.address_subscribe_event(
                    address=wallet.address,
                    event_type=SolanaEventType.TRANSACTION,
                    handler=SolanaHeliusTransactionHandler(processor, self._api_url, self._api_key, self.mode,
                                                           client=self.client,
                                                           coin_data_providers=self.coin_data_providers,
                                                           cache=self.cache)
                )
            )

