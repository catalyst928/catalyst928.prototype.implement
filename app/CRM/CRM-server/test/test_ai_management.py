"""Tests for AI Management Agent — get_ai_model_status skill."""

import asyncio

from test.helpers import extract_artifact_data, extract_error_status, make_a2a_request


class TestGetAiModelStatus:
    def test_active_model(self, client):
        resp = make_a2a_request(
            client, "/ai-management", "get_ai_model_status",
            {"model_id": "qwen2.5_7b"},
        )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["model_id"] == "qwen2.5_7b"
        assert data["model_name"] == "qwen2.5:7b"
        assert data["version"] == "7b"
        assert data["status"] == "active"
        assert data["accuracy_score"] == 0.87

    def test_unknown_model(self, client):
        resp = make_a2a_request(
            client, "/ai-management", "get_ai_model_status",
            {"model_id": "unknown_model"},
        )
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "AIModel not found" in (status.get("message") or "")


class TestInactiveModel:
    def test_inactive_status_returned(self, client):
        """Verify inactive model status is returned correctly."""
        from src.db import get_db

        async def _set_inactive():
            db = get_db()
            await db.execute(
                "UPDATE ai_models SET status = 'inactive' WHERE id = 'qwen2.5_7b'"
            )
            await db.commit()

        asyncio.get_event_loop().run_until_complete(_set_inactive())

        resp = make_a2a_request(
            client, "/ai-management", "get_ai_model_status",
            {"model_id": "qwen2.5_7b"},
        )
        assert resp.status_code == 200
        data = extract_artifact_data(resp.json())
        assert data["status"] == "inactive"


class TestUnknownSkill:
    def test_unknown_skill_returns_error(self, client):
        resp = make_a2a_request(client, "/ai-management", "nonexistent_skill", {})
        assert resp.status_code == 200
        status = extract_error_status(resp.json())
        assert status.get("state") == "failed"
        assert "Unknown skill" in (status.get("message") or "")
