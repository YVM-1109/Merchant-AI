"""
AuditAgent — Reads and queries the audit trail.

Provides aggregation-based reporting on money actions,
decision patterns, and guardian intervention rates.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.models import AuditLog


class AuditAgent:
    """Read-only audit trail querier."""

    async def get_audit_log(self, audit_id: str) -> Optional[dict]:
        """Fetch a single audit log entry by ID."""
        entry = await AuditLog.find_one(AuditLog.audit_id == audit_id)
        if not entry:
            return None
        return entry.model_dump()

    async def get_merchant_summary(self, merchant_id: str, days: int = 7) -> dict:
        """Aggregate audit log for a merchant over N days."""
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "timestamp": {"$gte": since},
                }
            },
            {
                "$group": {
                    "_id": "$action_type",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                    "approved": {
                        "$sum": {"$cond": [{"$eq": ["$status", "SUCCESS"]}, 1, 0]}
                    },
                    "denied": {
                        "$sum": {"$cond": [{"$eq": ["$status", "DENIED"]}, 1, 0]}
                    },
                }
            },
            {"$sort": {"count": -1}},
        ]

        results = await AuditLog.aggregate(pipeline).to_list()

        total_actions = sum(r["count"] for r in results)
        total_approved = sum(r["approved"] for r in results)
        total_denied = sum(r["denied"] for r in results)

        return {
            "merchant_id": merchant_id,
            "period_days": days,
            "total_actions": total_actions,
            "approved": total_approved,
            "denied": total_denied,
            "by_action_type": results,
        }

    async def get_recent_decisions(self, merchant_id: str, limit: int = 20) -> list[dict]:
        """Get recent audit entries for a merchant."""
        entries = await AuditLog.find(
            AuditLog.merchant_id == merchant_id,
        ).sort(-AuditLog.timestamp).limit(limit).to_list()

        return [
            {
                "audit_id": e.audit_id,
                "action_type": e.action_type,
                "amount": e.amount,
                "status": e.status,
                "reasoning": e.reasoning,
                "timestamp": e.timestamp.isoformat(),
            }
            for e in entries
        ]
