"""Payment-level Razorpay operations."""
from app.razorpay_client.client import RazorpayClient


def fetch_payment(client: RazorpayClient, payment_id: str) -> dict:
    return client.fetch_payment(payment_id)


def capture_payment(client: RazorpayClient, payment_id: str, amount: int, currency: str = "INR") -> dict:
    return client.capture_payment(payment_id=payment_id, amount=amount, currency=currency)


def refund_payment(client: RazorpayClient, payment_id: str, amount: int | None = None) -> dict:
    return client.refund_payment(payment_id=payment_id, amount=amount)


def fetch_all_payments(client: RazorpayClient, **filters) -> dict:
    return client.fetch_all_payments(**filters)
