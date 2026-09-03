"""
Demo API — End-to-end buyer flow simulation.

Simulates a complete ShopBot purchase flow:
1. Discover products via MCP catalog
2. Create intent mandate + cart mandate
3. Guardian validation
4. Razorpay order creation + payment capture simulation
"""
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.agents.graph import AgentGraph
from app.mcp.server import MCPCatalogServer
from app.razorpay_client import RazorpayClient
from app.models import IntentMandate, CartMandate, CartItem
from app.agents.guardian import GuardianAgent, MoneyAction
from app.agents.tools import AgentTools
from app.ap2.mandates import create_intent_mandate, sign_cart_mandate

router = APIRouter(prefix="/api/v1/demo", tags=["demo"])


class ShopBotRequest(BaseModel):
    merchant_id: str
    buyer_did: str
    message: str
    buyer_private_key: str


@router.post("/shopbot")
async def demo_shopbot(req: ShopBotRequest):
    """
    Simulate a ShopBot purchase flow.

    Example payload:
    {
        "merchant_id": "m_test123",
        "buyer_did": "did:example:buyer42",
        "message": "I want to buy a wireless mouse for under ₹1000",
        "buyer_private_key": "<PEM private key>"
    }
    """
    if not req.buyer_private_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="buyer_private_key is required. Generate one with the AP2 crypto tool.",
        )

    # Step 1: Discover products via MCP
    catalog = MCPCatalogServer()
    products = await catalog.list_products(merchant_id=req.merchant_id, limit=10)

    if not products:
        return {
            "step": 1,
            "status": "no_products",
            "message": "No products found for this merchant.",
            "products": [],
        }

    # Step 2: Select best product (simple heuristic — lowest price under budget)
    # In production, use an LLM to parse the natural-language intent
    best_product = products[0]  # Just pick first for demo
    selected_price = best_product["base_price_paise"]

    # Step 3: Create Intent Mandate (returns an IntentMandate object)
    intent_mandate = create_intent_mandate(
        buyer_did=req.buyer_did,
        agent_did="did:example:shopbot_agent",
        merchant_id=req.merchant_id,
        max_amount_per_txn=selected_price,
        max_amount_daily=selected_price * 3,
        allowed_categories=[best_product["category"]],
        merchant_dids=[req.merchant_id],
        duration_hours=24,
    )
    await intent_mandate.create()
    intent_mandate_id = intent_mandate.mandate_id

    # Step 4: Create Cart Mandate
    cart_item = CartItem(
        product_id=best_product["product_id"],
        product_name=best_product["name"],
        quantity=1,
        unit_price_paise=selected_price,
        line_total_paise=selected_price,
    )

    cart_mandate_id, buyer_sig = sign_cart_mandate(
        intent_mandate_id=intent_mandate_id,
        merchant_id=req.merchant_id,
        cart_items=[cart_item],
        total_amount=selected_price,
        currency="INR",
        buyer_private_key_pem=req.buyer_private_key,
    )

    # Step 5: Guardian validation — reuse the intent_mandate we just created
    tools = AgentTools()
    guardian = GuardianAgent(tools)

    action = MoneyAction(
        action_type="CREATE_ORDER",
        amount=selected_price,
        currency="INR",
        merchant_id=req.merchant_id,
        buyer_id=req.buyer_did,
        mandate_id=intent_mandate_id,
        category=best_product["category"],
        agent_id="DemoShopBot",
        request_payload={"message": req.message},
    )

    guardian_result = await guardian.validate_action(action, intent_mandate)

    if guardian_result["decision"] != "approved":
        return {
            "step": 2,
            "status": "denied",
            "message": f"Guardian denied: {guardian_result['reason']}",
            "guardian_decision": guardian_result,
        }

    # Step 6: Create CartMandate document
    cart_mandate = CartMandate(
        mandate_id=cart_mandate_id,
        intent_mandate_id=intent_mandate_id,
        merchant_id=req.merchant_id,
        buyer_did=req.buyer_did,
        cart_items=[cart_item],
        total_amount=selected_price,
        currency="INR",
        buyer_signature=buyer_sig,
        nonce=uuid4().hex,
        status="signed_pending_payment",
        expires_at=datetime.utcnow() + timedelta(minutes=15),
    )
    await cart_mandate.create()

    # Step 7: Create Razorpay order
    razorpay = RazorpayClient()
    order = razorpay.create_order(
        amount=selected_price,
        currency="INR",
        receipt=cart_mandate_id,
    )

    # Step 8: Simulate payment capture (in test mode, this is instant)
    payment = razorpay.capture_payment(
        payment_id=order.get("payments", [{}])[0].get("payment_id", "pay_test"),
        amount=selected_price,
    )

    # Step 9: Update status
    cart_mandate.status = "paid"
    await cart_mandate.save()

    # Step 10: Log audit
    await guardian.log_decision(action, guardian_result)

    return {
        "step": 3,
        "status": "success",
        "message": "✅ Full ShopBot flow completed!",
        "intent_mandate_id": intent_mandate_id,
        "cart_mandate_id": cart_mandate_id,
        "product": {
            "name": best_product["name"],
            "category": best_product["category"],
            "price_paise": selected_price,
            "price_display": f"₹{selected_price / 100:.0f}",
        },
        "guardian_decision": guardian_result,
        "razorpay_order": {
            "id": order.get("id"),
            "status": order.get("status"),
        },
        "payment": payment,
    }


@router.get("/products/{merchant_id}")
async def list_products(merchant_id: str):
    """List products for a merchant (for demo setup)."""
    catalog = MCPCatalogServer()
    products = await catalog.list_products(merchant_id=merchant_id, limit=20)
    return {"merchant_id": merchant_id, "products": products}
