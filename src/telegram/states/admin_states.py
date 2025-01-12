from aiogram.fsm.state import StatesGroup, State


class AdminState(StatesGroup):
    main = State()
    settings = State()
    manage_user = State()
