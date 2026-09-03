from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.models import Product

router = APIRouter(prefix="/api/v1/products", tags=["products"])


class ProductVariantCreate(BaseModel):
    sku: str
    price_paise: int
    stock_quantity: int
    attributes: dict = Field(default_factory=dict)


class ProductCreate(BaseModel):
    merchant_id: str
    razorpay_order_id: Optional[str] = None
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    base_price_paise: int
    currency: str = "INR"
    variants: List[ProductVariantCreate] = Field(default_factory=list)
    total_stock: int = 0
    agent_readable: dict = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    is_active: bool = True


class ProductRead(BaseModel):
    product_id: str
    merchant_id: str
    razorpay_order_id: Optional[str] = None
    name: str
    description: str
    category: str
    tags: List[str] = Field(default_factory=list)
    base_price_paise: int
    currency: str = "INR"
    variants: list = Field(default_factory=list)
    total_stock: int = 0
    agent_readable: dict = Field(default_factory=dict)
    images: List[str] = Field(default_factory=list)
    is_active: bool = True
    sales_velocity: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    base_price_paise: Optional[int] = None
    variants: Optional[List[ProductVariantCreate]] = None
    total_stock: Optional[int] = None
    agent_readable: Optional[dict] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(payload: ProductCreate):
    product = Product(**payload.model_dump())
    await product.create()
    return ProductRead.model_validate(product)


@router.get("/", response_model=List[ProductRead])
async def list_products(
    skip: int = 0,
    limit: int = 100,
    merchant_id: Optional[str] = None,
    category: Optional[str] = None,
):
    query = Product.all()
    if merchant_id:
        query = query.find(Product.merchant_id == merchant_id)
    if category:
        query = query.find(Product.category == category)
    products = await query.skip(skip).limit(limit).to_list()
    return [ProductRead.model_validate(p) for p in products]


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: str):
    product = await Product.find_one(Product.product_id == product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return ProductRead.model_validate(product)


@router.patch("/{product_id}", response_model=ProductRead)
async def update_product(product_id: str, payload: ProductUpdate):
    product = await Product.find_one(Product.product_id == product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")

    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    product.updated_at = datetime.utcnow()
    await product.save()
    return ProductRead.model_validate(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: str):
    product = await Product.find_one(Product.product_id == product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    await product.delete()
    return None
