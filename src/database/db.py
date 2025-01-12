from sqlalchemy import MetaData, AsyncAdaptedQueuePool, pool, NullPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base

Base = declarative_base(
    metadata=MetaData(naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_`%(constraint_name)s`",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
    )
)


def get_sessionmaker(postgres_url: str, pool: bool = True):
    engine = create_async_engine(postgres_url, poolclass=AsyncAdaptedQueuePool if pool else NullPool)
    return async_sessionmaker(
        autoflush=False,
        bind=engine,
        class_=AsyncSession,
    )
