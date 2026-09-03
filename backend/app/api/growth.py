"""Growth Agent API — revenue optimization via campaigns and recovery."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.agents.growth import GrowthAgent
from app.agents.tools import AgentTools

router = APIRouter(prefix="/api/v1/growth")


class CampaignRequest(BaseModel):
    merchant_id: str
    campaign_type: str = "abandoned_cart"
    target_segment: str = "all"
    discount_percentage: float | None = None


@router.post("/campaigns")
async def create_campaign(req: CampaignRequest):
    """Trigger the GrowthAgent to generate a recovery/upsell campaign.

    Returns the created GrowthCampaign document.
    """
    tools = AgentTools()
    agent = GrowthAgent(tools)
    # Wrap string segment into a dict matching the GrowthCampaign schema
    segment = {"segment": req.target_segment}
    campaign = await agent.generate_recovery_campaign(
        merchant_id=req.merchant_id,
        target_segment=segment,
    )
    return {
        "status": "success",
        "campaign_id": campaign.campaign_id,
        "campaign_type": campaign.campaign_type,
        "link_count": len(campaign.generated_payment_links),
    }
