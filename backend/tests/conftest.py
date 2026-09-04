"""
Pytest fixtures for backend tests.
Uses a real MongoDB instance at mongodb://localhost:27017.
"""
import pytest
import pytest_asyncio
from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.models import AuditLog, IntentMandate, CartMandate, Product, Merchant


@pytest_asyncio.fixture
async def mongo_client():
    """Initialize beanie with a test database for each test."""
    client = AsyncIOMotorClient("mongodb://localhost:27017/testdb_analytics")
    await init_beanie(
        database=client.testdb_analytics,
        document_models=[AuditLog, IntentMandate, CartMandate, Product, Merchant],
    )
    yield client
    # Cleanup: drop test database
    await client.testdb_analytics.command("dropDatabase")
    client.close()
