from typing import List

from fastapi import APIRouter

from app.models.game import AiModelInfo
from app.services import model_catalog


router = APIRouter()


@router.get("/", response_model=List[AiModelInfo], summary="List available AI models")
def list_models_endpoint() -> List[AiModelInfo]:
    """Return metadata for all AI models supported by the backend."""

    return [AiModelInfo(**model) for model in model_catalog.list_models()]

