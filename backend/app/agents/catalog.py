"""
CatalogAgent — Product discovery and negotiation.

Discovers products via MongoDB queries, checks stock levels,
and can negotiate prices within defined merchant rules.
MCP-compatible: each async method maps to an MCP tool.
"""
from typing import Optional

from app.agents.tools import AgentTools
from app.models import Product


class CatalogAgent:
    """MCP-compatible catalog server for product discovery."""

    def __init__(self, tools: AgentTools):
        self.tools = tools

    async def run(self, message: str, context: dict) -> dict:
        """Process a catalog query and return results."""
        merchant_id = context.get("merchant_id", "")

        if "search" in message.lower() or "find" in message.lower():
            parts = message.split("search for")
            if len(parts) > 1:
                query = parts[1].strip()
                return await self.tools.search_products(merchant_id, query)

        # Default: list products
        return await self.tools.list_products(merchant_id)

    async def list_products(
        self,
        merchant_id: str,
        category: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """MCP tool: list_products"""
        return await self.tools.list_products(merchant_id, category, limit=limit)

    async def get_product(self, product_id: str) -> Optional[dict]:
        """MCP tool: get_product"""
        return await self.tools.get_product(product_id)

    async def check_availability(self, product_id: str) -> dict:
        """MCP tool: check_availability"""
        product = await self.tools.get_product(product_id)
        if not product:
            return {"available": False, "reason": "Product not found"}
        return {
            "available": product["total_stock"] > 0,
            "stock": product["total_stock"],
            "price_paise": product["base_price_paise"],
        }

    async def negotiate_price(self, product_id: str, proposed_price_paise: int) -> dict:
        """MCP tool: negotiate_price — simple merchant rule: can't go below 80% of base price."""
        product = await self.tools.get_product(product_id)
        if not product:
            return {"accepted": False, "reason": "Product not found"}

        final_price = min(proposed_price_paise, product["base_price_paise"])
        min_price = int(product["base_price_paise"] * 0.8)  # 80% floor

        if final_price >= min_price:
            return {
                "accepted": True,
                "price_paise": final_price,
                "discount_paise": product["base_price_paise"] - final_price,
            }
        return {
            "accepted": False,
            "reason": f"Proposed price below minimum ({min_price} paise)",
            "final_offer_paise": min_price,
        }
