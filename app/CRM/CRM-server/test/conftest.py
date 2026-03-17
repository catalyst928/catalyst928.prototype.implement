"""Shared test fixtures for CRM-server tests."""

import asyncio
import os

import httpx
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# Use in-memory DB for tests
os.environ["CRM_DB_PATH"] = ":memory:"

from main import app  # noqa: E402
from src.db import close_db, init_db  # noqa: E402


@pytest.fixture(scope="session")
def event_loop():
    """Create a single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Initialize and seed the database before each test, clean up after."""
    await init_db()
    yield
    await close_db()


@pytest.fixture()
def client():
    """Synchronous test client for FastAPI app."""
    # Set a dummy ollama client on app.state for tests
    app.state.ollama_client = httpx.AsyncClient(timeout=30.0)
    with TestClient(app) as c:
        yield c
