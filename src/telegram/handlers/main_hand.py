from typing import List, Set

from aiogram import Router, F
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import User, Wallet
from core.services.BlockchainProvider import HeliusBlockchainProvider
from core.services.WalletsService import WalletsService

from telegram.keyboards import back_button, main_settings_keyboard
from telegram.keyboards.main_keys import manage_wallets_keyboard
from telegram.keyboards.settings_keys import SettingsCallbackScope
from telegram.notifications import TransactionNotificator
from telegram.utilts.text_utilts import wallet_list_text
from telegram.utilts.texts import texts_en
from telegram.states import WalletsState, SettingsState

router = Router()


@router.callback_query(F.data == 'add_wallets')
async def add_wallets(query: CallbackQuery, state: FSMContext):
    text = texts_en.get("add_wallets")
    await query.message.edit_text(text=text,
                                  reply_markup=back_button(callback_data=await state.get_value("from")))
    await state.set_state(WalletsState.add_wallets)


@router.callback_query(F.data == 'delete_wallets')
async def delete_wallets(query: CallbackQuery, state: FSMContext, user: User):
    await state.set_state(WalletsState.delete_wallets)
    delete_text = texts_en.get("delete_wallets")
    await query.message.answer(text=delete_text, reply_markup=back_button(callback_data=await state.get_value("from")))
    await query.message.edit_text(text=query.message.html_text, reply_markup=None)


@router.callback_query(F.data == 'back',
                       or_f(StateFilter(WalletsState.delete_wallets), StateFilter(WalletsState.add_wallets)))
@router.callback_query(F.data == 'manage_wallets')
async def manage_wallets(query: CallbackQuery, state: FSMContext, user: User):
    await state.set_state(WalletsState.manage_wallets)
    await state.set_data({"from": 'manage_wallets'})
    text = texts_en.get("manage_wallets").format(
        USER_WALLETS=len(user.wallets),
        LIMIT=50 if user.subscriber else 10,
        WALLETS_LIST=wallet_list_text(user.wallets)
    )
    await query.message.answer(text=text, reply_markup=manage_wallets_keyboard())
    await query.message.edit_text(text=query.message.html_text, reply_markup=None)


@router.message(WalletsState.add_wallets)
async def add_wallets_message(message: Message,
                              sessionmaker: async_sessionmaker, user: User,
                              blockchain_provider: HeliusBlockchainProvider,
                              notificator: TransactionNotificator):
    wallets = []
    bad_wallets = []
    limit = 50 if user.subscriber else 10

    for line in message.text.splitlines():

        if len(user.wallets) >= limit and not user.subscriber:
            continue

        parts = line.split(" ", maxsplit=1)
        address = parts[0]
        nickname = parts[1] if len(parts) > 1 else address
        wallet = Wallet(name=nickname, address=address)

        if wallet in user.wallets:
            bad_wallets.append(wallet)
            continue

        wallets.append(wallet)

    if wallets:
        new_wallets = await WalletsService(sessionmaker).create_wallets(user_id=user.telegram_id, wallets=wallets)

        await blockchain_provider.subscribe_wallets(wallets=[wallet for wallet in new_wallets],
                                                    processor=notificator.notify_wallet_owners)

        wallets.extend(user.wallets)
        await message.answer(texts_en.get("add_wallets_message_succ") + wallet_list_text(wallets[::-1]))
    if bad_wallets:
        await message.answer(
            text=texts_en.get("add_wallets_message_fail")
            .format(
                BAD_WALLETS_LIST='\n'.join([f'{wallet.address} - {wallet.name}' for wallet in bad_wallets]),
                USER_LIMIT=limit
            ))


@router.message(WalletsState.delete_wallets)
async def delete_wallets_message(message: Message,
                                 sessionmaker: async_sessionmaker,
                                 blockchain_provider: HeliusBlockchainProvider,
                                 user: User):
    need_to_delete: Set[str] = {line for line in message.text.splitlines()}
    deleted_wallets: List[Wallet] = []

    for wallet in user.wallets:
        if wallet.address in need_to_delete:
            deleted_wallets.append(wallet)

    await WalletsService(sessionmaker).delete_wallets(user_id=user.telegram_id, wallets=deleted_wallets)
    for wallet in deleted_wallets:
        await blockchain_provider.unsubscribe_wallet(wallet)

    if deleted_wallets:
        deleted_list = "\n".join([wallet.address for wallet in deleted_wallets])
        await message.answer(f"🧹 The following wallets were successfully deleted:\n{deleted_list}")
    else:
        await message.answer("❌ No matching wallets found.")


@router.callback_query(F.data == 'account_settings')
async def account_settings(query: CallbackQuery, state: FSMContext, user: User):
    await state.set_state(SettingsState.main)
    text = texts_en.get("account_settings")
    await query.message.edit_text(text=text,
                                  reply_markup=main_settings_keyboard(
                                      current_settings=user.settings, scope=SettingsCallbackScope.ACCOUNT
                                  ))
