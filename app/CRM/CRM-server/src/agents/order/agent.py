"""Order Agent — hosts create_order skill (TMF622).

Uses a2a-python SDK for Agent Card serving and skill dispatch.
"""

import logging

from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from src.agents.base import BaseAgentExecutor
from src.agents.order.skills.create_order import create_order
from src.config import ORDER_A2A_URL

logger = logging.getLogger(__name__)

ORDER_AGENT_CARD = AgentCard(
    name="Order Agent",
    description="Product order creation and management (TMF622)",
    url=f"{ORDER_A2A_URL}/a2a",
    version="0.1.0",
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="create_order",
            name="Create Order",
            description="Create a product order for a customer (TMF622 Product Order Management)",
            tags=["TMF622", "order"],
        ),
    ],
)


class OrderAgentExecutor(BaseAgentExecutor):
    """Executor for Order Agent — create_order skill."""

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        data = self._extract_input(context)
        skill = data.pop("skill", None)

        try:
            if skill == "create_order":
                result = await create_order(data)
            else:
                await self._emit_error(
                    f"Unknown skill: {skill}", context, event_queue
                )
                return

            await self._emit_result(result, context, event_queue)

        except ValueError as e:
            await self._emit_error(str(e), context, event_queue)
        except Exception as e:
            logger.exception("Order Agent error")
            await self._emit_error(str(e), context, event_queue)
