"""
AP2 Protocol — JSON-LD Schema Definitions

Defines the JSON-LD structures for Intent Mandates and Cart Mandates.
These follow AP2-style protocol conventions:
- @context for interoperability
- Embedded signature chains
- DID-based buyer identity
- Scope constraints (amount limits, categories, merchants, time windows)
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class MandateScopeJSONLD(BaseModel):
    """JSON-LD representation of mandate scope constraints."""
    model_config = {"populate_by_name": True}

    type: str = Field(default="ap2:SpendingScope", alias="@type")
    max_amount_per_txn: int  # paise
    max_amount_daily: int  # paise
    allowed_categories: List[str]
    merchant_dids: List[str]  # merchant DIDs whitelisted
    time_window_start: str  # ISO 8601
    time_window_end: str  # ISO 8601


class AP2MandateDocument(BaseModel):
    """JSON-LD Intent Mandate document for JWS signing."""
    model_config = {"populate_by_name": True}

    context: str = Field(default="https://ap2.org/context/v1", alias="@context")
    type: str = Field(default="ap2:IntentMandate", alias="@type")
    mandate_id: str
    buyer_did: str
    agent_did: str
    merchant_id: str
    scope: MandateScopeJSONLD
    buyer_public_key: str  # PEM-encoded public key
    created_at: str  # ISO 8601
    expires_at: str  # ISO 8601
    nonce: str  # random nonce for replay protection


class AP2CartMandateDocument(BaseModel):
    """JSON-LD Cart Mandate document for JWS signing."""
    model_config = {"populate_by_name": True}

    context: str = Field(default="https://ap2.org/context/v1", alias="@context")
    type: str = Field(default="ap2:CartMandate", alias="@type")
    mandate_id: str
    intent_mandate_id: str
    merchant_id: str
    cart_items: List[dict]  # [{product_id, product_name, quantity, unit_price_paise, line_total_paise}]
    total_amount: int  # paise
    currency: str
    nonce: str  # random nonce
    created_at: str  # ISO 8601
