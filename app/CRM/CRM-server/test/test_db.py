"""Tests for database initialization and seed data."""

import pytest
import pytest_asyncio

from src.db import (
    get_ai_model_by_id,
    get_customer_by_id,
    get_customer_by_phone,
    get_db,
    get_identity_by_customer,
    get_product_offerings,
)


class TestInitDb:
    @pytest.mark.asyncio
    async def test_tables_created(self):
        db = get_db()
        async with db.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            rows = await cursor.fetchall()
            table_names = [row[0] for row in rows]
        assert "customers" in table_names
        assert "product_offerings" in table_names
        assert "orders" in table_names
        assert "identities" in table_names
        assert "ai_models" in table_names


class TestSeedData:
    @pytest.mark.asyncio
    async def test_customers_seeded(self):
        cust_a = await get_customer_by_phone("13800000001")
        assert cust_a is not None
        assert cust_a["id"] == "cust_001"
        assert cust_a["customer_category"] == "gold"

        cust_b = await get_customer_by_phone("13800000002")
        assert cust_b is not None
        assert cust_b["customer_category"] == "silver"

        cust_c = await get_customer_by_phone("13800000003")
        assert cust_c is not None
        assert cust_c["customer_category"] == "bronze"

    @pytest.mark.asyncio
    async def test_product_offerings_seeded(self):
        offerings = await get_product_offerings()
        assert len(offerings) >= 3
        offering_ids = [o["id"] for o in offerings]
        assert "po_001" in offering_ids

    @pytest.mark.asyncio
    async def test_identities_seeded(self):
        for cust_id in ["cust_001", "cust_002", "cust_003"]:
            identity = await get_identity_by_customer(cust_id)
            assert identity is not None, f"Identity missing for {cust_id}"

    @pytest.mark.asyncio
    async def test_ai_model_seeded(self):
        model = await get_ai_model_by_id("qwen2.5_7b")
        assert model is not None
        assert model["model_name"] == "qwen2.5:7b"
        assert model["status"] == "active"
