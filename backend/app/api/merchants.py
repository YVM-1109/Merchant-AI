from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models import Merchant

router = APIRouter(prefix="/api/v1/merchants", tags=["merchants"])


class MerchantCreate(BaseModel):
    razorpay_account_id: str
    business_name: str
    api_key_id: str
    api_key_secret_encrypted: str
    business_type: str
    agent_config: dict = Field(default_factory=dict)
    mcp_endpoint: str = ""


class MerchantRead(BaseModel):
    merchant_id: str
    razorpay_account_id: str
    business_name: str
    api_key_id: str
    business_type: str
    agent_config: dict = Field(default_factory=dict)
    mcp_endpoint: str = ""
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MerchantUpdate(BaseModel):
    business_name: Optional[str] = None
    business_type: Optional[str] = None
    agent_config: Optional[dict] = None
    mcp_endpoint: Optional[str] = None
    is_active: Optional[bool] = None


@router.post("/", response_model=MerchantRead, status_code=status.HTTP_201_CREATED)
async def create_merchant(payload: MerchantCreate):
    existing = await Merchant.find_one(Merchant.razorpay_account_id == payload.razorpay_account_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Merchant with this Razorpay account ID already exists.",
        )
    merchant = Merchant(**payload.model_dump())
    await merchant.create()
    return MerchantRead.model_validate(merchant)


@router.get("/", response_model=List[MerchantRead])
async def list_merchants(skip: int = 0, limit: int = 100):
    merchants = await Merchant.all().skip(skip).limit(limit).to_list()
    return [MerchantRead.model_validate(m) for m in merchants]


@router.get("/{merchant_id}", response_model=MerchantRead)
async def get_merchant(merchant_id: str):
    merchant = await Merchant.find_one(Merchant.merchant_id == merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    return MerchantRead.model_validate(merchant)


@router.patch("/{merchant_id}", response_model=MerchantRead)
async def update_merchant(merchant_id: str, payload: MerchantUpdate):
    merchant = await Merchant.find_one(Merchant.merchant_id == merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(merchant, field, value)
    merchant.updated_at = datetime.utcnow()
    await merchant.save()
    return MerchantRead.model_validate(merchant)


@router.delete("/{merchant_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_merchant(merchant_id: str):
    merchant = await Merchant.find_one(Merchant.merchant_id == merchant_id)
    if not merchant:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant not found")
    await merchant.delete()
    return None
