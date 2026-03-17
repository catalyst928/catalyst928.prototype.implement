"""Business logic for query_customer skill (TMF629)."""

from src.agents.profiling.models import QueryCustomerInput, QueryCustomerOutput
from src.db import get_customer_by_phone


async def query_customer(data: dict) -> QueryCustomerOutput:
    """Look up a customer by phone number.

    Raises ValueError if no customer is found.
    """
    validated = QueryCustomerInput.model_validate(data)
    customer = await get_customer_by_phone(validated.phone)
    if customer is None:
        raise ValueError("Customer not found")
    return QueryCustomerOutput(
        customer_id=customer["id"],
        name=customer["name"],
        customer_category=customer["customer_category"],
        product_name=customer["product_name"],
    )
