"""Pydantic models for Communication Agent send_notification skill (TMF681)."""

from pydantic import BaseModel, Field


class SendNotificationInput(BaseModel):
    """Input for send_notification skill."""

    customer_id: str = Field(
        description="TMF681 CommunicationMessage.receiver[].id — the customer to notify"
    )
    channel: str = Field(
        description="Delivery channel: sms | email | push (TMF681 CommunicationMessage.type)"
    )
    message: str = Field(
        description="Notification body text (TMF681 CommunicationMessage.content)"
    )


class SendNotificationOutput(BaseModel):
    """Output for send_notification skill."""

    message_id: str = Field(description="TMF681 CommunicationMessage.id")
    status: str = Field(
        description="TMF681 CommunicationMessage.state (sent | failed)"
    )
    sent_at: str = Field(
        description="TMF681 CommunicationMessage.sendTime (ISO 8601)"
    )
