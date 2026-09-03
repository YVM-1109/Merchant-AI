"""
Analytics Service — MongoDB aggregation pipelines for revenue,
mandate volume, Guardian intervention rates, and buyer behavior.

All methods return dictionaries ready for the API layer.
"""
from datetime import datetime, timedelta
from typing import Optional

from app.models import AuditLog, Merchant


class AnalyticsService:
    """Aggregation-based analytics via Mongo pipelines."""

    @staticmethod
    async def revenue_summary(merchant_id: str, days: int = 30) -> dict:
        """Total revenue, AOV, and order count for a merchant."""
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "status": "SUCCESS",
                    "timestamp": {"$gte": since},
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total_revenue": {"$sum": "$amount"},
                    "order_count": {"$sum": 1},
                    "avg_order_value": {"$avg": "$amount"},
                }
            },
        ]

        results = await AuditLog.aggregate(pipeline).to_list()
        if not results:
            return {"merchant_id": merchant_id, "total_revenue": 0, "order_count": 0, "aov": 0}

        r = results[0]
        return {
            "merchant_id": merchant_id,
            "period_days": days,
            "total_revenue_paise": r["total_revenue"],
            "order_count": r["order_count"],
            "avg_order_value_paise": int(r["avg_order_value"]),
        }

    @staticmethod
    async def guardian_intervention_rate(merchant_id: str, days: int = 30) -> dict:
        """Percentage of money actions that were approved vs denied."""
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "action_type": {"$regex": "CREATE_ORDER|REFUND"},
                    "timestamp": {"$gte": since},
                }
            },
            {
                "$group": {
                    "_id": "$status",
                    "count": {"$sum": 1},
                    "total_amount": {"$sum": "$amount"},
                }
            },
        ]

        results = await AuditLog.aggregate(pipeline).to_list()

        approved_count = sum(r["count"] for r in results if "SUCCESS" in r["_id"])
        denied_count = sum(r["count"] for r in results if "DENIED" in r["_id"])
        total = approved_count + denied_count

        return {
            "merchant_id": merchant_id,
            "period_days": days,
            "total_actions": total,
            "approved": approved_count,
            "denied": denied_count,
            "intervention_rate_pct": round((denied_count / total * 100), 2) if total > 0 else 0,
        }

    @staticmethod
    async def top_products_by_revenue(merchant_id: str, limit: int = 10) -> list[dict]:
        """Top-selling products by total revenue generated."""
        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "status": "SUCCESS",
                }
            },
            {
                "$group": {
                    "_id": "$mandate_id",  # cart_mandate_id maps to product
                    "revenue": {"$sum": "$amount"},
                    "order_count": {"$sum": 1},
                }
            },
            {"$sort": {"revenue": -1}},
            {"$limit": limit},
        ]

        return await AuditLog.aggregate(pipeline).to_list()

    @staticmethod
    async def daily_revenue_trend(merchant_id: str, days: int = 30) -> list[dict]:
        """Daily revenue trend for charting."""
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {
                "$match": {
                    "merchant_id": merchant_id,
                    "status": "SUCCESS",
                    "timestamp": {"$gte": since},
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                    },
                    "daily_revenue": {"$sum": "$amount"},
                    "daily_orders": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]

        results = await AuditLog.aggregate(pipeline).to_list()
        return [
            {
                "date": r["_id"],
                "revenue_paise": r["daily_revenue"],
                "orders": r["daily_orders"],
            }
            for r in results
        ]

    @staticmethod
    async def merchant_dashboard(merchant_id: str, days: int = 30) -> dict:
        """All key metrics for a merchant dashboard in one call."""
        revenue = await AnalyticsService.revenue_summary(merchant_id, days)
        guardian = await AnalyticsService.guardian_intervention_rate(merchant_id, days)
        trend = await AnalyticsService.daily_revenue_trend(merchant_id, days)

        return {
            "merchant_id": merchant_id,
            "period_days": days,
            "revenue": revenue,
            "guardian": guardian,
            "daily_trend": trend,
        }
