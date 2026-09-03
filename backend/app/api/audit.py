"""
Audit API — recent decisions and merchant summary.
"""
from fastapi import APIRouter, HTTPException, status

from app.agents.audit import AuditAgent

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("/recent/{merchant_id}")
async def get_recent_audit(merchant_id: str, limit: int = 50):
    """Get recent audit log entries for a merchant."""
    agent = AuditAgent()
    entries = await agent.get_recent_decisions(merchant_id, limit)
    return entries


@router.get("/summary/{merchant_id}")
async def get_audit_summary(merchant_id: str, days: int = 7):
    """Get aggregated audit summary for a merchant."""
    agent = AuditAgent()
    return await agent.get_merchant_summary(merchant_id, days)
