"""Pydantic models for AI Management Agent get_ai_model_status skill (TMF915)."""

from pydantic import BaseModel, Field


class GetAiModelStatusInput(BaseModel):
    """Input for get_ai_model_status skill."""

    model_id: str = Field(
        description="TMF915 AIModel.id — identifier of the AI model to query"
    )


class GetAiModelStatusOutput(BaseModel):
    """Output for get_ai_model_status skill."""

    model_id: str = Field(description="TMF915 AIModel.id")
    model_name: str = Field(description="TMF915 AIModel.name")
    version: str = Field(description="TMF915 AIModel.version")
    status: str = Field(
        description="TMF915 AIModel.lifecycleStatus (active | inactive | training)"
    )
    accuracy_score: float = Field(
        description="TMF915 AIModel.characteristic[name=accuracy].value (0.0–1.0)"
    )
    last_updated: str = Field(
        description="TMF915 AIModel.lastUpdate (ISO 8601)"
    )
