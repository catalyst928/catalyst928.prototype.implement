"""Pydantic models for Order Agent create_order skill (TMF622)."""

from pydantic import BaseModel, Field


class CreateOrderInput(BaseModel):
    """Input for create_order skill."""

    customer_id: str = Field(
        description="TMF622 ProductOrder.relatedParty[role=customer].id"
    )
    offer_id: str = Field(
        description="TMF622 ProductOrder.productOrderItem[0].productOffering.id"
    )


class CreateOrderOutput(BaseModel):
    """Output for create_order skill."""

    order_id: str = Field(description="TMF622 ProductOrder.id")
    state: str = Field(
        description="TMF622 ProductOrder.state (acknowledged | inProgress | completed)"
    )
    order_date: str = Field(
        description="TMF622 ProductOrder.orderDate (ISO 8601)"
    )
