"""
Store API — Customer-facing product browsing + cart-driven checkout.

Endpoints:
- GET /api/v1/store/products — list active products for a merchant
- POST /api/v1/store/checkout — run AP2 checkout from a frontend cart
"""
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ap2.mandates import create_intent_mandate, sign_cart_mandate
from app.agents.guardian import GuardianAgent, MoneyAction
from app.razorpay_client import RazorpayClient
from app.models import IntentMandate, CartMandate, CartItem, Product
from app.agents.tools import AgentTools

router = APIRouter(prefix="/api/v1/store", tags=["store"])


class StoreCheckoutRequest(BaseModel):
    merchant_id: str
    buyer_did: str
    product_ids: list[str] = Field(..., min_length=1)
    quantities: dict[str, int] = Field(default_factory=dict)
    buyer_private_key: str = Field(..., description="Buyer's PEM private key for signing the cart mandate")


@router.get("/products")
async def list_store_products(merchant_id: str):
    """List active products for the customer storefront."""
    products = await Product.find(
        Product.merchant_id == merchant_id,
        Product.is_active == True,
    ).to_list()
    return products


@router.post("/checkout")
async def store_checkout(req: StoreCheckoutRequest):
    """AP2 checkout driven by a frontend-managed cart.

    Flow:
    1. Lookup-or-create Intent Mandate for buyer + merchant
    2. Build CartItems from selected products
    3. Sign CartMandate with buyer's private key
    4. Guardian validation
    5. Create Razorpay order on approval
    6. Persist CartMandate + AuditLog
    """
    # Step 1: Lookup-or-create Intent Mandate
    intent_mandate = await IntentMandate.find_one(
        IntentMandate.merchant_id == req.merchant_id,
        IntentMandate.buyer_did == req.buyer_did,
    )
    if not intent_mandate:
        intent_mandate_doc = create_intent_mandate(
            buyer_did=req.buyer_did,
            agent_did="StoreAPI",
            merchant_id=req.merchant_id,
            max_amount_per_txn=500000,
            max_amount_daily=1000000,
            allowed_categories=["electronics", "books", "clothing"],
            merchant_dids=[req.merchant_id],
            duration_hours=48,
        )
        await intent_mandate_doc.create()
        intent_mandate_id = intent_mandate_doc.mandate_id
    else:
        intent_mandate_id = intent_mandate.mandate_id

    # Step 2: Build CartItems from selected products
    cart_items: list[CartItem] = []
    total_amount = 0
    categories: set[str] = set()

    for pid in req.product_ids:
        product = await Product.find_one(
            Product.product_id == pid,
            Product.merchant_id == req.merchant_id,
            Product.is_active == True,
        )
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {pid} not found")
        qty = req.quantities.get(pid, 1)
        line_total = product.base_price_paise * qty
        total_amount += line_total
        categories.add(product.category)
        cart_items.append(CartItem(
            product_id=pid,
            product_name=product.name,
            quantity=qty,
            unit_price_paise=product.base_price_paise,
            line_total_paise=line_total,
        ))

    if total_amount <= 0:
        raise HTTPException(status_code=400, detail="Cart total must be greater than 0")

    # Step 3: Sign Cart Mandate
    cart_mandate_id, buyer_signature = sign_cart_mandate(
        intent_mandate_id=intent_mandate_id,
        merchant_id=req.merchant_id,
        cart_items=cart_items,
        total_amount=total_amount,
        currency="INR",
        buyer_private_key_pem=req.buyer_private_key,
    )

    # Step 4: Guardian validation
    tools = AgentTools()
    guardian = GuardianAgent(tools)

    action = MoneyAction(
        action_type="CREATE_ORDER",
        amount=total_amount,
        currency="INR",
        merchant_id=req.merchant_id,
        buyer_id=req.buyer_did,
        mandate_id=intent_mandate_id,
        category=next(iter(categories)) if categories else "uncategorized",
        agent_id="StoreAPI",
        request_payload={"cart_items": [item.model_dump() for item in cart_items]},
    )

    intent_mandate_doc = await IntentMandate.get(intent_mandate_id)
    if not intent_mandate_doc:
        raise HTTPException(status_code=404, detail="Intent Mandate not found")

    guardian_result = await guardian.validate_action(action, intent_mandate_doc)

    if guardian_result["decision"] != "approved":
        return {
            "success": False,
            "checkout_session_id": f"checkout_{uuid4().hex[:8]}",
            "cart_mandate_id": cart_mandate_id,
            "intent_mandate_id": intent_mandate_id,
            "guardian_decision": guardian_result,
            "message": f"Purchase blocked by Guardian: {guardian_result['reason']}",
        }

    # Step 5: Log approval + Persist CartMandate
    await guardian.log_decision(action, guardian_result)

    nonce = f"nonce_{uuid4().hex[:16]}"
    expires_at = datetime.utcnow() + timedelta(days=7)

    cart_mandate = CartMandate(
        mandate_id=cart_mandate_id,
        intent_mandate_id=intent_mandate_id,
        merchant_id=req.merchant_id,
        buyer_did=req.buyer_did,
        cart_items=cart_items,
        total_amount=total_amount,
        currency="INR",
        buyer_signature=buyer_signature,
        status="signed_pending_payment",
        nonce=nonce,
        expires_at=expires_at,
    )
    await cart_mandate.create()

    # Step 6: Create Razorpay order
    razorpay = RazorpayClient()
    order = razorpay.create_order(
        amount=total_amount,
        currency="INR",
        receipt=cart_mandate_id,
        notes={
            "cart_mandate_id": cart_mandate_id,
            "merchant_id": req.merchant_id,
            "buyer_did": req.buyer_did,
        },
    )

    if order.get("error"):
        raise HTTPException(
            status_code=502,
            detail=f"Razorpay order creation failed: {order.get('detail')}",
        )

    return {
        "success": True,
        "checkout_session_id": f"checkout_{uuid4().hex[:8]}",
        "cart_mandate_id": cart_mandate_id,
        "intent_mandate_id": intent_mandate_id,
        "razorpay_order": order,
        "guardian_decision": guardian_result,
        "message": f"Checkout approved. Razorpay order {order.get('id', 'unknown')} created.",
    }
