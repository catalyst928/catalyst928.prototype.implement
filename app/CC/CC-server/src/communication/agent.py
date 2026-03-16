"""Communication Agent — hosts send_notification skill (TMF681).

Uses a2a-python SDK for Agent Card serving and skill dispatch.
"""

import json
import uuid
from datetime import datetime, timezone

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
    Artifact,
    DataPart,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

from src.communication.models import SendNotificationInput, SendNotificationOutput
from src.config import COMMUNICATION_A2A_URL

COMMUNICATION_AGENT_CARD = AgentCard(
    name="Communication Agent",
    description="Delivers post-order notifications to customers via SMS, email, or push (TMF681 Communication Management)",
    url=f"{COMMUNICATION_A2A_URL}/a2a",
    version="0.1.0",
    default_input_modes=["application/json"],
    default_output_modes=["application/json"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[
        AgentSkill(
            id="send_notification",
            name="Send Notification",
            description="Send a notification to a customer (TMF681 CommunicationMessage)",
            tags=["TMF681", "notification"],
        ),
    ],
)


class CommunicationAgentExecutor(AgentExecutor):
    """Executor for the Communication Agent's send_notification skill."""

    async def execute(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Handle send_notification requests."""
        # Extract input from message parts
        input_data = self._extract_input(context)
        validated = SendNotificationInput.model_validate(input_data)

        # Demo stub: generate a notification response
        output = SendNotificationOutput(
            message_id=f"msg_{uuid.uuid4().hex[:8]}",
            status="sent",
            sent_at=datetime.now(timezone.utc).isoformat(),
        )

        # Emit artifact with the result
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                append=False,
                last_chunk=True,
                artifact=Artifact(
                    artifact_id=f"notif_{uuid.uuid4().hex[:8]}",
                    name="notification_result",
                    parts=[
                        DataPart(
                            data=json.loads(output.model_dump_json()),
                        )
                    ],
                ),
            )
        )

        # Mark task as completed
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=True,
                status=TaskStatus(
                    state=TaskState.completed,
                    message=None,
                ),
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel is not supported for this agent."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=True,
                status=TaskStatus(
                    state=TaskState.rejected,
                    message=None,
                ),
            )
        )

    def _extract_input(self, context: RequestContext) -> dict:
        """Extract input data from the request context message parts."""
        for part in context.message.parts:
            # Parts are wrapped in a Part root model
            inner = part.root if hasattr(part, "root") else part
            if hasattr(inner, "data") and inner.data is not None:
                return inner.data
            if hasattr(inner, "text") and inner.text is not None:
                return json.loads(inner.text)
        return {}
