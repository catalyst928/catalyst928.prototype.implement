"""AI Management Agent — hosts get_ai_model_status skill (TMF915).

Uses a2a-python SDK for Agent Card serving and skill dispatch.
"""

import logging

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from src.agents.base import BaseAgentExecutor
from src.agents.ai_management.skills.get_ai_model_status import get_ai_model_status
from src.config import AI_MANAGEMENT_A2A_URL

logger = logging.getLogger(__name__)

AI_MANAGEMENT_AGENT_CARD = AgentCard(
    name="AI Management Agent",
    description="AI model lifecycle status monitoring (TMF915)",
    url=f"{AI_MANAGEMENT_A2A_URL}/a2a",
    version="0.1.0",
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="get_ai_model_status",
            name="Get AI Model Status",
            description="Query the status of an AI model (TMF915 AI Management)",
            tags=["TMF915", "ai", "model"],
        ),
    ],
)


class AIManagementAgentExecutor(BaseAgentExecutor):
    """Executor for AI Management Agent — get_ai_model_status skill."""

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        data = self._extract_input(context)
        skill = data.pop("skill", None)

        try:
            if skill == "get_ai_model_status":
                result = await get_ai_model_status(data)
            else:
                await self._emit_error(
                    f"Unknown skill: {skill}", context, event_queue
                )
                return

            await self._emit_result(result, context, event_queue)

        except ValueError as e:
            await self._emit_error(str(e), context, event_queue)
        except Exception as e:
            logger.exception("AI Management Agent error")
            await self._emit_error(str(e), context, event_queue)
