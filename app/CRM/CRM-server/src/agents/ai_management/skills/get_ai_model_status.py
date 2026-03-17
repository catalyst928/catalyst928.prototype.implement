"""Business logic for get_ai_model_status skill (TMF915)."""

from src.agents.ai_management.models import (
    GetAiModelStatusInput,
    GetAiModelStatusOutput,
)
from src.db import get_ai_model_by_id


async def get_ai_model_status(data: dict) -> GetAiModelStatusOutput:
    """Look up AI model status by ID.

    Raises ValueError if the model does not exist.
    """
    validated = GetAiModelStatusInput.model_validate(data)
    model = await get_ai_model_by_id(validated.model_id)
    if model is None:
        raise ValueError("AIModel not found")
    return GetAiModelStatusOutput(
        model_id=model["id"],
        model_name=model["model_name"],
        version=model["version"],
        status=model["status"],
        accuracy_score=model["accuracy_score"],
        last_updated=model["last_updated"],
    )
