"""Configuration constants loaded from environment variables."""

import os

CRM_SERVER_URL: str = os.getenv("CRM_SERVER_URL", "http://localhost:8002")
BILLING_SERVER_URL: str = os.getenv("BILLING_SERVER_URL", "http://localhost:8003")
CC_SERVER_URL: str = os.getenv("CC_SERVER_URL", "http://localhost:8001")
NBO_MODEL_ID: str = os.getenv("NBO_MODEL_ID", "nbo-model-v1")

# A2A endpoint URLs — full URL to the JSON-RPC endpoint for each agent.
# When agents are mounted via a2a-python SDK, the endpoint is at the mount root.
PROFILING_A2A_URL: str = os.getenv(
    "PROFILING_A2A_URL", f"{CRM_SERVER_URL}/profiling"
)
RECOMMENDATION_A2A_URL: str = os.getenv(
    "RECOMMENDATION_A2A_URL", f"{CRM_SERVER_URL}/recommendation"
)
ORDER_A2A_URL: str = os.getenv(
    "ORDER_A2A_URL", f"{CRM_SERVER_URL}/order"
)
AI_MANAGEMENT_A2A_URL: str = os.getenv(
    "AI_MANAGEMENT_A2A_URL", f"{CRM_SERVER_URL}/ai-management"
)
USAGE_A2A_URL: str = os.getenv(
    "USAGE_A2A_URL", f"{BILLING_SERVER_URL}/usage"
)
COMMUNICATION_A2A_URL: str = os.getenv(
    "COMMUNICATION_A2A_URL", f"{CC_SERVER_URL}/communication"
)
