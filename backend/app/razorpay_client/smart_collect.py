"""Smart Collect payout operations.

Uses the Razorpay payment transfer API to sweep collected funds
from a payment to a settlement account.
"""
from app.razorpay_client.client import RazorpayClient


def create_sweep_payment(
    client: RazorpayClient,
    payment_id: str,
    account_number: str,
    amount: int,
    currency: str = "INR",
    notes: dict | None = None,
) -> dict:
    """Initiate a transfer (sweep) from a collected payment to an account."""
    return client.create_sweep_payment(
        payment_id=payment_id,
        account_number=account_number,
        amount=amount,
        currency=currency,
        notes=notes,
    )
