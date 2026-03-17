"""Business logic for get_nbo skill (TMF701) with Ollama LLM integration."""

import json
import logging
import re
import uuid

import httpx

from src.agents.recommendation.models import (
    GetNboInput,
    GetNboOutput,
    RecommendationItem,
)
from src.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from src.db import get_customer_by_id, get_product_offerings

logger = logging.getLogger(__name__)

NBO_PROMPT_TEMPLATE = """\
You are a telecom product recommendation engine.

Customer profile:
- customer_id: {customer_id}
- category: {customer_category}
- current plan: {product_name}

Available product offerings (excluding current plan):
{offerings_json}

Return ONLY a JSON array of up to 3 offering IDs ranked by suitability for this customer, most suitable first.
Example: ["po_002", "po_003", "po_001"]
Do not include any explanation."""


async def get_nbo(data: dict, ollama_client: httpx.AsyncClient) -> GetNboOutput:
    """Generate next-best-offer recommendations for a customer.

    Uses Ollama LLM when available, falls back to price-sorted offerings.
    Raises ValueError if customer_id does not exist.
    """
    validated = GetNboInput.model_validate(data)
    customer = await get_customer_by_id(validated.customer_id)
    if customer is None:
        raise ValueError("Customer not found")

    all_offerings = await get_product_offerings()

    # TMF637 exclusion: filter out customer's current plan
    eligible_offerings = [
        o for o in all_offerings if o["name"] != customer["product_name"]
    ]

    # Try Ollama LLM path
    ordered_ids = await _call_ollama(customer, eligible_offerings, ollama_client)

    if ordered_ids is not None:
        # Validate returned IDs exist in eligible offerings
        eligible_id_set = {o["id"] for o in eligible_offerings}
        valid_ids = [oid for oid in ordered_ids if oid in eligible_id_set]

        if valid_ids:
            return _build_response(valid_ids, eligible_offerings)
        else:
            logger.warning(
                "Ollama returned all-invalid offering IDs, falling back to price-sorted"
            )

    # Fallback: price-sorted eligible offerings
    logger.warning("Using price-sorted fallback for NBO recommendations")
    sorted_offerings = sorted(eligible_offerings, key=lambda o: o["price"])
    fallback_ids = [o["id"] for o in sorted_offerings[:3]]
    return _build_response(fallback_ids, eligible_offerings)


async def _call_ollama(
    customer: dict,
    eligible_offerings: list[dict],
    client: httpx.AsyncClient,
) -> list[str] | None:
    """Call Ollama to get ranked offering IDs. Returns None on any failure."""
    offerings_json = json.dumps(
        [
            {
                "id": o["id"],
                "name": o["name"],
                "description": o["description"],
                "price": o["price"],
                "price_unit": o["price_unit"],
            }
            for o in eligible_offerings
        ],
        indent=2,
    )

    prompt = NBO_PROMPT_TEMPLATE.format(
        customer_id=customer["id"],
        customer_category=customer["customer_category"],
        product_name=customer["product_name"],
        offerings_json=offerings_json,
    )

    try:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        result = response.json()
        response_text = result.get("response", "")
        return _parse_offering_ids(response_text)
    except Exception as e:
        logger.warning("Ollama call failed: %s", e)
        return None


def _parse_offering_ids(text: str) -> list[str] | None:
    """Parse a JSON array of offering IDs from LLM response text.

    Tries direct JSON parse first, then regex extraction for prose-wrapped responses.
    """
    # Try direct JSON parse
    try:
        parsed = json.loads(text.strip())
        if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    # Regex fallback: extract JSON array from prose
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group())
            if isinstance(parsed, list) and all(isinstance(x, str) for x in parsed):
                return parsed
        except json.JSONDecodeError:
            pass

    logger.warning("Could not parse offering IDs from Ollama response")
    return None


def _build_response(
    ordered_ids: list[str], offerings: list[dict]
) -> GetNboOutput:
    """Build a TMF701 Recommendation response from ordered offering IDs."""
    offerings_by_id = {o["id"]: o for o in offerings}
    items = []
    for priority, oid in enumerate(ordered_ids, start=1):
        offering = offerings_by_id[oid]
        items.append(
            RecommendationItem(
                id=f"ri_{uuid.uuid4().hex[:6]}",
                priority=priority,
                offering_id=offering["id"],
                name=offering["name"],
                description=offering["description"],
                price=offering["price"],
                price_unit=offering["price_unit"],
            )
        )
    return GetNboOutput(
        id=f"rec_{uuid.uuid4().hex[:6]}",
        recommendation_item=items,
    )
