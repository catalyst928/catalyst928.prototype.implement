"""CC-server — Call Center orchestrator, WebRTC signaling relay, A2A flow coordinator.

FastAPI application on port 8001.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from src.communication.agent import (
    COMMUNICATION_AGENT_CARD,
    CommunicationAgentExecutor,
)
from src.orchestration.flow import run_business_flow
from src.orchestration.order import router as order_router
from src.ws.signaling import router as signaling_router, set_orchestration_flow

app = FastAPI(
    title="CC-server",
    description="Call Center orchestrator — WebRTC signaling relay and A2A flow coordinator",
    version="0.1.0",
)

# CORS — allow all origins for local GUI access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register WebSocket signaling endpoint
app.include_router(signaling_router)

# Register REST order endpoint
app.include_router(order_router)

# Wire up orchestration flow to signaling
set_orchestration_flow(run_business_flow)

# --- Communication Agent (a2a-python SDK) ---
communication_executor = CommunicationAgentExecutor()
communication_task_store = InMemoryTaskStore()
communication_handler = DefaultRequestHandler(
    agent_executor=communication_executor,
    task_store=communication_task_store,
)
communication_app = A2AStarletteApplication(
    agent_card=COMMUNICATION_AGENT_CARD,
    http_handler=communication_handler,
)

# The a2a-python SDK app serves:
#   POST /      → JSON-RPC A2A endpoint
#   GET /.well-known/agent.json → Agent Card
#
# Mount under /communication so paths become:
#   POST /communication/      → A2A endpoint
#   GET /communication/.well-known/agent.json → Agent Card
#
# Additionally, add /communication/a2a as an alias for the A2A endpoint
# to match the spec convention (POST /communication/a2a).
communication_starlette = communication_app.build()
app.mount("/communication", communication_starlette)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "cc-server"}
