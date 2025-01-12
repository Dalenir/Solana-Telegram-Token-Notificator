import asyncio

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from sqlalchemy.ext.asyncio import async_sessionmaker
from redis import asyncio as aioredis
from config import settings, Settings
from core.services.BlockchainProvider import HeliusBlockchainProvider
from core.services.RedisCacheProvider import RedisCacheProvider
from core.services.WalletsService import WalletsService
from core.services.solana import BasicTokenCache
from core.services.solana.CoinDataProvider import CoinGeckoProvider, DexScreenerProvider, BirdeyeProvider
from database.db import get_sessionmaker
from telegram.custom_dispatcher import CustomDispatcher
from telegram.handlers import start_hand, main_hand, admin_hand, settings_hand
from telegram.middlewares.user_middleware import BotUserMiddleware
from telegram.notifications import TransactionNotificator

bot = Bot(token=settings.BOT_TOKEN,
          default=DefaultBotProperties(parse_mode="HTML"))

dp = CustomDispatcher()

dp.include_router(start_hand.router)
dp.include_router(settings_hand.router)
dp.include_router(main_hand.router)
dp.include_router(admin_hand.router)

dp.message.outer_middleware(BotUserMiddleware())
dp.callback_query.outer_middleware(BotUserMiddleware())


async def on_startup(dispatcher):
    o_settings: Settings = dispatcher["settings"]

    # Forming HeliusBlockchainProvider for main logs handling
    coin_data_providers = []

    redis_client = aioredis.from_url(o_settings.redis_url)
    cache = RedisCacheProvider(redis_client)

    if o_settings.BIRDEYE_API_KEY:
        birdeye_provider = BirdeyeProvider(api_key=o_settings.BIRDEYE_API_KEY)
        await birdeye_provider.start_watching_fresh_tokens(cache)
        coin_data_providers.append(birdeye_provider)
    # if o_settings.COINGECKO_API_KEY:
    #     coin_data_providers.append(CoinGeckoProvider(api_key=o_settings.COINGECKO_API_KEY))
    coin_data_providers.append(DexScreenerProvider())

    blockchain_provider = HeliusBlockchainProvider(rpc_hostname=o_settings.RPC_HOST,
                                                   api_url=o_settings.HELIUS_API_URL,
                                                   api_key=o_settings.HELIUS_API_KEY,
                                                   mode=o_settings.MODE,
                                                   coin_data_providers=coin_data_providers,
                                                   cache=cache)
    await blockchain_provider.connect()

    # await blockchain_provider.listen_token_creator_programm(
    #     handler=SolanaTokenProgramHandler(test4)
    # )

    dispatcher['blockchain_provider'] = blockchain_provider

    # Resubscribe all wallets
    sessionmaker: async_sessionmaker = dispatcher["sessionmaker"]

    notificator = TransactionNotificator(bot=bot, sessionmaker=sessionmaker, mode=o_settings.MODE)
    dispatcher["notificator"] = notificator

    wallets_service = WalletsService(sessionmaker=sessionmaker)
    all_wallets = await wallets_service.get_wallets()
    await blockchain_provider.subscribe_wallets(wallets=[wallet for wallet in all_wallets],
                                                processor=notificator.notify_wallet_owners)

    print("🟢 BOT STARTED!")


async def on_shutdown(dispatcher):
    blockchain_provider: HeliusBlockchainProvider = dispatcher['blockchain_provider']
    await blockchain_provider.disconnect()

    print("🔴 BOT IS DOWN!")


async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp['sessionmaker'] = get_sessionmaker(postgres_url=settings.postgres_url)
    dp['settings'] = settings

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


asyncio.run(main())
