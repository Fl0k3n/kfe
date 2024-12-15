import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends

from kfe.dependencies import get_directory_repo, get_model_managers
from kfe.persistence.directory_repository import DirectoryRepository
from kfe.utils.constants import Language
from kfe.utils.model_manager import ModelManager, ModelType

router = APIRouter(prefix="/events")

@router.post('/opened-or-refreshed')
async def on_ui_opened_or_refreshed(
    directory_repo: Annotated[DirectoryRepository, Depends(get_directory_repo)],
    model_managers: Annotated[dict[Language, ModelManager], Depends(get_model_managers)]
):
    models_to_eager_load = [ModelType.TEXT_EMBEDDING, ModelType.CLIP, ModelType.LEMMATIZER]

    primary_languages_in_use: set[str] = set()
    for directory in await directory_repo.get_all():
        primary_languages_in_use.add(str(directory.primary_language))

    for language in primary_languages_in_use:
        model_manager = model_managers[language]
        await asyncio.gather(*[model_manager.require_eager(model) for model in models_to_eager_load])
        asyncio.create_task(_release_after_delay(model_manager, models_to_eager_load))

async def _release_after_delay(model_manager: ModelManager, models: list[ModelType]):
    await asyncio.sleep(3600 * 0.25)
    for model in models:
        await model_manager.release_eager(model)
