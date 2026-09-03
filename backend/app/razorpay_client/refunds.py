"""Refund lookup operations."""
from app.razorpay_client.client import RazorpayClient


def fetch_refund(client: RazorpayClient, refund_id: str) -> dict:
    return client.fetch_refund(refund_id)
