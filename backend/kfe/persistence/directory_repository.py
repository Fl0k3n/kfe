from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from kfe.persistence.model import RegisteredDirectory


class DirectoryRepository:
    def __init__(self, sess: AsyncSession) -> None:
        self.sess = sess

    async def get_all(self) -> list[RegisteredDirectory]:
        res = await self.sess.execute(select(RegisteredDirectory))
        return list(res.scalars().all())

    async def get_by_name(self, name: str) -> Optional[RegisteredDirectory]:
        result = await self.sess.execute(
            select(RegisteredDirectory).where(RegisteredDirectory.name == name)
        )
        return result.scalars().first()

    async def add(self, directory: RegisteredDirectory):
        async with self.sess.begin_nested():
            self.sess.add(directory)

    async def remove(self, directory: RegisteredDirectory):
        async with self.sess.begin_nested():
            await self.sess.delete(directory)
