import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_model_manager
from utils.model_manager import ModelManager, ModelType

router = APIRouter(prefix="/events")

@router.post('/opened-or-refreshed')
async def on_ui_opened_or_refreshed(model_manager: Annotated[ModelManager, Depends(get_model_manager)]):
    await asyncio.gather(*[
        model_manager.require_eager(model)
        for model in (ModelType.TEXT_EMBEDDING, ModelType.IMAGE_EMBEDDING, ModelType.CLIP)
    ])
