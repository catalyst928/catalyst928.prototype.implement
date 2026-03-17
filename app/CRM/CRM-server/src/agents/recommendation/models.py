"""Pydantic models for Recommendation Agent get_nbo skill (TMF701/TMF620/TMF637)."""

from pydantic import BaseModel, Field


class GetNboInput(BaseModel):
    """Input for get_nbo skill."""

    customer_id: str = Field(
        description="TMF701 Recommendation.relatedParty[role=customer].id"
    )


class RecommendationItem(BaseModel):
    """A single recommendation item (TMF701 RecommendationItem)."""

    id: str = Field(description="TMF701 RecommendationItem.id")
    priority: int = Field(
        description="TMF701 RecommendationItem.priority (1 = highest)"
    )
    offering_id: str = Field(
        description="TMF620 ProductOffering.id (RecommendationItem.productOffering.id)"
    )
    name: str = Field(description="TMF620 ProductOffering.name")
    description: str = Field(description="TMF620 ProductOffering.description")
    price: float = Field(
        description="TMF620 ProductOffering.productOfferingPrice[0].price.value"
    )
    price_unit: str = Field(
        description="TMF620 ProductOffering.productOfferingPrice[0].price.unit (e.g. EUR)"
    )


class GetNboOutput(BaseModel):
    """Output for get_nbo skill (TMF701 Recommendation)."""

    id: str = Field(description="TMF701 Recommendation.id")
    recommendation_item: list[RecommendationItem] = Field(
        description="TMF701 Recommendation.recommendationItem[] — ordered by priority ascending"
    )
