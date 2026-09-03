from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class PaymentLinkRef(BaseModel):
    link_id: str
    razorpay_link_id: str
    amount: int
    status: str
    payments_count: int = 0
    created_at: datetime


class GrowthCampaign(Document):
    """AI-generated campaign with embedded payment links and metrics"""

    campaign_id: str = Field(default_factory=lambda: f"camp_{uuid4().hex[:12]}")
    merchant_id: Indexed(str)
    campaign_type: str  # abandoned_cart, upsell, cross_sell, pricing, smart_collect
    target_segment: dict = Field(default_factory=dict)  # Embedded rules
    generated_payment_links: List[PaymentLinkRef] = Field(default_factory=list)
    conversion_rate: float = 0.0
    revenue_generated: int = 0
    status: str = "draft"  # draft, active, paused, completed
    ai_reasoning: str = ""  # Why the AI suggested this campaign
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "growth_campaigns"
        indexes = [
            "campaign_id",
            "merchant_id",
            "campaign_type",
            "status",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)],
        ]
