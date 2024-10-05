from typing import Annotated

from fastapi import APIRouter, Depends

from dependencies import get_model_manager
from utils.model_manager import ModelManager, ModelType

router = APIRouter(prefix="/events")

@router.post('/opened-or-refreshed')
def on_ui_opened_or_refreshed(model_manager: Annotated[ModelManager, Depends(get_model_manager)]):
    model_manager.require_eager(ModelType.TEXT_EMBEDDING)
    model_manager.require_eager(ModelType.IMAGE_EMBEDDING)

