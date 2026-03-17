"""Pydantic models for Profiling Agent skills (TMF629/TMF720)."""

from pydantic import BaseModel, Field


class QueryCustomerInput(BaseModel):
    """Input for query_customer skill."""

    phone: str = Field(
        description="Customer phone number (TMF629 contactMedium.characteristic.phoneNumber)"
    )


class QueryCustomerOutput(BaseModel):
    """Output for query_customer skill."""

    customer_id: str = Field(description="TMF629 Customer.id")
    name: str = Field(description="TMF629 Customer.name")
    customer_category: str = Field(
        description="TMF629 Customer.customerCategory (e.g. gold, silver, bronze)"
    )
    product_name: str = Field(
        description="TMF637 Product.name — currently subscribed product/plan"
    )


class VerifyIdentityInput(BaseModel):
    """Input for verify_identity skill."""

    customer_id: str = Field(
        description="TMF720 DigitalIdentity.relatedParty[role=customer].id"
    )
    verification_method: str = Field(
        description="Verification method: otp | biometric | knowledge (TMF720 DigitalIdentity.identityType)"
    )


class VerifyIdentityOutput(BaseModel):
    """Output for verify_identity skill."""

    identity_id: str = Field(description="TMF720 DigitalIdentity.id")
    verified: bool = Field(
        description="true if identity check passes (TMF720 DigitalIdentity.status == active)"
    )
    confidence_score: float = Field(
        description="Confidence score 0.0–1.0 (TMF720 DigitalIdentity.characteristic[name=confidence].value)"
    )
    verified_at: str = Field(
        description="TMF720 DigitalIdentity.validFor.startDateTime (ISO 8601)"
    )
