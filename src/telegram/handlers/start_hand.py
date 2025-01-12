from aiogram import Router, Bot, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, BotCommand, CallbackQuery

from config import settings
from telegram.keyboards import main_menu_keyboard
from telegram.keyboards.admin_keys import admin_start_keyboard
from telegram.states import WalletsState, AdminState
from telegram.utilts.texts import texts_en

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext, bot: Bot):
    await bot.set_my_commands([BotCommand(command='/start', description="Main menu")])
    await bot.set_chat_menu_button(chat_id=message.chat.id)
    if message.from_user.id == settings.ADMIN_ID:
        await bot.set_my_commands([BotCommand(command='/admin', description="Main menu")])
    await main_menu(message, state, bot)


@router.callback_query(F.data == "main_menu")
@router.callback_query(WalletsState.manage_wallets, F.data == 'back')
async def main_menu(event: Message | CallbackQuery, state: FSMContext, bot: Bot):
    await state.clear()
    await state.set_data({"from": 'main_menu'})

    # Here we can delete old main message or remove keyboard
    text = texts_en.get("main_menu")
    await bot.send_message(event.from_user.id, text=text, reply_markup=main_menu_keyboard())

    if isinstance(event, CallbackQuery):
        await event.answer()
        await event.message.delete()


@router.message(Command('admin'), F.from_user.id == settings.ADMIN_ID)
async def admin_start(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(AdminState.main)
    text = texts_en.get("admin_start")
    await message.answer(text, reply_markup=admin_start_keyboard())
