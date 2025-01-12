from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import User, TradeSettings
from core.services import UserService
from telegram.keyboards.settings_keys import SetSettingsCallback, SettingsCallbackType, main_settings_keyboard
from telegram.states import SettingsState
from telegram.utilts.texts import texts_en

router = Router()

router.callback_query.filter(StateFilter(SettingsState))
router.message.filter(StateFilter(SettingsState))


@router.callback_query(SetSettingsCallback.filter())
async def set_trade_settings_question(query: CallbackQuery, callback_data: SetSettingsCallback,
                                      state: FSMContext):
    await state.set_data({
        "scope": callback_data.scope,
        "type": callback_data.type
    })

    text = texts_en.get("change_trade_settings")
    await query.message.edit_text(
        text=text, reply_markup=None
    )


@router.message()
async def set_trade_settings_answer(message: Message,
                                    state: FSMContext, user: User, sessionmaker: async_sessionmaker):

    try:
        value = int(message.text)
    except ValueError:
        await message.answer(f"Seems like {message.text} is not number. Try again.")
        return

    state_data = (await state.get_data())
    scope = state_data["scope"]
    _type = state_data["type"]

    new_settings = user.settings
    match _type:
        case SettingsCallbackType.MIN_TRADE:
            new_settings.min_trade = value
        case SettingsCallbackType.MAX_TRADE:
            new_settings.max_trade = value
        case SettingsCallbackType.MIN_MARKET:
            new_settings.min_cap = value
        case SettingsCallbackType.MAX_MARKET:
            new_settings.max_cap = value

    updated_user = await (UserService(sessionmaker)
                          .change_user_settings(telegram_id=str(message.from_user.id), settings=new_settings))

    await message.answer("Account limits updated",
                         reply_markup=main_settings_keyboard(current_settings=updated_user.settings, scope=scope))
