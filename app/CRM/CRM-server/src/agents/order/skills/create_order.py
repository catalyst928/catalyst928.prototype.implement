"""Business logic for create_order skill (TMF622)."""

from src.agents.order.models import CreateOrderInput, CreateOrderOutput
from src.db import create_order as db_create_order
from src.db import get_customer_by_id, get_product_offering_by_id


async def create_order(data: dict) -> CreateOrderOutput:
    """Create a product order for a customer.

    Raises ValueError if customer or offering does not exist.
    """
    validated = CreateOrderInput.model_validate(data)

    customer = await get_customer_by_id(validated.customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    offering = await get_product_offering_by_id(validated.offer_id)
    if offering is None:
        raise ValueError("ProductOffering not found")

    order = await db_create_order(validated.customer_id, validated.offer_id)
    return CreateOrderOutput(
        order_id=order["order_id"],
        state=order["state"],
        order_date=order["order_date"],
    )
