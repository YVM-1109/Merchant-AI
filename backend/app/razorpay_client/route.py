"""Route convenience helpers for AP2-style money actions.

These functions encapsulate the multi-step Razorpay calls that an agent
would trigger during a checkout flow: create order → capture payment.
"""
from app.razorpay_client import orders as order_ops
from app.razorpay_client import payments as payment_ops
from app.razorpay_client.client import RazorpayClient


def create_order_and_capture(
    client: RazorpayClient,
    amount: int,
    currency: str = "INR",
    receipt: str = "",
    notes: dict | None = None,
) -> dict:
    """One-shot: create an order (auto-capture not always supported,
    so this returns the order dict; caller must capture the payment_id
    separately if needed).

    For test-mode 7xxx cards that are auto-captured, this still works —
    the payment will already be captured by Razorpay.
    """
    return order_ops.create_order(
        client=client,
        amount=amount,
        currency=currency,
        receipt=receipt,
        notes=notes,
    )
