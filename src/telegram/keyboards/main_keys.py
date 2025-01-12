from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def back_button(callback_data: str):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="🔙 Back", callback_data=callback_data))
    return builder.as_markup()


def manage_wallets_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✨ Add", callback_data="add_wallets"))
    builder.add(InlineKeyboardButton(text="🗑 Delete", callback_data="delete_wallets"))
    builder.row(InlineKeyboardButton(text="🔙 Back", callback_data="back"))
    return builder.as_markup()
