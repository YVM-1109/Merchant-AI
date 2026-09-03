from datetime import datetime
from typing import Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import Field


class AuditLog(Document):
    """
    Immutable audit trail for every money action.
    Embedded reasoning, guardian decision, and full request/response.
    """

    audit_id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:16]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: Indexed(str)  # CREATE_ORDER, CAPTURE_PAYMENT, REFUND, etc.
    actor: str  # GrowthAgent, BuyerAgent, GuardianAgent, Manual
    agent_id: Optional[str] = None
    buyer_id: Optional[str] = None
    merchant_id: Indexed(str)
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    mandate_id: Optional[str] = None

    # Embedded rich documents
    guardian_decision: dict = Field(default_factory=dict)
    reasoning: str = ""  # LLM-generated explanation
    request_payload: dict = Field(default_factory=dict)
    response_payload: dict = Field(default_factory=dict)
    status: str  # SUCCESS, FAILED, DENIED
    error_details: Optional[dict] = None

    # Tamper evidence
    hmac_signature: str
    previous_audit_hash: Optional[str] = None  # Blockchain-style chain

    class Settings:
        name = "audit_logs"
        indexes = [
            "audit_id",
            "action_type",
            "merchant_id",
            "razorpay_order_id",
            "razorpay_payment_id",
            "mandate_id",
            "status",
            [("merchant_id", 1), ("action_type", 1), ("timestamp", -1)],
            [("timestamp", -1)],  # Time-series queries
        ]
