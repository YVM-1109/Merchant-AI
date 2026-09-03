"""
E2E test: Buyer ShopBot flow.

Tests the complete end-to-end purchase journey:
1. Browse catalog for products
2. Create intent mandate
3. Sign cart mandate
4. Guardian validation
5. Razorpay order creation
"""
import pytest
import pytest_asyncio
import httpx
import uuid
from typing import AsyncGenerator

BASE_URL = "http://localhost:8000"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=httpx.Timeout(30.0)) as client:
        yield client


@pytest.fixture
def test_key_pair():
    """Generate a valid ES256 key pair for buyer signing."""
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend

    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return priv_pem


@pytest.mark.asyncio
async def test_shopbot_full_flow(client: httpx.AsyncClient, test_merchant_id: str, test_key_pair: str):
    """Test the complete ShopBot demo flow end-to-end."""
    payload = {
        "merchant_id": test_merchant_id,
        "buyer_did": f"did:example:buyer_e2e_{uuid.uuid4().hex[:8]}",
        "message": "I want to buy a wireless mouse for under ₹1000",
        "buyer_private_key": test_key_pair,
    }

    res = await client.post("/api/v1/demo/shopbot", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "success"
    assert "intent_mandate_id" in data
    assert "cart_mandate_id" in data
    assert "guardian_decision" in data
    assert data["guardian_decision"]["decision"] == "approved"
    assert "razorpay_order" in data
    assert "product" in data


@pytest.mark.asyncio
async def test_shopbot_no_products(client: httpx.AsyncClient, test_key_pair: str):
    """Test ShopBot with a merchant that has no products."""
    payload = {
        "merchant_id": f"m_no_products_{uuid.uuid4().hex[:8]}",
        "buyer_did": "did:example:buyer_no_products",
        "message": "I want to buy something",
        "buyer_private_key": test_key_pair,
    }

    res = await client.post("/api/v1/demo/shopbot", json=payload)
    assert res.status_code == 200

    data = res.json()
    assert data["status"] == "no_products"


@pytest.mark.asyncio
async def test_shopbot_requires_private_key(client: httpx.AsyncClient, test_merchant_id: str):
    """Test that ShopBot rejects requests without a valid private key."""
    payload = {
        "merchant_id": test_merchant_id,
        "buyer_did": "did:example:buyer_no_key",
        "message": "I want to buy something",
        "buyer_private_key": "",
    }

    res = await client.post("/api/v1/demo/shopbot", json=payload)
    assert res.status_code == 400
    assert "buyer_private_key is required" in res.json()["detail"]


@pytest.mark.asyncio
async def test_analytics_endpoints(client: httpx.AsyncClient, test_merchant_id: str):
    """Test analytics dashboard endpoint."""
    res = await client.get(f"/api/v1/analytics/dashboard/{test_merchant_id}?days=7")
    assert res.status_code == 200
    data = res.json()
    assert "merchant_id" in data
    assert "revenue" in data
    assert "guardian" in data
    assert "daily_trend" in data


@pytest.mark.asyncio
async def test_growth_campaigns_endpoint(client: httpx.AsyncClient, test_merchant_id: str):
    """Test growth campaigns endpoint."""
    res = await client.post(
        "/api/v1/growth/campaigns",
        json={
            "merchant_id": test_merchant_id,
            "campaign_type": "abandoned_cart",
            "target_segment": "all",
            "discount_percentage": 15,
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
