"""
Shared agent tools available to all LangGraph agents.

Each agent node in the graph has access to these tools for:
- Product discovery (via MongoDB aggregation)
- Order creation (via Razorpay)
- Payment capture
- Audit querying
"""
from typing import List, Optional

from app.models import Product
from app.razorpay_client import RazorpayClient


class AgentTools:
    """Collection of tools callable by LangGraph agents."""

    def __init__(self, razorpay_client: Optional[RazorpayClient] = None):
        self.razorpay = razorpay_client or RazorpayClient()

    # ── Catalog tools ───────────────────────────────────────────────

    async def list_products(
        self,
        merchant_id: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
    ) -> list[dict]:
        """List products for a merchant, optionally filtered by category/tags."""
        query = Product.find(Product.merchant_id == merchant_id)
        if category:
            query = Product.find(Product.merchant_id == merchant_id, Product.category == category)
        if tags:
            query = query.find({"tags": {"$in": tags}})

        products = await query.limit(limit).to_list()
        return [
            {
                "product_id": p.product_id,
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "base_price_paise": p.base_price_paise,
                "total_stock": p.total_stock,
                "tags": p.tags,
                "agent_readable": p.agent_readable,
            }
            for p in products
        ]

    async def get_product(self, product_id: str) -> Optional[dict]:
        """Fetch a single product by ID."""
        product = await Product.find_one(Product.product_id == product_id)
        if not product:
            return None
        return {
            "product_id": product.product_id,
            "merchant_id": product.merchant_id,
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "base_price_paise": product.base_price_paise,
            "total_stock": product.total_stock,
            "variants": [v.model_dump() for v in product.variants],
            "tags": product.tags,
            "agent_readable": product.agent_readable,
        }

    # ── Razorpay tools ──────────────────────────────────────────────

    async def create_order(self, merchant_id: str, amount: int, currency: str = "INR", receipt: str = "") -> dict:
        """Create a Razorpay order."""
        return self.razorpay.create_order(amount=amount, currency=currency, receipt=receipt)

    async def capture_payment(self, payment_id: str, amount: int, currency: str = "INR") -> dict:
        """Capture a Razorpay payment."""
        return self.razorpay.capture_payment(payment_id=payment_id, amount=amount, currency=currency)

    # ── Search tools ────────────────────────────────────────────────

    async def search_products(self, merchant_id: str, query: str, limit: int = 10) -> list[dict]:
        """Full-text search across product name/description/tags."""
        from beanie import PydanticObjectId

        pipeline = [
            {"$match": {"merchant_id": merchant_id}},
            {"$search": {"index": "default", "text": {"query": query, "path": ["name", "description", "tags"]}}},
            {"$limit": limit},
        ]

        results = await Product.aggregate(pipeline).to_list()
        return [
            {
                "product_id": p["product_id"],
                "name": p["name"],
                "description": p["description"],
                "base_price_paise": p["base_price_paise"],
                "category": p["category"],
            }
            for p in results
        ]
