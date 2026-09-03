"""
Checkout API — AP2 cart-mandate-driven purchase flow.

POST /api/v1/checkout
    Presents an Intent Mandate to the buyer, creates a signed Cart Mandate,
    runs Guardian validation, and creates a Razorpay order.
"""
from datetime import datetime, timedelta
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field

from app.agents.graph import AgentGraph
from app.ap2.mandates import create_intent_mandate, sign_cart_mandate
from app.agents.guardian import GuardianAgent
from app.razorpay_client import RazorpayClient
from app.models import IntentMandate, CartMandate, CartItem
from app.agents.tools import AgentTools

router = APIRouter(prefix="/api/v1", tags=["checkout"])


class CheckoutRequest(BaseModel):
    merchant_id: str
    buyer_did: str
    product_ids: list[str] = Field(..., min_length=1)
    quantities: dict[str, int] = Field(default_factory=dict)
    buyer_private_key: str = Field(..., description="Buyer's PEM private key for signing the cart mandate")


class CheckoutResponse(BaseModel):
    success: bool
    checkout_session_id: str
    cart_mandate_id: str
    intent_mandate_id: str
    razorpay_order: dict | None = None
    guardian_decision: dict | None = None
    message: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(req: CheckoutRequest):
    """
    Full AP2 checkout flow:
    1. Create (or reuse) an Intent Mandate scoped to the merchant + buyer
    2. Build a Cart Mandate and sign it with the buyer's private key
    3. Run GuardianAgent validation against the Intent Mandate
    4. Create a Razorpay order on approval
    5. Return order details for front-end checkout
    """
    # Step 1: Create Intent Mandate
    intent_mandate = await IntentMandate.find_one(
        IntentMandate.merchant_id == req.merchant_id,
        IntentMandate.buyer_did == req.buyer_did,
    )
    if not intent_mandate:
        intent_mandate_id = await create_intent_mandate(
            merchant_id=req.merchant_id,
            buyer_did=req.buyer_did,
            max_amount_per_txn=500000,  # ₹5000 default
            daily_limit=1000000,  # ₹10000 daily default
            allowed_categories=["electronics", "books", "clothing"],
            merchant_whitelist=[req.merchant_id],
            expiry_hours=48,
        )
    else:
        intent_mandate_id = intent_mandate.mandate_id

    # Step 2: Build and sign the Cart Mandate
    # Fetch product details to compute totals
    from app.models import Product
    cart_items: list[CartItem] = []
    total_amount = 0

    for pid in req.product_ids:
        product = await Product.get(pid)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {pid} not found",
            )
        qty = req.quantities.get(pid, 1)
        line_total = product.base_price_paise * qty
        total_amount += line_total
        cart_items.append(CartItem(
            product_id=pid,
            product_name=product.name,
            quantity=qty,
            unit_price_paise=product.base_price_paise,
            line_total_paise=line_total,
        ))

    if total_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cart total must be greater than 0",
        )

    cart_mandate_id, buyer_signature = sign_cart_mandate(
        intent_mandate_id=intent_mandate_id,
        merchant_id=req.merchant_id,
        cart_items=cart_items,
        total_amount=total_amount,
        currency="INR",
        buyer_private_key_pem=req.buyer_private_key,
    )

    # Step 3: Guardian validation
    tools = AgentTools()
    guardian = GuardianAgent(tools)

    from app.agents.guardian import MoneyAction
    action = MoneyAction(
        action_type="CREATE_ORDER",
        amount=total_amount,
        currency="INR",
        merchant_id=req.merchant_id,
        buyer_id=req.buyer_did,
        mandate_id=intent_mandate_id,
        category=cart_items[0].product_name,
        agent_id="CheckoutAPI",
        request_payload={"cart_items": [item.model_dump() for item in cart_items]},
    )

    # Fetch the intent mandate for guardian validation
    intent_mandate_doc = await IntentMandate.get(intent_mandate_id)
    if not intent_mandate_doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Intent Mandate not found for Guardian validation",
        )

    guardian_result = await guardian.validate_action(action, intent_mandate_doc)

    if guardian_result["decision"] != "approved":
        return CheckoutResponse(
            success=False,
            checkout_session_id=f"checkout_{uuid4().hex[:8]}",
            cart_mandate_id=cart_mandate_id,
            intent_mandate_id=intent_mandate_id,
            guardian_decision=guardian_result,
            message=f"Purchase blocked by Guardian: {guardian_result['reason']}",
        )

    # Step 4: Log approval and create Razorpay order
    await guardian.log_decision(action, guardian_result)

    razorpay = RazorpayClient()
    order = razorpay.create_order(
        amount=total_amount,
        currency="INR",
        receipt=cart_mandate_id,
    )

    # Step 5: Save the Cart Mandate to the DB
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
    )
    await cart_mandate.create()

    return CheckoutResponse(
        success=True,
        checkout_session_id=f"checkout_{uuid4().hex[:8]}",
        cart_mandate_id=cart_mandate_id,
        intent_mandate_id=intent_mandate_id,
        razorpay_order=order,
        guardian_decision=guardian_result,
        message=f"✅ Checkout approved. Razorpay order {order.get('id', 'unknown')} created.",
    )
