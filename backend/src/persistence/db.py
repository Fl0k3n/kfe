from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from persistence.model import Base


class Database:
    def __init__(self, directory: Path) -> None:
        # TODO 3 slashes?
        SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{str(directory.absolute())}/skonrad.db"
        self.engine = create_async_engine(
            SQLALCHEMY_DATABASE_URL,
            echo=True
        )

    async def init_db(self): 
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.session_maker = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine,
            class_=AsyncSession
        )

    async def close_db(self):
        await self.engine.dispose()

    def session(self) -> AsyncSession:
        return self.session_maker()
