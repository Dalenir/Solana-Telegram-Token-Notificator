from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="✨ Add", callback_data="add_wallets"))
    builder.add(InlineKeyboardButton(text="👀 Manage", callback_data="manage_wallets"))
    # builder.row(InlineKeyboardButton(text="⚙️ Account Settings", callback_data="account_settings"))
    return builder.as_markup()
