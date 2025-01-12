from aiogram.filters import Filter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import User
from core.services import UserService
from telegram.states import AdminState


class SearchExistingUserFilter(Filter):

    async def __call__(self,
                       message: Message,
                       sessionmaker: async_sessionmaker,
                       state: FSMContext) -> dict[str, User] | bool:

        user_search_data = (await state.get_data()).get('target_user_id')
        if not user_search_data:
            user_search_data = message.text

        target_user = await UserService(sessionmaker).get_user(
            user_id=str(user_search_data), user_phone=user_search_data, user_username=user_search_data
        )

        if target_user is None:
            return False
        else:
            return {"target_user": target_user}
