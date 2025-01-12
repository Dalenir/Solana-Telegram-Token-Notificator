import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue
from functools import cache
from random import random, randint
from typing import Callable, Awaitable, Dict

from aiogram.client.session import aiohttp
from pydantic import BaseModel
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.responses import Notification, LogsNotification

from config import SolanaNetworkMode
from . import SolanaEventType, Token
from .CoinDataProvider import CoinDataProvider
from .models import KnownAMMProtocol, SolanaAccountChangeData, TokenChange, HeliusSolanaTransactionData
from .CacheProvider import TokenCacheProvider


class SolanaEventHandler(ABC):
    id: str
    type: SolanaEventType
    _processor: Callable[[BaseModel], Awaitable[None]]

    def __init__(self, processor: Callable[[BaseModel], Awaitable[None]], _id: str):
        self._processor = processor
        self.id = _id

    @abstractmethod
    async def handle_event(self, event: Notification, client: AsyncClient | None = None) -> None:
        ...


class SolanaHeliusTransactionHandler(SolanaEventHandler):
    type = SolanaEventType.TRANSACTION
    _helius_url: str
    _helius_api_key: str
    client: AsyncClient
    mode: SolanaNetworkMode
    token_cache: TokenCacheProvider | None = None
    __coin_data_providers: list[CoinDataProvider]

    def __init__(self, processor: Callable[[BaseModel], Awaitable[None]],
                 helius_url: str, helius_key: str, mode: SolanaNetworkMode,
                 client: AsyncClient,
                 coin_data_providers: list[CoinDataProvider],
                 cache: TokenCacheProvider | None = None,
                 _id: str = "Helius"):
        super().__init__(processor, _id)
        self._helius_url = helius_url
        self._helius_url = helius_url
        self._helius_api_key = helius_key
        self.client = client
        self.mode = mode
        self.__coin_data_providers = coin_data_providers
        self.token_cache = cache

        self.transaction_queue: Queue[str] = asyncio.Queue()

        # Start a background task to process transactions every second
        self.event_loop = asyncio.get_event_loop()
        self.event_loop.create_task(self.process_transactions_periodically())

    async def process_transactions_periodically(self):
        while True:
            try:
                await asyncio.sleep(1)
                transactions = []
                while not self.transaction_queue.empty():
                    transactions.append(await self.transaction_queue.get())

                if transactions:
                    asyncio.create_task(
                        self.handle_multiple_transactions(transactions_hashes=transactions, client=self.client)
                    )
            except Exception as e:
                print(f"Error during transaction processing: {e}")

    async def handle_event(self, event: LogsNotification, client: AsyncClient | None = None):
        await self.transaction_queue.put(str(event.result.value.signature))

    async def handle_multiple_transactions(self,
                                           transactions_hashes: list[str],
                                           client: AsyncClient | None = None
                                           ):
        data = await self._get_transaction(transactions_hashes)

        if not isinstance(data, list):
            raise Exception(f"Problem with helius api: wrong connection or breaking limits.")
        if not len(data):
            return

        if data:
            for transaction in data:
                asyncio.create_task(self.__handle_single_transaction(transaction, client=client))

    async def _get_transaction(self, transaction_hashes: list[str]):
        async with aiohttp.ClientSession() as session:
            async with session.post(self._helius_url + '/v0/transactions',
                                    params={"api-key": self._helius_api_key},
                                    headers={"Content-Type": "application/json"},
                                    json={"transactions": transaction_hashes}) as response:
                data = await response.json()
                return data

    @staticmethod
    async def fetch_sol_price():
        async with aiohttp.ClientSession() as session:
            async with session.get(
                    f"https://api.coingecko.com/api/v3/simple/price?ids=solana&vs_currencies=usd"
            ) as response:
                data = await response.json()
                return data.get("solana", {}).get("usd", 0)

    async def __handle_single_transaction(self, transaction_data: dict, client: AsyncClient):

        if transaction_data.get('transactionError') is not None:
            return

        print("Transaction", transaction_data.get('signature'))
        sender = transaction_data.get('feePayer')
        token_transfers = []
        sol_transfers = []
        accounts_changes: Dict[str, SolanaAccountChangeData] = {}
        source = None
        transaction_type = None
        fee = transaction_data.get('fee', 0) / 1e9

        # Type
        type_data = transaction_data.get('type')
        if type_data:
            try:
                transaction_type = SolanaEventType(type_data)
            except ValueError:
                pass

        # Source
        source_data = transaction_data.get('source')
        if source_data in ["UNKNOWN", "SYSTEM_PROGRAM"]:
            for account_data in transaction_data.get("accountData"):
                source_str = account_data.get('protocol')
                if not source_str:
                    source_str = account_data.get('account')
                try:
                    source = KnownAMMProtocol(source_str).name
                except ValueError:
                    continue
                else:
                    break
        else:
            source = source_data

        # SOL Price
        # CACHE NEEDED
        sol_token = await self.token_cache.get_cached_token('So11111111111111111111111111111111111111112')
        if not sol_token:
            sol_price = await self.fetch_sol_price()
            sol_token = Token(
                address='So11111111111111111111111111111111111111112',
                price_usd=sol_price,
            )
            await self.token_cache.cache_token_data(sol_token, expiration_seconds=180)
        else:
            sol_price = sol_token.price_usd

        # Account changes
        for change_data in transaction_data.get("accountData", []):
            native_change = change_data.get("nativeBalanceChange", 0)
            token_balance_changes = change_data.get("tokenBalanceChanges", [])

            # We are not interested in empty changes
            if not native_change and not token_balance_changes:
                continue

            account = change_data.get("account")
            solana_account_change_data = SolanaAccountChangeData()
            solana_account_change_data.native_change = native_change

            # Funny token processing

            tokens_in_transaction: dict[str, Token] = dict()

            for token_change in change_data.get("tokenBalanceChanges", []):

                # We are not supporting token accounts for now
                user_account = token_change.get("userAccount")
                if user_account != account:
                    account = user_account

                token = Token(address=token_change.get("mint"))

                # try:
                #     token_signatures = await self.client.get_signatures_for_address(Pubkey.from_string(token.address))
                #     token.created_timestamp = token_signatures.value[0].block_time
                # except Exception as e:
                #     print(e)

                amount = (float(token_change["rawTokenAmount"]["tokenAmount"]) /
                          (10 ** token_change["rawTokenAmount"]["decimals"]))

                # Check if token already in the known tokens for this transaction
                if tokens_in_transaction.get(token.address):
                    token = tokens_in_transaction[token.address]
                else:

                    if self.mode == SolanaNetworkMode.MAIN:
                        if token.address != "So11111111111111111111111111111111111111112":

                            # Check cache for basic data of fresh tokens; Note that market data is still fetching later
                            if self.token_cache:
                                token = await self.token_cache.add_cached_data_to_token(token)

                            # Fetching market data from all providers
                            # Right now the only -useful- one is BirdEye, so it is plain cycle
                            # But if more providers are used, here must be fun async.gather with shared state
                            for coin_data_provider in self.__coin_data_providers:
                                token: Token = await coin_data_provider.add_marketdata_to_token(token)
                                if token.symbol and token.price_usd and token.market_cap:
                                    break
                        else:
                            token = Token(name='Wrapped SOL', address=token.address, symbol="wSOL", price_usd=sol_price)

                    # If token still don't have name, we will try to get this data from token metadata extension:
                    if not token.name:
                        token_info_data = await client.get_account_info_json_parsed(Pubkey.from_string(token.address))
                        token_info_data = token_info_data.value.data.parsed
                        extension_data_list: list = token_info_data['info'].get('extensions')
                        if extension_data_list:
                            metadata = [
                                data['state'] for data in extension_data_list if data['extension'] == "tokenMetadata"
                            ]
                            if metadata:
                                token_info = metadata[0]
                                token_name = token_info.get('name')
                                token_symbol = token_info.get('symbol')
                                token.name = token_name if token_name else token_symbol

                    tokens_in_transaction[token.address] = token

                solana_account_change_data.token_changes.append(TokenChange(
                    amount=amount,
                    token=token
                ))

            if not accounts_changes.get(account):
                accounts_changes[account] = solana_account_change_data
            else:
                accounts_changes[account].token_changes.extend(solana_account_change_data.token_changes)

        if accounts_changes:
            await self._processor(
                HeliusSolanaTransactionData(
                    hash=str(transaction_data['signature']),
                    fee=fee,
                    signer=sender,
                    accounts_changes=accounts_changes,
                    type_=transaction_type,
                    source=source,
                    description=transaction_data.get('description'),
                    sol_price_usd=sol_price
                )
            )
