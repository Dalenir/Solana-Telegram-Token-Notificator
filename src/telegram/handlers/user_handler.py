# from typing import Set, List
#
# from aiogram import types, Router, F
# from aiogram.filters import CommandStart
# from aiogram.fsm.context import FSMContext
# from aiogram.fsm.state import State, StatesGroup
# from ..utilts.menu_processing import get_menu_content
# from ..keyboards.inline import MenuCallBack, get_callback_btns
# from sqlalchemy.ext.asyncio import async_sessionmaker
#
# from core.models import User, Wallet
# from core.services.WalletsService import WalletsService
#
#
# class WalletStates(StatesGroup):
#     adding_wallets = State()
#     deleting_wallets = State()
#
#
# user_router = Router()
# user_wallets = {}
#
#
# # @user_router.message(CommandStart())
# # async def start_cmd(message: types.Message):
# #     text, reply_markup = await get_menu_content(level=0, menu_name="main")
# #     await message.answer(text, reply_markup=reply_markup)
#
#
# @user_router.callback_query(MenuCallBack.filter(F.menu_name == 'delete_all_wallets'))
# async def delete_all_wallets(callback: types.CallbackQuery, state: FSMContext,
#                              sessionmaker: async_sessionmaker, user: User):
#     await WalletsService(sessionmaker).delete_all_wallets(user_id=user.telegram_id)
#
#     await callback.message.edit_text("🧹 All wallets have been deleted!")
#     await state.clear()
#
#
# @user_router.callback_query(MenuCallBack.filter(F.menu_name == 'manage'))
# async def manage_wallets(callback: types.CallbackQuery, state: FSMContext,
#                          sessionmaker: async_sessionmaker, user: User):
#     text = f"""
# <b>Total SOL wallets: {len(user.wallets)} / 10</b>
#
# ✅ - Wallet is active
# ⏸️ - You paused this wallet
# ⏳ - Wallet was sending too many txs and is paused
# 🛑 - Renew PRO to continue tracking this wallet
#
# <code>-------------------------------------------</code>
# <code>               YOUR WALLETS:               </code>
# <code>-------------------------------------------</code>
# """
#     for i, wallet in enumerate(user.wallets):
#         text += f"{i}: ✅ {wallet.name} {wallet.address}\n"
#
#     reply_markup = get_callback_btns(
#         level=2,
#         btns={
#             "🗑 Delete": "delete_wallets",
#             "🔙 Back": "main",
#         },
#         sizes=(1, 1)
#     )
#
#     await callback.message.edit_text(text, reply_markup=reply_markup)
#
#
# @user_router.callback_query(MenuCallBack.filter())
# async def user_menu(callback: types.CallbackQuery, callback_data: MenuCallBack, state: FSMContext):
#     user_id = callback.from_user.id
#
#     if callback_data.menu_name == "main":
#         text, reply_markup = await get_menu_content(level=0, menu_name="main")
#         await callback.message.edit_text(text, reply_markup=reply_markup)
#         await state.clear()
#
#     if callback_data.menu_name == "add":
#         text, reply_markup = await get_menu_content(level=1, menu_name="add")
#         await callback.message.edit_text(text, reply_markup=reply_markup)
#         await state.set_state(WalletStates.adding_wallets)
#
#     elif callback_data.menu_name == "delete_wallets":
#         text = """
# You can now delete multiple wallets at once. 🚀
#
# Simply send me each wallet address on a new line 🧹For example:
#
# WalletAddress1
# WalletAddress2
# WalletAddress3
#
# Or click DELETE ALL button below to delete all wallets
#         """
#         reply_markup = get_callback_btns(
#             level=3,
#             btns={
#                 "🛑 DELETE ALL": "delete_all_wallets",
#                 "🔙 Back": "manage"
#             },
#             sizes=(1, 1)
#         )
#         await callback.message.edit_text(text, reply_markup=reply_markup)
#         await state.set_state(WalletStates.deleting_wallets)
#
#
# @user_router.message(WalletStates.adding_wallets)
# async def add_wallets(message: types.Message, state: FSMContext, sessionmaker: async_sessionmaker, user: User):
#     wallets = []
#     bad_wallets = []
#     limit = 50 if user.subscriber else 10
#
#     for line in message.text.splitlines():
#
#         if len(user.wallets) >= limit and not user.subscriber:
#             continue
#
#         parts = line.split(" ", maxsplit=1)
#         address = parts[0]
#         nickname = parts[1] if len(parts) > 1 else address
#         wallet = Wallet(name=nickname, address=address)
#
#         if wallet in user.wallets:
#             bad_wallets.append(wallet)
#             continue
#
#         wallets.append(wallet)
#
#     if wallets:
#         await WalletsService(sessionmaker).create_wallets(user_id=user.telegram_id, wallets=wallets)
#         await message.answer("✅ Wallet(s) successfully added! Your current wallets:\n\n" +
#                              '\n'.join([
#                                  f'{i}: <code>{wallet.address}</code> - {wallet.name}' for i, wallet in
#                                  enumerate(wallets)
#                              ]))
#     if bad_wallets:
#         await message.answer("✖️ These wallet(s) were not added:\n\n" +
#                              '\n'.join([f'{wallet.address} - {wallet.name}' for wallet in bad_wallets]) +
#                              '\n\nBecause they are alredy exist or you reached limit of your wallets.' +
#                              f'\n\nYour current limit: {limit} wallets')
#     await state.clear()
#
#
# @user_router.message(WalletStates.deleting_wallets)
# async def delete_wallets(message: types.Message, state: FSMContext, sessionmaker: async_sessionmaker, user: User):
#     need_to_delete: Set[str] = {line for line in message.text.splitlines()}
#     deleted_wallets: List[Wallet] = []
#
#     for wallet in user.wallets:
#         if wallet.address in need_to_delete:
#             deleted_wallets.append(wallet)
#
#     await WalletsService(sessionmaker).delete_wallets(user_id=user.telegram_id, wallets=deleted_wallets)
#
#     if deleted_wallets:
#         deleted_list = "\n".join([wallet.address for wallet in deleted_wallets])
#         await message.answer(f"🧹 The following wallets were successfully deleted:\n{deleted_list}")
#     else:
#         await message.answer("❌ No matching wallets found.")
#
#     await state.clear()

# @user_router.callback_query(lambda c: c.data == "delete_all_wallets")
# async def delete_all_wallets(callback: types.CallbackQuery, state: FSMContext):
#     user_id = callback.from_user.id
#     user_wallets[user_id] = []
#     await callback.message.edit_text("🧹 All wallets have been deleted!")
#     await state.clear()
