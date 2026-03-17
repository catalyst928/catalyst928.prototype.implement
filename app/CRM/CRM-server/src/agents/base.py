"""Base agent executor with shared helpers for input extraction and event emission."""

import json
import uuid

from pydantic import BaseModel

from a2a.server.agent_execution import AgentExecutor
from a2a.server.agent_execution.context import RequestContext
from a2a.server.events.event_queue import EventQueue
from a2a.types import (
    Artifact,
    DataPart,
    Message,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
)


class BaseAgentExecutor(AgentExecutor):
    """Shared base for all CRM agent executors.

    Provides:
    - _extract_input(): parse skill name and data from message parts
    - _emit_result(): emit artifact + completed status
    - _emit_error(): emit failed status with message
    """

    def _extract_input(self, context: RequestContext) -> dict:
        """Extract input data from the request context message parts."""
        for part in context.message.parts:
            inner = part.root if hasattr(part, "root") else part
            if hasattr(inner, "data") and inner.data is not None:
                return dict(inner.data)
            if hasattr(inner, "text") and inner.text is not None:
                return json.loads(inner.text)
        return {}

    async def _emit_result(
        self,
        output: BaseModel,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Emit a successful result as artifact + completed status."""
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                append=False,
                last_chunk=True,
                artifact=Artifact(
                    artifact_id=f"result_{uuid.uuid4().hex[:8]}",
                    name="result",
                    parts=[
                        DataPart(
                            data=json.loads(output.model_dump_json()),
                        )
                    ],
                ),
            )
        )
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

    async def _emit_error(
        self,
        error_message: str,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        """Emit a failed status with an error message."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=context.task_id,
                context_id=context.context_id,
                final=True,
                status=TaskStatus(
                    state=TaskState.failed,
                    message=Message(
                        role="agent",
                        message_id=str(uuid.uuid4()),
                        parts=[TextPart(text=error_message)],
                    ),
                ),
            )
        )

    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> None:
        """Cancel is not supported."""
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
