"""Business logic for verify_identity skill (TMF720)."""

from src.agents.profiling.models import VerifyIdentityInput, VerifyIdentityOutput
from src.db import get_customer_by_id, get_identity_by_customer


async def verify_identity(data: dict) -> VerifyIdentityOutput:
    """Verify a customer's digital identity.

    Raises ValueError if the customer does not exist.
    """
    validated = VerifyIdentityInput.model_validate(data)
    customer = await get_customer_by_id(validated.customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    identity = await get_identity_by_customer(validated.customer_id)
    if identity is None:
        raise ValueError("Customer not found")

    return VerifyIdentityOutput(
        identity_id=identity["id"],
        verified=bool(identity["verified"]),
        confidence_score=identity["confidence_score"],
        verified_at=identity["verified_at"],
    )
