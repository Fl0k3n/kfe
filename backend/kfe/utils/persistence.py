import json
from pathlib import Path

from sqlalchemy import select

from kfe.persistence.db import Database
from kfe.persistence.file_metadata_repository import FileMetadataRepository
from kfe.persistence.model import FileMetadata


async def dump_descriptions(path: Path, file_repo: FileMetadataRepository):
    files = await file_repo.load_all_files()
    res = {str(x.name): str(x.description) for x in files}
    with open(path, 'w') as f:
        json.dump(res, f)

async def restore_descriptions(path: Path, db: Database):
    with open(path, 'r') as f:
        descriptions: dict[str, str] = json.load(f)

    async with db.session() as sess:
        async with sess.begin():
            q = await sess.stream(select(FileMetadata))
            async for row in q.scalars():
                old_description = descriptions.get(str(row.name))
                if old_description is not None:
                    row.description = old_description
