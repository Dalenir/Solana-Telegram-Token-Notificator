from enum import Enum
from typing import List, Dict

from pydantic import BaseModel, Field


class KnownAMMProtocol(Enum):
    RAYDIUM = "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8"
    LIFINITY = '2wT8Yq49kHgDzXuPxZSaeLaH1qbmGXtEyPy64bL7aD3c'
    ORCA = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'
    PUMP_FUN = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P'
    METEORA = 'LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo'


class TransactionType(Enum):
    SWAP = "SWAP"
    TOKEN_MINT = "TOKEN_MINT"
    TRANSFER = "TRANSFER"


class TokenValue(BaseModel):
    usd_value: float
    sol_value: float


class Token(BaseModel):
    address: str
    created_timestamp: int | None = None
    name: str | None = None
    symbol: str | None = None
    supply: int | None = None
    market_cap: float | None = None
    price_usd: float | None = None
    price_sol: float | None = None

    def __eq__(self, other):
        return self.address == other.address


class SolanaTransfer(BaseModel):
    from_: str
    to_: str
    amount: float
    value_sol: float | None = None


class SolanaTokenTransfer(SolanaTransfer):
    token: Token
    total_value_usd: float | None = None
    value_sol: float | None = None


class SolanaTransactionData(BaseModel):
    hash: str

    type_: TransactionType | None = None
    source: str | None = None
    signer: str
    fee: float
    sol_transfers: List[SolanaTransfer]
    token_transfers: List[SolanaTokenTransfer] | None = None
    description: str | None = None


class TokenChange(BaseModel):
    amount: float
    token: Token


class SolanaAccountChangeData(BaseModel):
    native_change: float = 0
    token_changes: list[TokenChange] = Field(default_factory=list)


class NewSolanaTransactionData(BaseModel):
    hash: str
    signer: str
    fee: float

    accounts_changes: Dict[str, SolanaAccountChangeData]


class HeliusSolanaTransactionData(NewSolanaTransactionData):
    type_: TransactionType | None = None
    source: str | None = None
    description: str | None = None
    sol_price_usd: float | None = None


class SolanaEventType(Enum):
    TRANSACTION = 1
    TOKEN_PROGRAM_LOGS = 2
