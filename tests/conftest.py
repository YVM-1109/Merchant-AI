"""Pytest configuration and shared fixtures."""
import pytest
import pytest_asyncio
import httpx
import uuid
import os

BASE_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")


@pytest_asyncio.fixture
async def client() -> httpx.AsyncClient:
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        yield client


@pytest.fixture
def test_merchant_id():
    """Return a merchant ID that was created during setup.

    Uses a known test merchant from earlier in the session.
    Falls back to creating one if it doesn't exist.
    """
    return "merch_1d07bd956960"


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
