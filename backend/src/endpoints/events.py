import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_model_manager
from utils.model_manager import ModelManager, ModelType

router = APIRouter(prefix="/events")

@router.post('/opened-or-refreshed')
async def on_ui_opened_or_refreshed(model_manager: Annotated[ModelManager, Depends(get_model_manager)]):
    models_to_eager_load = [ModelType.TEXT_EMBEDDING, ModelType.IMAGE_EMBEDDING, ModelType.CLIP]
    await asyncio.gather(*[model_manager.require_eager(model) for model in models_to_eager_load])
    async def release_after_delay():
        await asyncio.sleep(3600 * 0.25)
        for model in models_to_eager_load:
            await model_manager.release_eager(model)
    asyncio.create_task(release_after_delay())
