"""
Guardian Agent — Bounds-Checking & Audit Layer

Validates money actions against active Intent Mandates:
- Checks daily spend limits via MongoDB aggregation
- Validates category and merchant whitelist constraints
- Runs fraud heuristics (velocity scoring)
- Creates immutable AuditLog entries with HMAC signatures + chain

Every money action flowing from BuyerAgent or GrowthAgent passes
through GuardianAgent before execution.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.ap2.crypto import AP2Crypto
from app.models import IntentMandate, AuditLog
from app.razorpay_client import RazorpayClient


class GuardianDecision:
    """Result of a Guardian validation check."""

    APPROVED = "approved"
    DENIED = "denied"
    ESCALATED = "escalated"  # needs human review


class MoneyAction:
    """Represents a money operation to be validated by the Guardian."""

    def __init__(
        self,
        action_type: str,
        amount: int,
        currency: str,
        merchant_id: str,
        buyer_id: Optional[str] = None,
        mandate_id: Optional[str] = None,
        category: Optional[str] = None,
        razorpay_order_id: Optional[str] = None,
        agent_id: str = "GuardianAgent",
        request_payload: Optional[dict] = None,
    ):
        self.action_type = action_type
        self.amount = amount
        self.currency = currency
        self.merchant_id = merchant_id
        self.buyer_id = buyer_id
        self.mandate_id = mandate_id
        self.category = category
        self.razorpay_order_id = razorpay_order_id
        self.agent_id = agent_id
        self.request_payload = request_payload or {}


class GuardianAgent:
    """Validates money actions against Intent Mandates and logs decisions."""

    # Velocity threshold: flag if > 5 txn/day from same buyer
    VELOCITY_THRESHOLD_DAILY = 5

    def __init__(self, razorpay_client: Optional[RazorpayClient] = None):
        self.razorpay = razorpay_client or RazorpayClient()

    async def validate_action(self, action: MoneyAction, mandate: IntentMandate) -> dict:
        """Run full validation pipeline on a money action.

        Returns a decision dict with:
            - decision: "approved" | "denied" | "escalated"
            - reason: human-readable explanation
            - risk_score: 0.0 - 1.0
        """
        now = datetime.utcnow()
        reasons = []
        risk_score = 0.0

        # ── 1. Check mandate expiry ──────────────────────────────────
        if mandate.expires_at < now:
            reasons.append("Mandate has expired")
            risk_score += 0.5
        elif mandate.expires_at < now + timedelta(minutes=5):
            reasons.append("Mandate expires soon (<5 min remaining)")
            risk_score += 0.1

        # ── 2. Check mandate status ──────────────────────────────────
        if mandate.status != "active":
            reasons.append(f"Mandate status is '{mandate.status}', not 'active'")
            risk_score += 0.5

        # ── 3. Check per-transaction amount limit ───────────────────
        if action.amount > mandate.scope.max_amount_per_txn:
            reasons.append(
                f"Amount {action.amount} exceeds per-txn limit {mandate.scope.max_amount_per_txn}"
            )
            risk_score += 0.4

        # ── 4. Check daily spend limit ────────────────────────────────
        daily_spent = await self._calculate_daily_spend(
            buyer_did=mandate.buyer_did,
            merchant_id=action.merchant_id,
        )
        remaining_daily = mandate.scope.max_amount_daily - daily_spent
        if action.amount > remaining_daily:
            reasons.append(
                f"Amount {action.amount} exceeds remaining daily budget {remaining_daily}"
            )
            risk_score += 0.4

        # ── 5. Check allowed categories ───────────────────────────────
        if action.category and action.category not in mandate.scope.allowed_categories:
            reasons.append(f"Category '{action.category}' not in allowed list")
            risk_score += 0.3

        # ── 6. Check merchant DID whitelist ──────────────────────────
        # In AP2, merchant IDs can encode DIDs. For now, check merchant_id.
        if mandate.scope.merchant_dids:
            if action.merchant_id not in mandate.scope.merchant_dids:
                reasons.append("Merchant not in whitelist")
                risk_score += 0.3

        # ── 7. Check time window ──────────────────────────────────────
        tw_start = mandate.scope.time_window_start
        tw_end = mandate.scope.time_window_end
        if now < tw_start:
            reasons.append("Time window not yet open")
            risk_score += 0.2
        if now > tw_end:
            reasons.append("Time window has closed")
            risk_score += 0.3

        # ── 8. Velocity heuristic ─────────────────────────────────────
        txn_count_today = await self._count_today_transactions(
            buyer_did=mandate.buyer_did,
            merchant_id=action.merchant_id,
        )
        if txn_count_today > self.VELOCITY_THRESHOLD_DAILY:
            reasons.append(f"High velocity: {txn_count_today} transactions today")
            risk_score += 0.3

        # ── Decision ──────────────────────────────────────────────────
        if risk_score >= 0.5:
            decision = GuardianDecision.DENIED
        elif risk_score >= 0.3:
            decision = GuardianDecision.ESCALATED
        else:
            decision = GuardianDecision.APPROVED

        if not reasons and decision != GuardianDecision.APPROVED:
            reasons.append("Risk score exceeded threshold")

        return {
            "decision": decision,
            "reason": ". ".join(reasons) if reasons else "All checks passed",
            "risk_score": round(risk_score, 3),
            "daily_spent": daily_spent,
            "txn_count_today": txn_count_today,
        }

    async def log_decision(
        self,
        action: MoneyAction,
        decision_result: dict,
    ) -> AuditLog:
        """Create an immutable AuditLog entry with HMAC chain.

        Each entry's hmac_signature covers the previous entry's hash,
        creating a blockchain-style tamper-evident chain.
        """
        now = datetime.utcnow()

        # Find the previous audit entry for this buyer/merchant
        previous = await AuditLog.find(
            AuditLog.merchant_id == action.merchant_id,
            AuditLog.buyer_id == action.buyer_id,
        ).sort(-AuditLog.timestamp).first_or_none()

        previous_hash = previous.hmac_signature if previous else None

        # Build the data to sign
        audit_data = {
            "audit_id": f"aud_{now.strftime('%Y%m%d%H%M%S%f')}",
            "timestamp": now.isoformat() + "Z",
            "action_type": action.action_type,
            "actor": action.agent_id,
            "buyer_id": action.buyer_id,
            "merchant_id": action.merchant_id,
            "amount": action.amount,
            "currency": action.currency,
            "mandate_id": action.mandate_id,
            "decision": decision_result["decision"],
            "risk_score": decision_result["risk_score"],
            "reason": decision_result["reason"],
            "request_payload": action.request_payload,
            "previous_audit_hash": previous_hash,
        }

        # HMAC signature over the audit data
        hmac_sig = self._compute_hmac(audit_data)

        audit_entry = AuditLog(
            audit_id=audit_data["audit_id"],
            timestamp=now,
            action_type=action.action_type,
            actor=action.agent_id,
            buyer_id=action.buyer_id,
            merchant_id=action.merchant_id,
            razorpay_order_id=action.razorpay_order_id,
            amount=action.amount,
            currency=action.currency,
            mandate_id=action.mandate_id,
            guardian_decision=decision_result,
            reasoning=decision_result["reason"],
            request_payload=action.request_payload,
            response_payload={"decision": decision_result["decision"]},
            status=decision_result["decision"].upper() if decision_result["decision"] != "escalated" else "PENDING",
            hmac_signature=hmac_sig,
            previous_audit_hash=previous_hash,
        )
        await audit_entry.create()
        return audit_entry

    # ── Internal helpers ────────────────────────────────────────────

    async def _calculate_daily_spend(self, buyer_did: str, merchant_id: str) -> int:
        """Sum all successful transactions for a buyer today (via aggregation)."""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        pipeline = [
            {
                "$match": {
                    "buyer_id": buyer_did,
                    "merchant_id": merchant_id,
                    "status": "SUCCESS",
                    "timestamp": {"$gte": start_of_day},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"},
                }
            },
        ]

        result = await AuditLog.aggregate(pipeline).to_list()
        if result:
            return result[0].get("total", 0)
        return 0

    async def _count_today_transactions(self, buyer_did: str, merchant_id: str) -> int:
        """Count transactions for a buyer today."""
        now = datetime.utcnow()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        count = await AuditLog.find(
            AuditLog.buyer_id == buyer_did,
            AuditLog.merchant_id == merchant_id,
            AuditLog.timestamp >= start_of_day,
        ).count()
        return count

    @staticmethod
    def _compute_hmac(data: dict) -> str:
        """Compute HMAC-SHA256 over the canonical JSON of the data."""
        import hashlib
        import hmac
        import json

        # Canonicalize: sort keys, no whitespace
        canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
        secret = b"guardian-hmac-secret"  # In production, use settings.JWT_SECRET
        signature = hmac.new(secret, canonical.encode("utf-8"), hashlib.sha256).hexdigest()
        return signature
