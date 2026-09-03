"""
MCP Catalog Server — exposes product catalog as MCP tools.

Implements the Model Context Protocol (MCP) for catalog operations:
  - list_products: Search/list merchant products
  - get_product_details: Get full details of a single product
  - check_availability: Check stock level
  - negotiate_price: Suggest a discounted price for bulk orders

Designed to be MCP-compatible so frontend or other agents can
discover products via a standardized protocol.
"""
import json
from typing import Optional

from app.models import Product


class MCPCatalogServer:
    """MCP-compatible catalog server backed by MongoDB via Beanie."""

    def __init__(self, transport: str = "stdio"):
        self.transport = transport
        self.name = "merchant-catalog"
        self.version = "1.0.0"

    async def list_products(
        self,
        merchant_id: str,
        category: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
    ) -> list[dict]:
        """List products for a merchant, optionally filtered by category or search term."""
        query = {"merchant_id": merchant_id}
        if category:
            query["category"] = category
        if search:
            # Case-insensitive partial match on product name
            products = await Product.find(
                Product.merchant_id == merchant_id,
                Product.name.search(search, case_sensitive=False),
            ).to_list()
        else:
            products = await Product.find(
                Product.merchant_id == merchant_id,
            ).limit(limit).to_list()

        return [
            {
                "product_id": str(p.id),
                "name": p.name,
                "description": p.description,
                "category": p.category,
                "base_price_paise": p.base_price_paise,
                "currency": p.currency,
                "total_stock": p.total_stock,
                "sales_velocity": getattr(p, "sales_velocity", 0),
            }
            for p in products
        ]

    async def get_product_details(self, product_id: str) -> dict:
        """Get full details of a single product."""
        product = await Product.get(product_id)
        if not product:
            return {"error": "Product not found", "product_id": product_id}

        return {
            "product_id": str(product.id),
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "base_price_paise": product.base_price_paise,
            "currency": product.currency,
            "total_stock": product.total_stock,
            "sales_velocity": getattr(product, "sales_velocity", 0),
            "merchant_id": product.merchant_id,
            "metadata": product.metadata or {},
        }

    async def check_availability(self, product_id: str) -> dict:
        """Check stock availability for a product."""
        product = await Product.get(product_id)
        if not product:
            return {"product_id": product_id, "available": False, "reason": "not_found"}

        return {
            "product_id": product_id,
            "available": product.total_stock > 0,
            "total_stock": product.total_stock,
            "unit": "units",
        }

    async def negotiate_price(self, product_id: str, quantity: int) -> dict:
        """Suggest a discounted price for bulk orders."""
        product = await Product.get(product_id)
        if not product:
            return {"product_id": product_id, "error": "not_found"}

        base_price = product.base_price_paise
        discount_pct = 0.0

        if quantity >= 100:
            discount_pct = 0.10  # 10% for bulk orders of 100+
        elif quantity >= 50:
            discount_pct = 0.05  # 5% for 50+
        elif quantity >= 10:
            discount_pct = 0.02  # 2% for 10+

        discounted_price = int(base_price * quantity * (1 - discount_pct))

        return {
            "product_id": product_id,
            "quantity": quantity,
            "base_total_paise": base_price * quantity,
            "discount_pct": discount_pct,
            "discounted_total_paise": discounted_price,
            "currency": product.currency,
        }

    async def search_products(self, merchant_id: str, query: str, limit: int = 10) -> list[dict]:
        """Full-text search across product names and descriptions."""
        products = await Product.find(
            Product.merchant_id == merchant_id,
            Product.name.search(query, case_sensitive=False),
        ).limit(limit).to_list()

        return [
            {
                "product_id": str(p.id),
                "name": p.name,
                "category": p.category,
                "base_price_paise": p.base_price_paise,
                "currency": p.currency,
            }
            for p in products
        ]


# ─── MCP Tool definitions for stdio transport ───────────────────────
async def handle_mcp_request(request: str) -> str:
    """Handle an MCP tool call request (JSON-RPC 2.0 over stdio)."""
    data = json.loads(request)
    method = data.get("method", "")
    params = data.get("params", {})
    server = MCPCatalogServer()

    if method == "list_products":
        result = await server.list_products(
            merchant_id=params.get("merchant_id", ""),
            category=params.get("category"),
            search=params.get("search"),
            limit=params.get("limit", 20),
        )
        return json.dumps({"id": data.get("id"), "result": result})
    elif method == "get_product_details":
        result = await server.get_product_details(params.get("product_id", ""))
        return json.dumps({"id": data.get("id"), "result": result})
    elif method == "check_availability":
        result = await server.check_availability(params.get("product_id", ""))
        return json.dumps({"id": data.get("id"), "result": result})
    elif method == "negotiate_price":
        result = await server.negotiate_price(
            product_id=params.get("product_id", ""),
            quantity=params.get("quantity", 1),
        )
        return json.dumps({"id": data.get("id"), "result": result})
    else:
        return json.dumps({"id": data.get("id"), "error": {"code": -32601, "message": f"Method {method} not found"}})
