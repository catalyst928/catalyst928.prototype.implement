"""Recommendation Agent — hosts get_nbo skill (TMF701/TMF620/TMF637).

Uses a2a-python SDK for Agent Card serving and skill dispatch.
LLM integration via Ollama with httpx.AsyncClient.
"""

import logging

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from src.agents.base import BaseAgentExecutor
from src.agents.recommendation.skills.get_nbo import get_nbo
from src.config import RECOMMENDATION_A2A_URL

logger = logging.getLogger(__name__)

RECOMMENDATION_AGENT_CARD = AgentCard(
    name="Recommendation Agent",
    description="LLM-powered next-best-offer product recommendations (TMF701/TMF620/TMF637)",
    url=f"{RECOMMENDATION_A2A_URL}/a2a",
    version="0.1.0",
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="get_nbo",
            name="Get NBO",
            description="Generate next-best-offer recommendations for a customer (TMF701 Recommendation API)",
            tags=["TMF701", "TMF620", "TMF637", "recommendation", "nbo"],
        ),
    ],
)


class RecommendationAgentExecutor(BaseAgentExecutor):
    """Executor for Recommendation Agent — get_nbo skill with Ollama integration."""

    def __init__(self, ollama_client):
        self._ollama_client = ollama_client

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        data = self._extract_input(context)
        skill = data.pop("skill", None)

        try:
            if skill == "get_nbo":
                result = await get_nbo(data, self._ollama_client)
            else:
                await self._emit_error(
                    f"Unknown skill: {skill}", context, event_queue
                )
                return

            await self._emit_result(result, context, event_queue)

        except ValueError as e:
            await self._emit_error(str(e), context, event_queue)
        except Exception as e:
            logger.exception("Recommendation Agent error")
            await self._emit_error(str(e), context, event_queue)
