"""Tests for Agent Card endpoints — verify all four agents serve correct cards."""


class TestAgentCards:
    def test_profiling_agent_card(self, client):
        resp = client.get("/profiling/.well-known/agent.json")
        assert resp.status_code == 200
        card = resp.json()
        assert card["name"] == "Profiling Agent"
        skill_ids = [s["id"] for s in card["skills"]]
        assert "query_customer" in skill_ids
        assert "verify_identity" in skill_ids

    def test_recommendation_agent_card(self, client):
        resp = client.get("/recommendation/.well-known/agent.json")
        assert resp.status_code == 200
        card = resp.json()
        assert card["name"] == "Recommendation Agent"
        skill_ids = [s["id"] for s in card["skills"]]
        assert "get_nbo" in skill_ids

    def test_order_agent_card(self, client):
        resp = client.get("/order/.well-known/agent.json")
        assert resp.status_code == 200
        card = resp.json()
        assert card["name"] == "Order Agent"
        skill_ids = [s["id"] for s in card["skills"]]
        assert "create_order" in skill_ids

    def test_ai_management_agent_card(self, client):
        resp = client.get("/ai-management/.well-known/agent.json")
        assert resp.status_code == 200
        card = resp.json()
        assert card["name"] == "AI Management Agent"
        skill_ids = [s["id"] for s in card["skills"]]
        assert "get_ai_model_status" in skill_ids
