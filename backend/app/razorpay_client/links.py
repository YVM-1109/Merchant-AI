"""Payment-link Razorpay operations."""
from app.razorpay_client.client import RazorpayClient


def create_payment_link(
    client: RazorpayClient,
    amount: int,
    description: str,
    customer: dict | None = None,
    callback_url: str | None = None,
    notes: dict | None = None,
) -> dict:
    return client.create_payment_link(
        amount=amount,
        description=description,
        customer=customer,
        callback_url=callback_url,
        notes=notes,
    )


def fetch_payment_link(client: RazorpayClient, link_id: str) -> dict:
    return client.fetch_payment_link(link_id)
