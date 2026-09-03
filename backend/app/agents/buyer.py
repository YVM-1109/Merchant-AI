"""
BuyerAgent (ShopBot) — AI buyer that navigates AP2 protocol to complete purchases.

Flow:
1. Presents Intent Mandate to the merchant's storefront
2. Creates a Cart Mandate (signed with buyer's private key)
3. Passes through GuardianAgent for bounds-checking
4. Creates Razorpay order → captures payment
5. Logs everything to the audit trail
"""
import json
from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from app.agents.tools import AgentTools
from app.agents.guardian import GuardianAgent, MoneyAction
from app.ap2.crypto import AP2Crypto
from app.ap2.mandates import create_intent_mandate, sign_cart_mandate
from app.models import IntentMandate, CartMandate, CartItem, AuditLog


class BuyerAgent:
    """AI Buyer Agent (ShopBot) using AP2 protocol."""

    def __init__(self, tools: AgentTools, guardian: GuardianAgent, buyer_private_key: str, buyer_did: str):
        self.tools = tools
        self.guardian = guardian
        self.buyer_private_key = buyer_private_key
        self.buyer_did = buyer_did

    async def run(self, message: str, context: dict) -> dict:
        """Process a buyer request like 'I want to buy a wireless mouse for under ₹1000'.

        Steps:
        1. Interpret intent (category, budget)
        2. Discover products via CatalogAgent
        3. Create Cart Mandate + pass through Guardian
        4. Execute Razorpay order
        """
        merchant_id = context.get("merchant_id", "")

        # Simple intent parsing — in production, use an LLM
        intent = self._parse_intent(message)

        # Step 1: Discover products
        products = await self.tools.list_products(
            merchant_id=merchant_id,
            category=intent.get("category"),
            limit=5,
        )

        if not products:
            return {"reply": "No products found matching your criteria.", "status": "no_products"}

        # Step 2: Pick the best match
        best_product = self._select_product(products, intent)

        # Step 3: Create Cart Mandate
        cart_item = CartItem(
            product_id=best_product["product_id"],
            product_name=best_product["name"],
            quantity=1,
            unit_price_paise=best_product["base_price_paise"],
            line_total_paise=best_product["base_price_paise"],
        )

        cart_mandate_id, buyer_signature = sign_cart_mandate(
            intent_mandate_id=context.get("intent_mandate_id", ""),
            merchant_id=merchant_id,
            cart_items=[cart_item],
            total_amount=best_product["base_price_paise"],
            currency="INR",
            buyer_private_key_pem=self.buyer_private_key,
        )

        # Step 4: Guardian validation
        action = MoneyAction(
            action_type="CREATE_ORDER",
            amount=best_product["base_price_paise"],
            currency="INR",
            merchant_id=merchant_id,
            buyer_id=self.buyer_did,
            mandate_id=context.get("intent_mandate_id", ""),
            category=best_product["category"],
            agent_id="BuyerAgent",
            request_payload={"cart_item": cart_item.model_dump()},
        )

        # Fetch the actual IntentMandate to pass to guardian
        intent_mandate = await IntentMandate.find_one(
            IntentMandate.mandate_id == context.get("intent_mandate_id", "")
        )
        if not intent_mandate:
            return {"reply": "No active mandate found. Please create one first.", "status": "no_mandate"}

        guardian_result = await self.guardian.validate_action(action, intent_mandate)

        if guardian_result["decision"] != "approved":
            await self.guardian.log_decision(action, guardian_result)
            return {
                "reply": f"Purchase blocked: {guardian_result['reason']}",
                "status": "denied",
                "guardian_decision": guardian_result,
            }

        # Step 5: Create Razorpay order
        order = self.tools.razorpay.create_order(
            amount=best_product["base_price_paise"],
            currency="INR",
            receipt=cart_mandate_id,
        )

        # Step 6: Log the approved decision
        await self.guardian.log_decision(action, guardian_result)

        return {
            "reply": f"✅ Purchase approved! Order created for {best_product['name']} (₹{best_product['base_price_paise']/100:.0f})",
            "status": "success",
            "product": best_product,
            "order": order,
            "guardian_decision": guardian_result,
            "cart_mandate_id": cart_mandate_id,
        }

    def _parse_intent(self, message: str) -> dict:
        """Simple intent parser — extracts category and budget from natural language."""
        msg = message.lower()
        intent = {"category": None, "max_price_paise": None}

        categories = ["electronics", "books", "clothing", "food", "groceries"]
        for cat in categories:
            if cat in msg:
                intent["category"] = cat
                break

        # Extract price (₹ or rupees)
        import re
        price_match = re.search(r'₹(\d+)|(\d+)\s*rupee', msg)
        if price_match:
            amount = int(price_match.group(1) or price_match.group(2))
            intent["max_price_paise"] = amount * 100

        return intent

    def _select_product(self, products: list[dict], intent: dict) -> dict:
        """Select the best product matching the intent."""
        if intent.get("max_price_paise"):
            affordable = [p for p in products if p["base_price_paise"] <= intent["max_price_paise"]]
            if affordable:
                products = affordable

        if intent.get("category"):
            filtered = [p for p in products if p["category"] == intent["category"]]
            if filtered:
                products = filtered

        # Return highest-rated by sales_velocity or just first
        return products[0] if products else None
