from aiogram import Dispatcher
from sqlalchemy.ext.asyncio import async_sessionmaker


class CustomDispatcher(Dispatcher):
    sessionmaker: async_sessionmaker
