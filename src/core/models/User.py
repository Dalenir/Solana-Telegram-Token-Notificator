from typing import List

from ._core_basemodel import CoreBaseModel
from .TradeSettings import TradeSettings
from .Wallet import Wallet


class UserData(CoreBaseModel):
    settings: TradeSettings | None = None
    telegram_id: str
    username: str
    subscriber: bool


class User(UserData):
    wallets: List[Wallet] | None = None

