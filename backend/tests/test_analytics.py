"""
Tests for the analytics API layer.
These tests use the real FastAPI TestClient with an in-memory MongoDB
(via beanie's test fixtures or mongomock where possible).
"""
import pytest
from datetime import datetime, timedelta

from app.models import AuditLog


pytestmark = pytest.mark.asyncio


async def test_guardian_stats_endpoint_structure(mongo_client):
    """guardian-stats endpoint returns the expected JSON shape."""
    # Insert test audit logs
    since = datetime.utcnow() - timedelta(days=30)
    await AuditLog(
        action_type="CREATE_ORDER",
        actor="GuardianAgent",
        buyer_id="did:example:buyer_demo",
        merchant_id="m_test",
        amount=5000,
        currency="INR",
        status="SUCCESS",
        guardian_decision={"decision": "approved", "reason": "All checks passed", "risk_score": 0.1},
        hmac_signature="test_sig_1",
    ).insert()

    await AuditLog(
        action_type="CREATE_ORDER",
        actor="GuardianAgent",
        buyer_id="did:example:buyer_demo",
        merchant_id="m_test",
        amount=3000,
        currency="INR",
        status="DENIED",
        guardian_decision={"decision": "denied", "reason": "Risk score exceeded threshold", "risk_score": 0.6},
        hmac_signature="test_sig_2",
    ).insert()

    from app.main import app
    from httpx import AsyncClient, ASGITransport

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/guardian-stats/m_test?days=30")
        assert response.status_code == 200
        data = response.json()
        assert "approved" in data
        assert "denied" in data
        assert "intervention_rate_pct" in data
        assert "risk_distribution" in data
        assert data["merchant_id"] == "m_test"
