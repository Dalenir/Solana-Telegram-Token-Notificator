from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from core.models import User
from core.services.UserService import UserService


class BotUserMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_service = UserService(sessionmaker=data['sessionmaker'])
        telegram_id = str(event.from_user.id)
        user: User = await user_service.get_user(telegram_id)
        if not user:
            username = event.from_user.username
            if not username:
                # User have at least first name
                username = event.from_user.first_name + " " + (event.from_user.last_name or "")
            user = await user_service.create_user(telegram_id=telegram_id, username=username)

        data['user'] = user
        return await handler(event, data)
