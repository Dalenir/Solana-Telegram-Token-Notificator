from typing import Optional

from . import TradeSettings
from ._core_basemodel import CoreBaseModel


class Wallet(CoreBaseModel):
    id: int | None = None
    user_id: Optional[str] = None
    address: str
    name: str

    settings: TradeSettings | None = None

    def __eq__(self, other):
        return self.address == other.address and self.name == other.name
