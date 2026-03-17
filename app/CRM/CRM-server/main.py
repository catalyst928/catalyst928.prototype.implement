"""CRM-server — Customer relationship management with A2A agents.

FastAPI application on port 8002 hosting four A2A agents:
- Profiling Agent (/profiling) — query_customer, verify_identity
- Recommendation Agent (/recommendation) — get_nbo
- Order Agent (/order) — create_order
- AI Management Agent (/ai-management) — get_ai_model_status
"""

import logging
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from src.agents.ai_management.agent import (
    AI_MANAGEMENT_AGENT_CARD,
    AIManagementAgentExecutor,
)
from src.agents.order.agent import ORDER_AGENT_CARD, OrderAgentExecutor
from src.agents.profiling.agent import PROFILING_AGENT_CARD, ProfilingAgentExecutor
from src.agents.recommendation.agent import (
    RECOMMENDATION_AGENT_CARD,
    RecommendationAgentExecutor,
)
from src.config import CRM_SERVER_PORT, OLLAMA_BASE_URL, OLLAMA_MODEL
from src.db import close_db, init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize DB and shared httpx client on startup, clean up on shutdown."""
    logger.info("CRM-server starting on port %s", CRM_SERVER_PORT)
    logger.info("OLLAMA_BASE_URL=%s", OLLAMA_BASE_URL)
    logger.info("OLLAMA_MODEL=%s", OLLAMA_MODEL)

    await init_db()
    logger.info("Database initialized and seeded")

    async with httpx.AsyncClient(timeout=30.0) as client:
        app.state.ollama_client = client
        yield

    await close_db()
    logger.info("CRM-server shut down")


app = FastAPI(
    title="CRM-server",
    description="Customer relationship management — A2A agents for profiling, recommendation, order, and AI management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow all origins for local GUI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Profiling Agent ---
profiling_executor = ProfilingAgentExecutor()
profiling_handler = DefaultRequestHandler(
    agent_executor=profiling_executor,
    task_store=InMemoryTaskStore(),
)
profiling_app = A2AStarletteApplication(
    agent_card=PROFILING_AGENT_CARD,
    http_handler=profiling_handler,
)
app.mount("/profiling", profiling_app.build())


# --- Recommendation Agent ---
# NOTE: The executor needs the ollama_client, but app.state isn't available
# at module import time. We use a lazy wrapper that resolves at first request.
class _LazyRecommendationExecutor:
    """Wrapper that creates the real executor on first use with the shared httpx client."""

    def __init__(self):
        self._executor = None

    def _get_executor(self):
        if self._executor is None:
            self._executor = RecommendationAgentExecutor(app.state.ollama_client)
        return self._executor

    async def execute(self, context, event_queue):
        return await self._get_executor().execute(context, event_queue)

    async def cancel(self, context, event_queue):
        return await self._get_executor().cancel(context, event_queue)


recommendation_handler = DefaultRequestHandler(
    agent_executor=_LazyRecommendationExecutor(),
    task_store=InMemoryTaskStore(),
)
recommendation_app = A2AStarletteApplication(
    agent_card=RECOMMENDATION_AGENT_CARD,
    http_handler=recommendation_handler,
)
app.mount("/recommendation", recommendation_app.build())


# --- Order Agent ---
order_executor = OrderAgentExecutor()
order_handler = DefaultRequestHandler(
    agent_executor=order_executor,
    task_store=InMemoryTaskStore(),
)
order_app = A2AStarletteApplication(
    agent_card=ORDER_AGENT_CARD,
    http_handler=order_handler,
)
app.mount("/order", order_app.build())


# --- AI Management Agent ---
ai_management_executor = AIManagementAgentExecutor()
ai_management_handler = DefaultRequestHandler(
    agent_executor=ai_management_executor,
    task_store=InMemoryTaskStore(),
)
ai_management_app = A2AStarletteApplication(
    agent_card=AI_MANAGEMENT_AGENT_CARD,
    http_handler=ai_management_handler,
)
app.mount("/ai-management", ai_management_app.build())


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "crm-server"}
