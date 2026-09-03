from datetime import datetime
from typing import Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import Field


class Merchant(Document):
    """Core merchant profile linked to Razorpay account"""

    merchant_id: str = Field(default_factory=lambda: f"merch_{uuid4().hex[:12]}")
    razorpay_account_id: Indexed(str, unique=True)
    business_name: str
    api_key_id: str
    api_key_secret_encrypted: str  # AES-256 encrypted
    business_type: str  # ecommerce, saas, b2b, etc.
    agent_config: dict = Field(default_factory=dict)  # Guardian thresholds
    mcp_endpoint: str = Field(default="")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "merchants"
        indexes = [
            "razorpay_account_id",
            "business_type",
            "created_at",
        ]
