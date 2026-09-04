"""
Analytics API — aggregate endpoints powered by AnalyticsService.
"""
from fastapi import APIRouter, HTTPException
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/guardian-stats/{merchant_id}")
async def guardian_stats(merchant_id: str, days: int = 30):
    """Detailed Guardian decision stats with risk-score distribution."""
    return await AnalyticsService.guardian_detailed_stats(merchant_id, days)


@router.get("/dashboard/{merchant_id}")
async def get_dashboard(merchant_id: str, days: int = 30):
    """Full dashboard metrics for a merchant."""
    return await AnalyticsService.merchant_dashboard(merchant_id, days)


@router.get("/revenue/{merchant_id}")
async def get_revenue(merchant_id: str, days: int = 30):
    """Revenue summary for a merchant."""
    return await AnalyticsService.revenue_summary(merchant_id, days)


@router.get("/guardian-rate/{merchant_id}")
async def get_guardian_rate(merchant_id: str, days: int = 30):
    """Guardian intervention/approval rate."""
    return await AnalyticsService.guardian_intervention_rate(merchant_id, days)


@router.get("/top-products/{merchant_id}")
async def get_top_products(merchant_id: str, limit: int = 10):
    """Top products by revenue."""
    return await AnalyticsService.top_products_by_revenue(merchant_id, limit)


@router.get("/daily-trend/{merchant_id}")
async def get_daily_trend(merchant_id: str, days: int = 30):
    """Daily revenue trend for charting."""
    return await AnalyticsService.daily_revenue_trend(merchant_id, days)
