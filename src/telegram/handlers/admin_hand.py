from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import User
from core.services import UserService
from telegram.filters.admin_search_filter import SearchExistingUserFilter
from telegram.keyboards.admin_keys import admin_manage_user_keyboard
from telegram.states import AdminState

router = Router()

router.message.filter(StateFilter(AdminState))
router.callback_query.filter(StateFilter(AdminState))


@router.message(F.text == "Settings")
async def admin_settings(message: Message, state: FSMContext):
    await state.set_state(AdminState.settings)
    await message.answer("Settings")


@router.message(SearchExistingUserFilter())
async def admin_manage_user(message: Message, state: FSMContext, target_user: User):
    await state.set_state(AdminState.manage_user)
    await state.set_data({"target_user_id": target_user.telegram_id})
    await message.answer(f"Manage user {target_user.username} here",
                         reply_markup=admin_manage_user_keyboard(target_user))


@router.callback_query(SearchExistingUserFilter(), F.data == "give_prem")
async def give_premium(query: CallbackQuery, target_user: User, sessionmaker: async_sessionmaker):
    updtd_user = await (UserService(sessionmaker)
                        .change_user_premium_status(target_user.telegram_id, target_prem_status=True))
    await query.message.edit_text(f"Success! {target_user.username} now is a premium user.",
                                  reply_markup=admin_manage_user_keyboard(updtd_user))


@router.callback_query(SearchExistingUserFilter(), F.data == "stop_prem")
async def give_premium(query: CallbackQuery, target_user: User, sessionmaker: async_sessionmaker):
    updtd_user = await (UserService(sessionmaker)
                        .change_user_premium_status(target_user.telegram_id, target_prem_status=False))
    await query.message.edit_text(f"Success! {target_user.username} now is not a premium user.",
                                  reply_markup=admin_manage_user_keyboard(updtd_user))


@router.message()
async def no_users(message: Message):
    await message.answer(f"User {message.text} is not found")
