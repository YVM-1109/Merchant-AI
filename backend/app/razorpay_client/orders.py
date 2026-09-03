"""Order-level Razorpay operations."""
from app.razorpay_client.client import RazorpayClient


def create_order(client: RazorpayClient, amount: int, currency: str = "INR", receipt: str = "", notes: dict | None = None) -> dict:
    return client.create_order(amount=amount, currency=currency, receipt=receipt, notes=notes)


def fetch_order(client: RazorpayClient, order_id: str) -> dict:
    return client.fetch_order(order_id)


def fetch_payments_for_order(client: RazorpayClient, order_id: str) -> dict:
    return client.fetch_payments_for_order(order_id)
