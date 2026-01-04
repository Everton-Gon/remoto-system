"""
RemotDesk Server - Database Connection
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from .models import Base
from ..core.config import get_settings

settings = get_settings()

# Engine async
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# Session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Inicializa o banco de dados criando as tabelas"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    """Dependency para obter sessão do banco"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
