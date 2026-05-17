from fastapi import APIRouter, Depends

from app.api.deps import get_config_service
from app.models.schemas import PromptConfigOut, PromptConfigUpdate
from app.services.config_service import ConfigService

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/prompt", response_model=PromptConfigOut)
async def get_prompt_config(config: ConfigService = Depends(get_config_service)):
    return config.get_prompt_config()


@router.put("/prompt", response_model=PromptConfigOut)
async def update_prompt_config(
    body: PromptConfigUpdate,
    config: ConfigService = Depends(get_config_service),
):
    return config.update_prompt_config(body)
