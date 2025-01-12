from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class MenuCallBack(CallbackData, prefix="menu"):
    level: int
    menu_name: str


def get_user_main_btns(*, level: int, sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()
    btns = {
        "✨ Add": "add",
        "👀 Manage": "manage"
    }

    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()


def get_callback_btns(*, level: int, btns: dict[str, str], sizes: tuple[int] = (2,)):
    keyboard = InlineKeyboardBuilder()

    for text, menu_name in btns.items():
        keyboard.add(InlineKeyboardButton(text=text, callback_data=MenuCallBack(level=level + 1, menu_name=menu_name).pack()))

    return keyboard.adjust(*sizes).as_markup()

