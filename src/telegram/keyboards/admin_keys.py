from aiogram.filters.callback_data import CallbackData
from aiogram.types import KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

from core.models import User


def admin_start_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Settings"))
    return builder.as_markup(resize_keyboard=True)


class ManageUserCallback(CallbackData, prefix="mu"):
    user_id: int
    prem_nxt: bool


def admin_manage_user_keyboard(user: User):
    builder = InlineKeyboardBuilder()

    if not user.subscriber:
        builder.row(InlineKeyboardButton(text="⭐️ Give premium", callback_data="give_prem"))
    else:
        builder.row(InlineKeyboardButton(text="😐 Stop premium", callback_data="stop_prem"))
    return builder.as_markup()
