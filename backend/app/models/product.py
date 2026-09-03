from datetime import datetime
from typing import List, Optional
from uuid import uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class ProductVariant(BaseModel):
    sku: str
    price_paise: int
    stock_quantity: int
    attributes: dict = Field(default_factory=dict)  # color, size, etc.


class Product(Document):
    """Agent-readable product catalog with MCP-compatible metadata"""

    product_id: str = Field(default_factory=lambda: f"prod_{uuid4().hex[:12]}")
    merchant_id: Indexed(str)
    razorpay_order_id: Optional[str] = None
    name: str
    description: str
    category: Indexed(str)
    tags: List[str] = Field(default_factory=list)
    base_price_paise: int
    currency: str = "INR"
    variants: List[ProductVariant] = Field(default_factory=list)
    total_stock: int = 0
    agent_readable: dict = Field(default_factory=dict)  # UCP-style JSON-LD
    images: List[str] = Field(default_factory=list)
    is_active: bool = True
    sales_velocity: float = 0.0  # Calculated field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "products"
        indexes = [
            "merchant_id",
            "category",
            "tags",
            "is_active",
            [("merchant_id", 1), ("category", 1), ("is_active", 1)],
        ]
