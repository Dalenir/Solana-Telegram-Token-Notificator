from enum import Enum, IntEnum

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from core.models import TradeSettings


class SettingsCallbackType(IntEnum):
    MIN_TRADE = 1
    MIN_MARKET = 2
    MAX_TRADE = 3
    MAX_MARKET = 4


class SettingsCallbackScope(IntEnum):
    ACCOUNT = 1
    WALLET = 2


class SetSettingsCallback(CallbackData, prefix="set_settings"):
    type: SettingsCallbackType | None = None
    scope: SettingsCallbackScope | None = None


def main_settings_keyboard(current_settings: TradeSettings, scope: SettingsCallbackScope):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text=f"Min trade SOL: {current_settings.min_trade or 0}",
                                     callback_data=SetSettingsCallback(type=SettingsCallbackType.MIN_TRADE,
                                                                       scope=scope).pack()))
    builder.add(InlineKeyboardButton(text=f"Max trade SOL: {current_settings.max_trade or 0}",
                                     callback_data=SetSettingsCallback(type=SettingsCallbackType.MAX_TRADE,
                                                                       scope=scope).pack()))
    builder.add(InlineKeyboardButton(text=f"Min MC: {current_settings.min_cap or 0}",
                                     callback_data=SetSettingsCallback(type=SettingsCallbackType.MIN_MARKET,
                                                                       scope=scope).pack()))
    builder.add(InlineKeyboardButton(text=f"Max MC: {current_settings.max_cap or 0}",
                                     callback_data=SetSettingsCallback(type=SettingsCallbackType.MAX_MARKET,
                                                                       scope=scope).pack()))
    builder.adjust(2, 2)

    return builder.as_markup()
