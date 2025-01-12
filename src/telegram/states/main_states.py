from aiogram.fsm.state import StatesGroup, State


class WalletsState(StatesGroup):
    add_wallets = State()
    delete_wallets = State()
    manage_wallets = State()
