import asyncio
from typing import Dict, cast, Optional, List

import math
import websockets
from pydantic import BaseModel
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionLogsFilterMentions
from solders.rpc.responses import LogsNotification, SubscriptionResult

from . import SolanaEventHandler
from . import SolanaEventType
from .websockets_rewrited import custom_connect, CustomSolanaWsClientProtocol


class PendingSubscribtion(BaseModel):
    token_programm: bool = False
    address: str


class SolanaManager:
    __instance = None

    _subscribtions = Dict[str, int]
    _handlers: Dict[SolanaEventType, List[SolanaEventHandler]] = {}
    __websocket: Optional[CustomSolanaWsClientProtocol] = None
    client: Optional[AsyncClient] = None
    _rpc_host: str

    token_creator_subscribtion_id: int
    pending_subscribtions: Dict[int, PendingSubscribtion] = {}
    signature_cash = []            # Sometimes websockets send multiple logs for the same event with only 1 subscribtion

    def __new__(cls, rpc_host: str) -> "SolanaManager":
        if cls.__instance is None:
            instance = super(SolanaManager, cls).__new__(cls)
            instance._rpc_host = rpc_host
            instance._subscription_id = None
            instance.__websocket = None
            instance.client = AsyncClient("https://" + rpc_host)
            instance._subscribtions = {}
            instance.pending_subscribtions = {}
            instance.token_creator_subscribtion_id = 0
            cls.__instance = instance
        return cls.__instance

    @property
    def websocket(self) -> CustomSolanaWsClientProtocol:
        if self.__websocket is None:
            raise ValueError("WebSocket is not initialized. Call start_listening() first.")
        return self.__websocket

    async def start_listening(self):
        retry_delay = 1
        while True:
            try:
                print("Attempting to establish WebSocket connection...")
                self.__websocket = cast(
                    CustomSolanaWsClientProtocol,
                    await custom_connect('wss://' + self._rpc_host)
                )
                print("WebSocket connection established.")
                loop = asyncio.get_event_loop()
                loop.create_task(self.async_log_process(self.__websocket))
                loop.create_task(self.__clean_cash())
                break
            except Exception as e:
                print(f"Error establishing WebSocket connection: {e}")
                print(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 60)

    async def stop_listening(self):
        await self.websocket.close()
        self.__websocket = None
        self._subscribtions = {}

    async def async_log_process(self, websocket: CustomSolanaWsClientProtocol):
        while True:
            try:
                msg_list = await websocket.recv()
                for msg in list(msg_list):

                    if isinstance(msg, SubscriptionResult):
                        if isinstance(msg.result, int):
                            pending: PendingSubscribtion = self.pending_subscribtions.pop(msg.id)
                            self._subscribtions[pending.address] = msg.result

                            print(self._subscribtions)
                    elif isinstance(msg, LogsNotification):

                        if str(msg.result.value.signature) in self.signature_cash:
                            continue
                        self.signature_cash.append(str(msg.result.value.signature))

                        handlers = self._handlers.get(SolanaEventType.TRANSACTION)

                        if handlers:
                            for handler in handlers:
                                loop = asyncio.get_event_loop()
                                loop.create_task(handler.handle_event(msg, client=self.client))

            except websockets.ConnectionClosed as e:
                print(f"WebSocket closed: {e}")
                break
            except Exception as e:
                print(f"Error during WebSocket processing: {e}")
                continue

        # Try to reconnect
        print("Attempting to reconnect WebSocket...")
        self.__websocket = None
        await self.start_listening()
        print("Manager is listening for logs")
        for address in self._subscribtions.keys():
            for handler in self._handlers.get(SolanaEventType.TRANSACTION):
                await self.address_subscribe_event(address, SolanaEventType.TRANSACTION, handler)

    async def address_subscribe_event(self,
                                      address: str,
                                      event_type: SolanaEventType,
                                      handler: SolanaEventHandler | None = None):
        _id = await self.websocket.logs_subscribe(
            filter_=RpcTransactionLogsFilterMentions(Pubkey.from_string(address))
        )

        if handler:
            self.add_handler(event_type=event_type, handler=handler)

        self.pending_subscribtions[_id] = PendingSubscribtion(address=address)

        print(f"Event {event_type} for address {address} subscribed. ID {_id}")

    async def address_unsubscribe_event(self, address: str):
        subscribtion: int = self._subscribtions.get(address)
        await self.websocket.logs_unsubscribe(subscription=subscribtion)
        del self._subscribtions[address]
        print(self._subscribtions)

    def add_handler(self, event_type: SolanaEventType, handler: SolanaEventHandler):
        if not self._handlers.get(event_type):
            self._handlers[event_type] = []

        handler_is_new = True
        for old_handler in self._handlers[event_type]:
            if old_handler.id == handler.id:
                handler_is_new = False
                break
        if handler_is_new:
            self._handlers[event_type].append(handler)

    async def __clean_cash(self):
        await asyncio.sleep(60)
        del self.signature_cash[:math.floor(len(self.signature_cash)/3)]
