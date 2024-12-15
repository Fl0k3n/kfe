from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from kfe.persistence.model import Base


class Database:
    DB_FILE_NAME = '.kfe.db'

    def __init__(self, directory: Path, log_sql=True) -> None:
        self.engine = create_async_engine(
            url=f"sqlite+aiosqlite:///{directory.absolute()}/{self.DB_FILE_NAME}",
            echo=log_sql
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
