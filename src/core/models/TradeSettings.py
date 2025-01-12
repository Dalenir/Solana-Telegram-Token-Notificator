from ._core_basemodel import CoreBaseModel


class TradeSettings(CoreBaseModel):
    min_trade: int | None = None
    max_trade: int | None = None

    min_cap: float | None = None
    max_cap: float | None = None
