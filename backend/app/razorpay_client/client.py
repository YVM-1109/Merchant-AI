"""Facade around the official Razorpay Python SDK.

Wraps test-mode API calls with consistent error handling so every
downstream agent/service gets a uniform response shape.
"""
import razorpay
from razorpay.errors import BadRequestError, GatewayError, ServerError

from app.config import settings


class RazorpayClient:
    """Facade around the official Razorpay Python SDK.

    All 7+ APIs (Orders, Payments, Payment Links, Subscriptions, Refunds,
    Smart Collect transfers, Settlements) are proxied through this facade
    with consistent error handling.
    """

    def __init__(self):
        self._client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
        )

    # ── Health ──────────────────────────────────────────────────────

    def is_healthy(self) -> bool:
        """Ping the Razorpay API with a lightweight call."""
        try:
            # Validate the access token with a simple fetch
            self._client.settlement.all({"limit": 1})
            return True
        except (BadRequestError, GatewayError, ServerError) as exc:
            print(f"Razorpay health check failed: {exc}")
            return False

    # ── Orders ──────────────────────────────────────────────────────
    def _orders(self):
        return self._client.order

    def create_order(
        self,
        amount: int,
        currency: str = "INR",
        receipt: str = "",
        notes: dict | None = None,
    ) -> dict:
        """Create a Razorpay order. Amount is in paise."""
        payload = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }
        return self._safe("orders.create", self._orders().create, payload)

    def fetch_order(self, order_id: str) -> dict:
        return self._safe("orders.fetch", self._orders().fetch, order_id)

    def fetch_payments_for_order(self, order_id: str) -> dict:
        return self._safe(
            "orders.payments", self._orders().payments, order_id
        )

    # ── Payments ────────────────────────────────────────────────────
    def _payments(self):
        return self._client.payment

    def fetch_payment(self, payment_id: str) -> dict:
        return self._safe("payments.fetch", self._payments().fetch, payment_id)

    def capture_payment(self, payment_id: str, amount: int, currency: str = "INR") -> dict:
        """Capture an authorized payment."""
        payload = {"amount": amount, "currency": currency}
        return self._safe(
            "payments.capture", self._payments().capture, payment_id, payload
        )

    def refund_payment(self, payment_id: str, amount: int | None = None) -> dict:
        payload = {"amount": amount} if amount else {}
        return self._safe(
            "payments.refund", self._payments().refund, payment_id, payload
        )

    def fetch_all_payments(self, **filters) -> dict:
        return self._safe("payments.all", self._payments().all, filters)

    # ── Payment Links ───────────────────────────────────────────────

    def create_payment_link(
        self,
        amount: int,
        description: str,
        customer: dict | None = None,
        callback_url: str | None = None,
        notes: dict | None = None,
    ) -> dict:
        """Create a payment link."""
        payload = {
            "amount": amount,
            "currency": "INR",
            "description": description,
            "notes": notes or {},
        }
        if customer:
            payload["customer"] = customer
        if callback_url:
            payload["callback_url"] = callback_url
            payload["callback_method"] = "post"
        return self._safe(
            "links.create", self._client.payment_link.create, payload
        )

    def fetch_payment_link(self, link_id: str) -> dict:
        return self._safe("links.fetch", self._client.payment_link.fetch, link_id)

    # ── Subscriptions ───────────────────────────────────────────────

    def create_subscription(
        self,
        plan_id: str,
        customer_id: str,
        notes: dict | None = None,
    ) -> dict:
        payload = {
            "plan_id": plan_id,
            "customer_id": customer_id,
            "notes": notes or {},
        }
        return self._safe(
            "subscriptions.create", self._client.subscription.create, payload
        )

    def fetch_subscription(self, subscription_id: str) -> dict:
        return self._safe(
            "subscriptions.fetch", self._client.subscription.fetch, subscription_id
        )

    def cancel_subscription(
        self, subscription_id: str, cancel_at_cycle_end: bool = False
    ) -> dict:
        opts = {"cancel_at_cycle_end": 1 if cancel_at_cycle_end else 0}
        return self._safe(
            "subscriptions.cancel",
            self._client.subscription.cancel,
            subscription_id,
            opts,
        )

    # ── Smart Collect ──────────────────────────────────────────────
    # Smart Collect uses payment transfers (collect via virtual accounts,
    # then sweep to settlement account).
    def create_sweep_payment(
        self,
        payment_id: str,
        account_number: str,
        amount: int,
        currency: str = "INR",
        notes: dict | None = None,
    ) -> dict:
        """Initiate a transfer (sweep) from a collected payment."""
        payload = {
            "account_number": account_number,
            "amount": amount,
            "currency": currency,
            "notes": notes or {},
        }
        return self._safe(
            "transfers.create", self._payments().transfer, payment_id, payload
        )

    # ── Refunds ────────────────────────────────────────────────────

    def fetch_refund(self, refund_id: str) -> dict:
        return self._safe("refunds.fetch", self._client.refund.fetch, refund_id)

    # ── Settlements ────────────────────────────────────────────────

    def fetch_settlements(self, **filters) -> dict:
        return self._safe("settlements.all", self._client.settlement.all, filters)

    # ── Internal helper ────────────────────────────────────────────

    def _safe(self, label: str, fn, *args, **kwargs) -> dict:
        """Wrap every SDK call with consistent error handling."""
        try:
            return fn(*args, **kwargs)
        except BadRequestError as exc:
            print(f"[{label}] bad request: {exc}")
            return {"error": "bad_request", "detail": str(exc)}
        except GatewayError as exc:
            print(f"[{label}] gateway error: {exc}")
            return {"error": "gateway_error", "detail": str(exc)}
        except ServerError as exc:
            print(f"[{label}] server error: {exc}")
            return {"error": "server_error", "detail": str(exc)}
        except Exception as exc:
            print(f"[{label}] unexpected: {exc}")
            return {"error": "unexpected", "detail": str(exc)}
