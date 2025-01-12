from typing import Any, Union, Optional

from solana.rpc.commitment import Commitment
from solana.rpc.core import _COMMITMENT_TO_SOLDERS
from solana.rpc.websocket_api import SolanaWsClientProtocol
from solders.rpc.config import RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions, RpcTransactionLogsConfig
from solders.rpc.requests import LogsSubscribe
from websockets.legacy.client import connect as ws_connect

"""
Solana py rewriting, ignore IDE warnings
"""


class CustomSolanaWsClientProtocol(SolanaWsClientProtocol):
    async def logs_subscribe(
            self,
            filter_: Union[RpcTransactionLogsFilter, RpcTransactionLogsFilterMentions] = RpcTransactionLogsFilter.All,
            commitment: Optional[Commitment] = None,
    ):
        req_id = self.increment_counter_and_get_id()
        commitment_to_use = None if commitment is None else _COMMITMENT_TO_SOLDERS[commitment]
        config = RpcTransactionLogsConfig(commitment_to_use)
        req = LogsSubscribe(filter_, config, req_id)
        await self.send_data(req)
        return req_id


class custom_connect(ws_connect):

    def __init__(self, uri: str = "ws://localhost:8900", **kwargs: Any) -> None:
        kwargs.setdefault("create_protocol", CustomSolanaWsClientProtocol)
        super().__init__(uri, **kwargs)
