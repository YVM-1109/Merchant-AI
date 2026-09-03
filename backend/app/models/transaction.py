from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import Field


class RazorpayOrder(Document):
    """Razorpay order document with embedded payment attempts"""

    razorpay_order_id: Indexed(str, unique=True)
    merchant_id: Indexed(str)
    amount: int
    currency: str = "INR"
    status: str = "created"  # created, attempted, paid, failed
    receipt: str
    notes: dict = Field(default_factory=dict)
    cart_mandate_id: Optional[str] = None
    payment_attempts: List[dict] = Field(default_factory=list)  # Embedded history
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "razorpay_orders"
        indexes = [
            "razorpay_order_id",
            "merchant_id",
            "status",
            "cart_mandate_id",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)],
        ]


class RazorpayPayment(Document):
    """Individual payment with full Razorpay response embedded"""

    razorpay_payment_id: Indexed(str, unique=True)
    order_id: Indexed(str)  # References razorpay_orders.razorpay_order_id
    merchant_id: Indexed(str)
    amount: int
    status: str  # created, authorized, captured, refunded, failed
    method: Optional[str] = None  # upi, card, netbanking, etc.
    email: Optional[str] = None
    contact: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_reason: Optional[str] = None
    captured: bool = False
    captured_at: Optional[datetime] = None
    fee: Optional[int] = None
    tax: Optional[int] = None
    raw_response: dict = Field(default_factory=dict)  # Full Razorpay payload
    refund_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "razorpay_payments"
        indexes = [
            "razorpay_payment_id",
            "order_id",
            "merchant_id",
            "status",
            "method",
            "captured",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)],
        ]
