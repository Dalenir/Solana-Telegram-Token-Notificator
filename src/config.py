from enum import Enum
from typing import Annotated

from pydantic import computed_field, Field
from pydantic_settings import BaseSettings


class SolanaNetworkMode(Enum):
    MAIN = "MAIN"
    DEV = "DEV"


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMIN_ID: int

    DB_HOST: str
    DB_PORT: int
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str

    MODE: SolanaNetworkMode

    HELIUS_API_KEY: str | None = None
    COINGECKO_API_KEY: str | None = None
    BIRDEYE_API_KEY: str | None = None

    REDIS_HOST: str
    REDIS_PORT: Annotated[str, Field(alias="REDIS_INNER_PORT")]

    @computed_field
    @property
    def HELIUS_API_URL(self) -> str:
        return "https://api.helius.xyz" if self.MODE == SolanaNetworkMode.MAIN else "https://api-devnet.helius-rpc.com"

    @computed_field
    @property
    def postgres_url(self) -> str:
        return f"postgresql+asyncpg://" \
               f"{self.DB_USERNAME}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}" \
               f"?async_fallback=True"

    @computed_field
    @property
    def RPC_HOST(self) -> str:
        return "mainnet.helius-rpc.com" if self.MODE == SolanaNetworkMode.MAIN else "devnet.helius-rpc.com"

    @computed_field
    @property
    def redis_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"


settings = Settings()
