"""Configuration constants loaded from environment variables."""

import os

CRM_SERVER_PORT: int = int(os.getenv("CRM_SERVER_PORT", "8002"))
CRM_SERVER_URL: str = os.getenv("CRM_SERVER_URL", f"http://localhost:{CRM_SERVER_PORT}")

DB_PATH: str = os.getenv("CRM_DB_PATH", "crm.db")

OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# A2A endpoint URLs for Agent Cards
PROFILING_A2A_URL: str = f"{CRM_SERVER_URL}/profiling"
RECOMMENDATION_A2A_URL: str = f"{CRM_SERVER_URL}/recommendation"
ORDER_A2A_URL: str = f"{CRM_SERVER_URL}/order"
AI_MANAGEMENT_A2A_URL: str = f"{CRM_SERVER_URL}/ai-management"
