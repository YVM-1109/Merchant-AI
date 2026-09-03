"""Subscription Razorpay operations."""
from app.razorpay_client.client import RazorpayClient


def create_subscription(client: RazorpayClient, plan_id: str, customer_id: str, notes: dict | None = None) -> dict:
    return client.create_subscription(plan_id=plan_id, customer_id=customer_id, notes=notes)


def fetch_subscription(client: RazorpayClient, subscription_id: str) -> dict:
    return client.fetch_subscription(subscription_id)


def cancel_subscription(client: RazorpayClient, subscription_id: str, cancel_at_cycle_end: bool = False) -> dict:
    return client.cancel_subscription(subscription_id=subscription_id, cancel_at_cycle_end=cancel_at_cycle_end)
