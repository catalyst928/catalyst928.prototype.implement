"""SQLite database layer — DDL, connection management, and query functions."""

import uuid
from datetime import datetime, timezone
from typing import Optional

import aiosqlite

from src.config import DB_PATH

_db: Optional[aiosqlite.Connection] = None


async def init_db() -> None:
    """Create tables and seed demo data. Called from FastAPI lifespan."""
    global _db
    _db = await aiosqlite.connect(DB_PATH)
    _db.row_factory = aiosqlite.Row

    await _db.executescript("""
        CREATE TABLE IF NOT EXISTS customers (
            id TEXT PRIMARY KEY,
            phone TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            customer_category TEXT NOT NULL,
            product_name TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS product_offerings (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            price_unit TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS orders (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            offering_id TEXT NOT NULL,
            state TEXT NOT NULL,
            order_date TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (offering_id) REFERENCES product_offerings(id)
        );

        CREATE TABLE IF NOT EXISTS identities (
            id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            verified INTEGER NOT NULL,
            confidence_score REAL NOT NULL,
            verified_at TEXT NOT NULL,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        );

        CREATE TABLE IF NOT EXISTS ai_models (
            id TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            version TEXT NOT NULL,
            status TEXT NOT NULL,
            accuracy_score REAL NOT NULL,
            last_updated TEXT NOT NULL
        );
    """)
    await _db.commit()

    from src.seed import seed_data
    await seed_data(_db)


async def close_db() -> None:
    """Close the database connection. Called from FastAPI lifespan."""
    global _db
    if _db:
        await _db.close()
        _db = None


def get_db() -> aiosqlite.Connection:
    """Return the active database connection."""
    assert _db is not None, "Database not initialized. Call init_db() first."
    return _db


# --- Query functions ---


async def get_customer_by_phone(phone: str) -> Optional[dict]:
    """Look up a customer by phone number."""
    db = get_db()
    async with db.execute(
        "SELECT id, phone, name, customer_category, product_name FROM customers WHERE phone = ?",
        (phone,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def get_customer_by_id(customer_id: str) -> Optional[dict]:
    """Look up a customer by ID."""
    db = get_db()
    async with db.execute(
        "SELECT id, phone, name, customer_category, product_name FROM customers WHERE id = ?",
        (customer_id,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def get_product_offerings() -> list[dict]:
    """Return all product offerings."""
    db = get_db()
    async with db.execute(
        "SELECT id, name, description, price, price_unit FROM product_offerings"
    ) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_product_offering_by_id(offering_id: str) -> Optional[dict]:
    """Look up a product offering by ID."""
    db = get_db()
    async with db.execute(
        "SELECT id, name, description, price, price_unit FROM product_offerings WHERE id = ?",
        (offering_id,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def create_order(customer_id: str, offering_id: str) -> dict:
    """Create a new product order. Returns the order record."""
    db = get_db()
    order_id = f"ord_{uuid.uuid4().hex[:8]}"
    order_date = datetime.now(timezone.utc).isoformat()
    state = "acknowledged"
    await db.execute(
        "INSERT INTO orders (id, customer_id, offering_id, state, order_date) VALUES (?, ?, ?, ?, ?)",
        (order_id, customer_id, offering_id, state, order_date),
    )
    await db.commit()
    return {"order_id": order_id, "state": state, "order_date": order_date}


async def get_identity_by_customer(customer_id: str) -> Optional[dict]:
    """Look up the identity verification record for a customer."""
    db = get_db()
    async with db.execute(
        "SELECT id, customer_id, verified, confidence_score, verified_at FROM identities WHERE customer_id = ?",
        (customer_id,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)


async def get_ai_model_by_id(model_id: str) -> Optional[dict]:
    """Look up an AI model by ID."""
    db = get_db()
    async with db.execute(
        "SELECT id, model_name, version, status, accuracy_score, last_updated FROM ai_models WHERE id = ?",
        (model_id,),
    ) as cursor:
        row = await cursor.fetchone()
        if row is None:
            return None
        return dict(row)
