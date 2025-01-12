from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import User, TradeSettings
from database import SettingsModel
from database.models import UserModel


class UserService:
    sessionmaker: async_sessionmaker

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def get_user(self,
                       user_id: str | None = None,
                       user_phone: str | None = None,
                       user_username: str | None = None) -> User | None:
        async with self.sessionmaker() as session:
            if user_id:
                user_model = await session.get(UserModel, user_id)
                if user_model:
                    return User.model_validate(user_model)

            conditions = []
            if user_username:
                conditions.append(UserModel.username == user_username)
            if user_phone:
                conditions.append(UserModel.phone == user_phone)
            if conditions:
                query = select(UserModel).where(or_(*conditions))
                return (await session.execute(query)).scalars().first()
            return None

    async def create_user(self, telegram_id: str, username: str, phone: str | None = None) -> User:
        async with self.sessionmaker() as session:
            settings = SettingsModel(
                min_trade=0,
                max_trade=0,
                min_cap=0,
                max_cap=0
            )
            session.add(settings)
            await session.flush()

            user = UserModel(telegram_id=telegram_id, username=username, phone=phone, settings_id=settings.id)
            session.add(user)
            await session.flush()

            await session.refresh(user)
            user_data = User.model_validate(user)
            await session.commit()

            return user_data

    async def change_user_premium_status(self, telegram_id: str, target_prem_status: bool) -> User:
        async with self.sessionmaker() as session:
            user_model = await session.get(UserModel, telegram_id)
            if user_model:
                user_model.subscriber = target_prem_status
                await session.flush()
                user = User.model_validate(user_model)
                await session.commit()
                return user
            else:
                raise ValueError(f"Admin trying to make premium unexisting user! {telegram_id}")

    async def change_user_settings(self, telegram_id: str | int, settings: TradeSettings) -> User:
        async with self.sessionmaker() as session:
            user_model = await session.get(UserModel, telegram_id)

            if settings.min_trade:
                user_model.settings.min_trade = settings.min_trade
            if settings.max_trade:
                user_model.settings.max_trade = settings.max_trade
            if settings.min_cap:
                user_model.settings.min_cap = settings.min_cap
            if settings.max_cap:
                user_model.settings.max_cap = settings.max_cap

            await session.flush()
            user = User.model_validate(user_model)
            await session.commit()

            return user
