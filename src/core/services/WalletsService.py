from typing import List

from sqlalchemy import select, Tuple
from sqlalchemy.ext.asyncio import async_sessionmaker

from core.models import Wallet, User, UserData
from database.models import UserModel, WalletModel


class WalletsService:
    sessionmaker: async_sessionmaker

    def __init__(self, sessionmaker: async_sessionmaker):
        self.sessionmaker = sessionmaker

    async def create_wallets(self, user_id: str, wallets: List[Wallet]):
        async with self.sessionmaker() as session:
            user_model = await session.get(UserModel, user_id)
            for wallet in wallets:
                user_model.wallets.append(WalletModel(
                    name=wallet.name,
                    address=wallet.address,
                ))
            session.add(user_model)
            await session.flush()
            new_wallets = [Wallet.model_validate(wallet) for wallet in user_model.wallets]
            await session.commit()
            return new_wallets

    async def delete_wallets(self, user_id: str, wallets: List[Wallet]):
        async with self.sessionmaker() as session:
            user_model = await session.get(UserModel, user_id)
            if not user_model:
                raise ValueError("User not found")

            wallet_addresses_to_delete = {wallet.address for wallet in wallets}

            wallets_to_delete = [w for w in user_model.wallets if w.address in wallet_addresses_to_delete]

            for wallet in wallets_to_delete:
                await session.delete(wallet)

            await session.commit()

    async def delete_all_wallets(self, user_id: str):
        async with self.sessionmaker() as session:
            user_model = await session.get(UserModel, user_id)
            if not user_model:
                raise ValueError("User not found")

            user_model.wallets.clear()
            await session.commit()

    async def get_wallets(self, addresses: List[str] | None = None) -> List[Wallet]:
        async with self.sessionmaker() as session:
            query = select(WalletModel)
            if addresses:
                query = query.where(WalletModel.address.in_(addresses))
            all_wallets = (await session.execute(query)).scalars()
            return [Wallet.model_validate(wallet) for wallet in all_wallets]

    async def get_wallets_with_users(self, addresses: List[str] | None = None) -> list[tuple[Wallet, UserData]]:

        """
        Experimental
        In theory, can cause funny circular errors.
        But more effective for particular important usecase without much overcomplication with models
        """

        async with self.sessionmaker() as session:
            query = select(WalletModel)
            if addresses:
                query = query.where(WalletModel.address.in_(addresses))
            all_wallets = (await session.execute(query)).scalars()

            return [(Wallet.model_validate(wallet), UserData.model_validate(wallet.user)) for wallet in all_wallets]
