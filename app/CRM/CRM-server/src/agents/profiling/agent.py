"""Profiling Agent — hosts query_customer and verify_identity skills (TMF629/TMF720).

Uses a2a-python SDK for Agent Card serving and skill dispatch.
"""

import logging

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from src.agents.base import BaseAgentExecutor
from src.agents.profiling.skills.query_customer import query_customer
from src.agents.profiling.skills.verify_identity import verify_identity
from src.config import PROFILING_A2A_URL

logger = logging.getLogger(__name__)

PROFILING_AGENT_CARD = AgentCard(
    name="Profiling Agent",
    description="Customer profile lookup and identity verification (TMF629/TMF720)",
    url=f"{PROFILING_A2A_URL}/a2a",
    version="0.1.0",
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="query_customer",
            name="Query Customer",
            description="Look up customer profile by phone number (TMF629 Customer Management)",
            tags=["TMF629", "TMF637", "customer"],
        ),
        AgentSkill(
            id="verify_identity",
            name="Verify Identity",
            description="Verify customer digital identity (TMF720 Digital Identity Management)",
            tags=["TMF720", "identity", "verification"],
        ),
    ],
)


class ProfilingAgentExecutor(BaseAgentExecutor):
    """Executor for Profiling Agent — dispatches by skill name."""

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        data = self._extract_input(context)
        skill = data.pop("skill", None)

        try:
            if skill == "query_customer":
                result = await query_customer(data)
            elif skill == "verify_identity":
                result = await verify_identity(data)
            else:
                await self._emit_error(
                    f"Unknown skill: {skill}", context, event_queue
                )
                return

            await self._emit_result(result, context, event_queue)

        except ValueError as e:
            await self._emit_error(str(e), context, event_queue)
        except Exception as e:
            logger.exception("Profiling Agent error")
            await self._emit_error(str(e), context, event_queue)
