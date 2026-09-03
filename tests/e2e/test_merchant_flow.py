"""
E2E test: Merchant onboarding and product management flow.

Tests the full lifecycle:
1. Create a merchant
2. Verify in Mongo
3. Create products for the merchant
4. List products by merchant
"""
import pytest
import pytest_asyncio
import httpx
import uuid
from typing import AsyncGenerator

BASE_URL = "http://localhost:8000"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        yield client


@pytest.mark.asyncio
async def test_merchant_crud_flow(client: httpx.AsyncClient):
    """Test creating, reading, and listing merchants."""
    # Step 1: Create a merchant
    merchant_data = {
        "razorpay_account_id": f"acc_e2e_{uuid.uuid4().hex[:8]}",
        "business_name": "E2E Test Merchant",
        "api_key_id": "rzp_test_key_e2e",
        "api_key_secret_encrypted": "encrypted_secret_e2e",
        "business_type": "retail",
        "agent_config": {"auto_capture": True},
    }

    res = await client.post("/api/v1/merchants/", json=merchant_data)
    assert res.status_code == 201
    created = res.json()
    assert created["business_name"] == "E2E Test Merchant"
    assert created["is_active"] is True
    merchant_id = created["merchant_id"]

    # Step 2: Get the merchant
    res = await client.get(f"/api/v1/merchants/{merchant_id}")
    assert res.status_code == 200
    fetched = res.json()
    assert fetched["merchant_id"] == merchant_id
    assert fetched["business_name"] == "E2E Test Merchant"

    # Step 3: List all merchants — should include ours
    res = await client.get("/api/v1/merchants/")
    assert res.status_code == 200
    merchants = res.json()
    assert any(m["merchant_id"] == merchant_id for m in merchants)

    # Step 4: Update merchant
    res = await client.patch(
        f"/api/v1/merchants/{merchant_id}",
        json={"business_name": "Updated E2E Merchant"},
    )
    assert res.status_code == 200
    assert res.json()["business_name"] == "Updated E2E Merchant"

    # Step 5: Delete merchant
    res = await client.delete(f"/api/v1/merchants/{merchant_id}")
    assert res.status_code == 204

    # Step 6: Verify deleted
    res = await client.get(f"/api/v1/merchants/{merchant_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_product_crud_flow(client: httpx.AsyncClient, test_merchant_id: str):
    """Test creating and listing products for a merchant."""
    product_data = {
        "merchant_id": test_merchant_id,
        "name": "Test Wireless Mouse",
        "description": "E2E test product",
        "category": "electronics",
        "tags": ["wireless", "test"],
        "base_price_paise": 50000,
        "currency": "INR",
        "variants": [
            {"sku": "TWM-001", "price_paise": 50000, "stock_quantity": 100}
        ],
        "total_stock": 100,
        "agent_readable": {"color": "black"},
        "is_active": True,
    }

    res = await client.post("/api/v1/products/", json=product_data)
    assert res.status_code == 201
    created = res.json()
    assert created["name"] == "Test Wireless Mouse"
    assert created["merchant_id"] == test_merchant_id
    product_id = created["product_id"]

    # List products by merchant
    res = await client.get(f"/api/v1/products/?merchant_id={test_merchant_id}")
    assert res.status_code == 200
    products = res.json()
    assert len(products) > 0
    assert any(p["product_id"] == product_id for p in products)

    # Get single product
    res = await client.get(f"/api/v1/products/{product_id}")
    assert res.status_code == 200
    assert res.json()["product_id"] == product_id
