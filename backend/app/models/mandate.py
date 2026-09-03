from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class MandateScope(BaseModel):
    max_amount_per_txn: int  # in paise
    max_amount_daily: int
    allowed_categories: List[str]
    merchant_dids: List[str]
    time_window_start: datetime
    time_window_end: datetime


class IntentMandate(Document):
    """AP2-style Intent Mandate stored as a rich document"""

    mandate_id: Indexed(str, unique=True)
    buyer_did: Indexed(str)
    agent_did: Indexed(str)
    merchant_id: Indexed(str)
    scope: MandateScope
    buyer_public_key: str
    mandate_signature: str  # JWS
    status: str = "active"  # active, revoked, expired, consumed
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime

    class Settings:
        name = "intent_mandates"
        indexes = [
            "mandate_id",
            "buyer_did",
            "agent_did",
            "merchant_id",
            "status",
            "expires_at",
            [("buyer_did", 1), ("status", 1), ("expires_at", 1)],
        ]


class CartItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int


class CartMandate(Document):
    """AP2 Cart Mandate with embedded items and signatures"""

    mandate_id: str = Field(default_factory=lambda: f"cart_{uuid4().hex[:12]}")
    intent_mandate_id: Indexed(str)
    intent_mandate_ref: Optional[IntentMandate] = None  # DBRef pattern via beanie
    merchant_id: Indexed(str)
    cart_items: List[CartItem]
    total_amount: int
    currency: str = "INR"
    buyer_signature: str
    nonce: str
    guardian_decision: Optional[dict] = None  # Embedded decision
    status: str = "pending"  # pending, approved, denied, executed, expired
    razorpay_order_id: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # 15-minute TTL

    class Settings:
        name = "cart_mandates"
        indexes = [
            "mandate_id",
            "intent_mandate_id",
            "merchant_id",
            "status",
            [("intent_mandate_id", 1), ("status", 1)],
        ]
