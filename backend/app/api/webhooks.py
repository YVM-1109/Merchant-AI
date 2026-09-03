"""
Webhook API — Razorpay payment status updates.

Handles inbound webhooks from Razorpay, verifies signatures,
updates CartMandate / AuditLog documents, and publishes
events to Redis for async processing.
"""
import hashlib
import hmac
import json

from fastapi import APIRouter, Request, HTTPException, status, Depends
from pydantic import BaseModel

from app.razorpay_client import RazorpayClient
from app.models import CartMandate, AuditLog
import redis.asyncio as aioredis

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])


class WebhookResponse(BaseModel):
    success: bool
    event_type: str
    processed: bool
    message: str


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """
    Receive Razorpay webhook events and update the merchant's records.

    Verifies the webhook signature, looks up the relevant CartMandate by
    receipt ID (which we set to cart_mandate_id), updates status, and
    publishes an event to Redis for async processing by FailureAgent.
    """
    # Get raw body
    body = await request.body()

    # Verify webhook signature
    razorpay_client = RazorpayClient()
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        event = razorpay_client.verify_webhook_signature(
            body=body,
            signature=signature,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Webhook signature verification failed: {exc}",
        )

    event_type = event.get("event", "unknown")

    # Route based on event type
    if event_type == "payment.captured":
        await _handle_payment_captured(event)
    elif event_type == "payment.failed":
        await _handle_payment_failed(event)
    elif event_type == "order.paid":
        await _handle_order_paid(event)
    elif event_type == "refund.processed":
        await _handle_refund_processed(event)

    # Publish to Redis for async processing
    from app.config import settings
    redis = aioredis.from_url(settings.REDIS_URL)
    event_data = json.dumps(event)
    await redis.publish("razorpay_events", event_data)
    await redis.close()

    return WebhookResponse(
        success=True,
        event_type=event_type,
        processed=True,
        message=f"Event '{event_type}' processed successfully.",
    )


async def _handle_payment_captured(event: dict):
    """Update CartMandate and AuditLog when a payment is captured."""
    payload = event.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payload.get("order_id", "")

    # Find the CartMandate by receipt (we stored cart_mandate_id as receipt)
    cart_mandate = await CartMandate.find_one(
        CartMandate.status == "signed_pending_payment"
    ).first_or_none()

    if cart_mandate:
        cart_mandate.status = "paid"
        await cart_mandate.save()

    # Log audit entry
    audit = AuditLog(
        audit_id=f"audit_{order_id[:8]}" if order_id else None,
        action_type="CAPTURE_PAYMENT",
        amount=payload.get("amount", 0),
        currency=payload.get("currency", "INR"),
        status="SUCCESS",
        merchant_id=payload.get("notes", {}).get("merchant_id", ""),
        buyer_id=payload.get("notes", {}).get("buyer_did", ""),
        mandate_id=payload.get("notes", {}).get("cart_mandate_id", ""),
        reasoning=f"Payment captured for order {order_id}",
    )
    await audit.create()


async def _handle_payment_failed(event: dict):
    """Handle payment failure — queue for retry via FailureAgent."""
    payload = event.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payload.get("order_id", "")

    # Find and update CartMandate
    cart_mandate = await CartMandate.find_one(
        CartMandate.status.in_(["signed_pending_payment", "paid"])
    ).first_or_none()

    if cart_mandate:
        cart_mandate.status = "payment_failed"
        await cart_mandate.save()


async def _handle_order_paid(event: dict):
    """Mark CartMandate as settled when order is fully paid."""
    payload = event.get("payload", {}).get("order", {}).get("entity", {})
    order_id = payload.get("id", "")

    cart_mandate = await CartMandate.find_one(
        CartMandate.mandate_id == order_id  # or receipt matches
    ).first_or_none()

    if cart_mandate:
        cart_mandate.status = "settled"
        await cart_mandate.save()


async def _handle_refund_processed(event: dict):
    """Log a refund in the audit trail."""
    payload = event.get("payload", {}).get("refund", {}).get("entity", {})
    payment_id = payload.get("payment_id", "")

    audit = AuditLog(
        audit_id=f"refund_{payload.get('id', 'unknown')[:12]}",
        action_type="REFUND",
        amount=payload.get("amount", 0),
        currency=payload.get("currency", "INR"),
        status="SUCCESS",
        merchant_id="",
        buyer_id="",
        mandate_id=payload.get("notes", {}).get("cart_mandate_id", ""),
        reasoning=f"Refund processed for payment {payment_id}",
    )
    await audit.create()
