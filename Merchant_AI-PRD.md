
# PRD: MERCHANT-AI — Agentic Commerce Operating System for Razorpay
## Track 1: AI Growth & Agentic Commerce | Razorpay AI Buildathon 2026
### *MongoDB Edition*

---

## 1. EXECUTIVE SUMMARY

**Project Name:** MERCHANT-AI (Merchant Agent Intelligence)  
**Tagline:** *"The First AP2-Ready Agentic Commerce Platform for Razorpay Merchants"*  
**Core Thesis:** Build a dual-sided platform where (a) Razorpay merchants get an AI Growth Co-pilot that analyzes transaction data and auto-generates revenue-optimizing campaigns, and (b) their storefront becomes instantly transactable by external AI buyers through a protocol-compliant agent interface implementing AP2-style mandates, ACP-inspired checkout, and x402 settlement simulation — all operating on Razorpay test-mode APIs with explainable, bounded, and audited money actions.

**Why This Wins:**
- **Protocol-Forward:** Implements emerging standards (AP2, ACP, x402, MCP, UCP) that Razorpay's product team is actively exploring
- **API-Deep:** Uses 7+ Razorpay test-mode APIs demonstrating platform mastery
- **Agent-Native:** Multi-agent architecture with LangGraph, not a chatbot wrapper
- **Document-First:** MongoDB's flexible schema perfectly models nested mandates, audit chains, and agent reasoning
- **Audit-First:** Every money action is cryptographically logged, bounded by guardrails, and explainable
- **Demo-Complete:** Working AI buyer agent completing real test-mode transactions end-to-end

---

## 2. TECH STACK (Updated)

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Backend API** | Python 3.11 + FastAPI | Modern async, auto-generated OpenAPI docs, Razorpay SDK native |
| **AI Orchestration** | LangGraph + LangChain | State-machine agents with memory, tool-calling, multi-agent graphs |
| **LLM Models** | OpenAI GPT-4o (primary) + Anthropic Claude 3.5 Sonnet (fallback) | Best reasoning + tool use; dual-model shows sophistication |
| **Database** | **MongoDB 7.0 + Motor (async driver)** | Document-native for mandates, audit trails, agent state; flexible schema evolution |
| **ODM** | **Beanie** (async ODM for MongoDB) | Pydantic-native, type-safe, async-first, built on Motor |
| **Cache/Queue** | Redis | Session state, mandate TTL, webhook buffering, agent state snapshots |
| **Frontend** | Next.js 14 (App Router) + TypeScript | Modern React, SSR for SEO, excellent DX |
| **UI Components** | shadcn/ui + Tailwind CSS | Beautiful, accessible, fast to build |
| **Charts** | Recharts + Tremor | Financial dashboards |
| **Razorpay SDK** | Official `razorpay` Python package | Native integration |
| **Protocol Layer** | Custom JSON-LD + JWS signatures | AP2 mandate implementation |
| **DevOps** | Docker + Docker Compose | One-command local setup |
| **Testing** | pytest (backend) + Playwright (E2E) | Professional test coverage |

---

## 3. DATABASE DESIGN (MongoDB)

### 3.1 Why MongoDB for This Project

| Use Case | MongoDB Advantage |
|----------|----------------|
| **AP2 Mandates** | Nested JSON-LD documents with embedded signature chains; no JOINs needed |
| **Audit Logs** | Append-only document collection with rich nested metadata; easy time-series queries |
| **Agent Reasoning** | Store LangGraph state snapshots as documents; flexible schema for evolving agent steps |
| **Product Catalogs** | Variable product attributes (different merchants have different fields) |
| **Campaign Data** | Embedded arrays of payment links, conversion events, and targeting rules |
| **Real-Time Dashboard** | Change Streams for live updates; aggregation pipelines for analytics |

### 3.2 Collections Schema

```python
# backend/models/merchant.py
from beanie import Document, Indexed
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List
from uuid import uuid4

class Merchant(Document):
    """Core merchant profile linked to Razorpay account"""
    merchant_id: str = Field(default_factory=lambda: f"merch_{uuid4().hex[:12]}")
    razorpay_account_id: Indexed(str, unique=True)
    business_name: str
    api_key_id: str
    api_key_secret_encrypted: str  # AES-256 encrypted
    business_type: str  # ecommerce, saas, b2b, etc.
    agent_config: dict = Field(default_factory=dict)  # Guardian thresholds
    mcp_endpoint: str = Field(default="")
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "merchants"
        indexes = [
            "razorpay_account_id",
            "business_type",
            "created_at"
        ]

# backend/models/product.py
class ProductVariant(BaseModel):
    sku: str
    price_paise: int
    stock_quantity: int
    attributes: dict = Field(default_factory=dict)  # color, size, etc.

class Product(Document):
    """Agent-readable product catalog with MCP-compatible metadata"""
    product_id: str = Field(default_factory=lambda: f"prod_{uuid4().hex[:12]}")
    merchant_id: Indexed(str)
    razorpay_order_id: Optional[str] = None
    name: str
    description: str
    category: Indexed(str)
    tags: List[str] = Field(default_factory=list)
    base_price_paise: int
    currency: str = "INR"
    variants: List[ProductVariant] = Field(default_factory=list)
    total_stock: int = 0
    agent_readable: dict = Field(default_factory=dict)  # UCP-style JSON-LD
    images: List[str] = Field(default_factory=list)
    is_active: bool = True
    sales_velocity: float = 0.0  # Calculated field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "products"
        indexes = [
            "merchant_id",
            "category",
            "tags",
            "is_active",
            [("merchant_id", 1), ("category", 1), ("is_active", 1)]
        ]

# backend/models/mandate.py
class MandateScope(BaseModel):
    max_amount_per_txn: int  # in paise
    max_amount_daily: int
    allowed_categories: List[str]
    merchant_dids: List[str]
    time_window_start: datetime
    time_window_end: datetime

class IntentMandate(Document):
    """AP2-style Intent Mandate stored as a rich document"""
    mandate_id: Indexed(str, unique=True)
    buyer_did: Indexed(str)
    agent_did: Indexed(str)
    merchant_id: Indexed(str)
    scope: MandateScope
    buyer_public_key: str
    mandate_signature: str  # JWS
    status: str = "active"  # active, revoked, expired, consumed
    revoked_at: Optional[datetime] = None
    revoke_reason: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime
    
    class Settings:
        name = "intent_mandates"
        indexes = [
            "mandate_id",
            "buyer_did",
            "agent_did",
            "merchant_id",
            "status",
            "expires_at",
            [("buyer_did", 1), ("status", 1), ("expires_at", 1)]
        ]

class CartItem(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price_paise: int
    line_total_paise: int

class CartMandate(Document):
    """AP2 Cart Mandate with embedded items and signatures"""
    mandate_id: Indexed(str, unique=True)
    intent_mandate_id: Indexed(str)
    intent_mandate_ref: Optional[IntentMandate] = None  # DBRef pattern via beanie
    merchant_id: Indexed(str)
    cart_items: List[CartItem]
    total_amount: int
    currency: str = "INR"
    buyer_signature: str
    nonce: str
    guardian_decision: Optional[dict] = None  # Embedded decision
    status: str = "pending"  # pending, approved, denied, executed, expired
    razorpay_order_id: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime  # 15-minute TTL
    
    class Settings:
        name = "cart_mandates"
        indexes = [
            "mandate_id",
            "intent_mandate_id",
            "merchant_id",
            "status",
            "expires_at",
            [("intent_mandate_id", 1), ("status", 1)]
        ]

# backend/models/transaction.py
class RazorpayOrder(Document):
    """Razorpay order document with embedded payment attempts"""
    razorpay_order_id: Indexed(str, unique=True)
    merchant_id: Indexed(str)
    amount: int
    currency: str = "INR"
    status: str = "created"  # created, attempted, paid, failed
    receipt: str
    notes: dict = Field(default_factory=dict)
    cart_mandate_id: Optional[str] = None
    payment_attempts: List[dict] = Field(default_factory=list)  # Embedded history
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "razorpay_orders"
        indexes = [
            "razorpay_order_id",
            "merchant_id",
            "status",
            "cart_mandate_id",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)]
        ]

class RazorpayPayment(Document):
    """Individual payment with full Razorpay response embedded"""
    razorpay_payment_id: Indexed(str, unique=True)
    order_id: Indexed(str)  # References razorpay_orders.razorpay_order_id
    merchant_id: Indexed(str)
    amount: int
    status: str  # created, authorized, captured, refunded, failed
    method: Optional[str] = None  # upi, card, netbanking, etc.
    email: Optional[str] = None
    contact: Optional[str] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    error_reason: Optional[str] = None
    captured: bool = False
    captured_at: Optional[datetime] = None
    fee: Optional[int] = None
    tax: Optional[int] = None
    raw_response: dict = Field(default_factory=dict)  # Full Razorpay payload
    refund_ids: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "razorpay_payments"
        indexes = [
            "razorpay_payment_id",
            "order_id",
            "merchant_id",
            "status",
            "method",
            "captured",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)]
        ]

# backend/models/audit.py
class AuditLog(Document):
    """
    Immutable audit trail for every money action.
    Embedded reasoning, guardian decision, and full request/response.
    """
    audit_id: str = Field(default_factory=lambda: f"aud_{uuid4().hex[:16]}")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    action_type: Indexed(str)  # CREATE_ORDER, CAPTURE_PAYMENT, REFUND, etc.
    actor: str  # GrowthAgent, BuyerAgent, GuardianAgent, Manual
    agent_id: Optional[str] = None
    buyer_id: Optional[str] = None
    merchant_id: Indexed(str)
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    amount: Optional[int] = None
    currency: Optional[str] = None
    mandate_id: Optional[str] = None
    
    # Embedded rich documents
    guardian_decision: dict = Field(default_factory=dict)
    reasoning: str = ""  # LLM-generated explanation
    request_payload: dict = Field(default_factory=dict)
    response_payload: dict = Field(default_factory=dict)
    status: str  # SUCCESS, FAILED, DENIED
    error_details: Optional[dict] = None
    
    # Tamper evidence
    hmac_signature: str
    previous_audit_hash: Optional[str] = None  # Blockchain-style chain
    
    class Settings:
        name = "audit_logs"
        indexes = [
            "audit_id",
            "action_type",
            "merchant_id",
            "razorpay_order_id",
            "razorpay_payment_id",
            "mandate_id",
            "status",
            [("merchant_id", 1), ("action_type", 1), ("timestamp", -1)],
            [("timestamp", -1)]  # Time-series queries
        ]

# backend/models/campaign.py
class PaymentLinkRef(BaseModel):
    link_id: str
    razorpay_link_id: str
    amount: int
    status: str
    payments_count: int = 0
    created_at: datetime

class GrowthCampaign(Document):
    """AI-generated campaign with embedded payment links and metrics"""
    campaign_id: str = Field(default_factory=lambda: f"camp_{uuid4().hex[:12]}")
    merchant_id: Indexed(str)
    campaign_type: str  # abandoned_cart, upsell, cross_sell, pricing, smart_collect
    target_segment: dict = Field(default_factory=dict)  # Embedded rules
    generated_payment_links: List[PaymentLinkRef] = Field(default_factory=list)
    conversion_rate: float = 0.0
    revenue_generated: int = 0
    status: str = "draft"  # draft, active, paused, completed
    ai_reasoning: str = ""  # Why the AI suggested this campaign
    executed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "growth_campaigns"
        indexes = [
            "campaign_id",
            "merchant_id",
            "campaign_type",
            "status",
            [("merchant_id", 1), ("status", 1), ("created_at", -1)]
        ]

# backend/models/agent_state.py
class AgentStateSnapshot(Document):
    """
    LangGraph state snapshots for debugging and resumability.
    MongoDB's flexible schema handles varying state shapes per agent.
    """
    session_id: Indexed(str)
    agent_type: str  # growth, buyer, guardian, catalog
    merchant_id: Optional[str] = None
    state_data: dict  # Flexible LangGraph state
    checkpoint_type: str  # start, step, end, error
    step_number: int
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "agent_state_snapshots"
        indexes = [
            "session_id",
            "agent_type",
            "checkpoint_type",
            [("session_id", 1), ("step_number", 1)]
        ]
```

### 3.3 MongoDB Configuration & Best Practices

```python
# backend/database.py
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from backend.config import settings
from backend.models import (
    Merchant, Product, IntentMandate, CartMandate,
    RazorpayOrder, RazorpayPayment, AuditLog,
    GrowthCampaign, AgentStateSnapshot
)

class MongoDB:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect(cls):
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            retryWrites=True,
            w="majority"
        )
        
        # Initialize Beanie ODM
        await init_beanie(
            database=cls.client[settings.MONGODB_DB_NAME],
            document_models=[
                Merchant, Product, IntentMandate, CartMandate,
                RazorpayOrder, RazorpayPayment, AuditLog,
                GrowthCampaign, AgentStateSnapshot
            ]
        )
        
        # Create TTL indexes for ephemeral data
        await cls.client[settings.MONGODB_DB_NAME].cart_mandates.create_index(
            "expires_at", expireAfterSeconds=0
        )
        await cls.client[settings.MONGODB_DB_NAME].agent_state_snapshots.create_index(
            "created_at", expireAfterSeconds=86400  # 24h retention
        )
    
    @classmethod
    async def disconnect(cls):
        if cls.client:
            cls.client.close()

# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "merchant_ai"
    REDIS_URL: str = "redis://localhost:6379"
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    JWT_SECRET: str
    ENCRYPTION_KEY: str  # For API key secrets
    
    class Config:
        env_file = ".env"

settings = Settings()
```

### 3.4 MongoDB Aggregation Pipelines (Analytics)

```python
# backend/services/analytics.py
from beanie import PydanticObjectId
from backend.models import RazorpayPayment, GrowthCampaign

class AnalyticsService:
    """MongoDB aggregation pipelines for dashboard metrics"""
    
    @staticmethod
    async def get_revenue_metrics(merchant_id: str, days: int = 30):
        """Aggregate revenue, transaction count, avg order value"""
        pipeline = [
            {"$match": {
                "merchant_id": merchant_id,
                "status": "captured",
                "created_at": {"$gte": datetime.utcnow() - timedelta(days=days)}
            }},
            {"$group": {
                "_id": None,
                "total_revenue": {"$sum": "$amount"},
                "transaction_count": {"$sum": 1},
                "avg_order_value": {"$avg": "$amount"},
                "max_transaction": {"$max": "$amount"}
            }},
            {"$project": {
                "_id": 0,
                "total_revenue": 1,
                "transaction_count": 1,
                "avg_order_value": {"$round": ["$avg_order_value", 2]},
                "max_transaction": 1
            }}
        ]
        result = await RazorpayPayment.aggregate(pipeline).to_list(1)
        return result[0] if result else {}
    
    @staticmethod
    async def get_abandoned_carts(merchant_id: str):
        """Find orders with payment attempts but no capture"""
        pipeline = [
            {"$match": {
                "merchant_id": merchant_id,
                "status": {"$in": ["created", "attempted"]},
                "created_at": {"$lte": datetime.utcnow() - timedelta(hours=1)}
            }},
            {"$lookup": {
                "from": "razorpay_payments",
                "localField": "razorpay_order_id",
                "foreignField": "order_id",
                "as": "payments"
            }},
            {"$match": {
                "payments.status": {"$ne": "captured"}
            }},
            {"$project": {
                "razorpay_order_id": 1,
                "amount": 1,
                "created_at": 1,
                "payment_attempts": {"$size": "$payments"}
            }}
        ]
        return await RazorpayOrder.aggregate(pipeline).to_list(100)
    
    @staticmethod
    async def get_agent_activity_timeline(merchant_id: str, limit: int = 50):
        """Recent audit log entries with embedded decisions"""
        pipeline = [
            {"$match": {"merchant_id": merchant_id}},
            {"$sort": {"timestamp": -1}},
            {"$limit": limit},
            {"$lookup": {
                "from": "intent_mandates",
                "localField": "mandate_id",
                "foreignField": "mandate_id",
                "as": "mandate"
            }},
            {"$unwind": {"path": "$mandate", "preserveNullAndEmptyArrays": True}},
            {"$project": {
                "audit_id": 1,
                "timestamp": 1,
                "action_type": 1,
                "actor": 1,
                "amount": 1,
                "status": 1,
                "reasoning": 1,
                "guardian_decision": 1,
                "mandate_scope": "$mandate.scope"
            }}
        ]
        return await AuditLog.aggregate(pipeline).to_list(limit)
    
    @staticmethod
    async def get_campaign_performance(merchant_id: str):
        """Campaign conversion analytics"""
        pipeline = [
            {"$match": {"merchant_id": merchant_id, "status": "completed"}},
            {"$group": {
                "_id": "$campaign_type",
                "total_campaigns": {"$sum": 1},
                "total_revenue": {"$sum": "$revenue_generated"},
                "avg_conversion": {"$avg": "$conversion_rate"},
                "total_links": {"$sum": {"$size": "$generated_payment_links"}}
            }},
            {"$sort": {"total_revenue": -1}}
        ]
        return await GrowthCampaign.aggregate(pipeline).to_list(10)
```

---

## 4. GUARDIAN AGENT (MongoDB-Optimized)

```python
# backend/agents/guardian.py
from beanie.operators import And, Gte, Lte, Eq
from backend.models import IntentMandate, CartMandate, AuditLog
from backend.services.audit import AuditService

class GuardianAgent:
    """
    Intercepts every money action before execution.
    Uses MongoDB aggregation for real-time spending calculation.
    """
    
    async def validate_action(self, action: MoneyAction) -> GuardianDecision:
        # 1. Check active Intent Mandate
        mandate = await IntentMandate.find_one(
            And(
                Eq(IntentMandate.merchant_id, action.merchant_id),
                Eq(IntentMandate.buyer_did, action.buyer_did),
                Eq(IntentMandate.status, "active"),
                Gte(IntentMandate.expires_at, datetime.utcnow())
            )
        )
        
        if not mandate:
            return GuardianDecision(deny=True, reason="NO_VALID_MANDATE")
        
        # 2. Calculate daily spent using MongoDB aggregation
        daily_spent = await self._calculate_daily_spent(
            action.buyer_did, 
            action.merchant_id
        )
        
        if daily_spent + action.amount > mandate.scope.max_amount_daily:
            return GuardianDecision(
                deny=True,
                reason="DAILY_LIMIT_EXCEEDED",
                current_spent=daily_spent,
                limit=mandate.scope.max_amount_daily,
                suggested_action="REQUEST_CART_MANDATE"
            )
        
        # 3. Category check
        if action.category not in mandate.scope.allowed_categories:
            return GuardianDecision(deny=True, reason="CATEGORY_NOT_ALLOWED")
        
        # 4. Merchant whitelist
        merchant_did = f"did:web:merchant-ai.dev/{action.merchant_id}"
        if merchant_did not in mandate.scope.merchant_dids:
            return GuardianDecision(deny=True, reason="MERCHANT_NOT_AUTHORIZED")
        
        # 5. Fraud heuristics (MongoDB aggregation for pattern detection)
        risk_score = await self._calculate_risk_score(action)
        if risk_score > 0.8:
            return GuardianDecision(
                deny=True,
                reason="HIGH_RISK_SCORE",
                risk_details={"score": risk_score, "factors": await self._get_risk_factors(action)}
            )
        
        # 6. APPROVE with embedded audit log
        decision = GuardianDecision(approve=True, bounds_checked=True)
        
        # Create audit log document with embedded decision
        audit_entry = AuditLog(
            action_type=action.action_type,
            actor=action.actor,
            agent_id=action.agent_id,
            buyer_id=action.buyer_id,
            merchant_id=action.merchant_id,
            amount=action.amount,
            currency=action.currency,
            mandate_id=mandate.mandate_id,
            guardian_decision=decision.dict(),
            reasoning=await self._generate_reasoning(action, mandate, decision),
            request_payload=action.dict(),
            status="SUCCESS" if decision.approve else "DENIED",
            hmac_signature=await AuditService.sign_audit_entry(action, decision)
        )
        await audit_entry.insert()
        
        return decision
    
    async def _calculate_daily_spent(self, buyer_did: str, merchant_id: str) -> int:
        """Use MongoDB aggregation for real-time daily spending"""
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        pipeline = [
            {"$match": {
                "buyer_id": buyer_did,
                "merchant_id": merchant_id,
                "status": "SUCCESS",
                "timestamp": {"$gte": today_start},
                "action_type": {"$in": ["CAPTURE_PAYMENT", "CREATE_ORDER"]}
            }},
            {"$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }}
        ]
        result = await AuditLog.aggregate(pipeline).to_list(1)
        return result[0]["total"] if result else 0
    
    async def _calculate_risk_score(self, action: MoneyAction) -> float:
        """MongoDB-based fraud detection using velocity patterns"""
        # Check transaction velocity (count in last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        velocity_pipeline = [
            {"$match": {
                "buyer_id": action.buyer_id,
                "timestamp": {"$gte": hour_ago}
            }},
            {"$group": {
                "_id": None,
                "count": {"$sum": 1},
                "total_amount": {"$sum": "$amount"}
            }}
        ]
        velocity = await AuditLog.aggregate(velocity_pipeline).to_list(1)
        
        # Simple risk heuristic
        risk = 0.0
        if velocity:
            if velocity[0]["count"] > 10:
                risk += 0.4
            if velocity[0]["total_amount"] > 1000000:  # > 10k in 1 hour
                risk += 0.4
        
        return min(risk, 1.0)
```

---

## 5. GROWTH AGENT (MongoDB-Powered)

```python
# backend/agents/growth.py
from beanie.operators import And, Eq, In, Lt
from backend.models import RazorpayOrder, RazorpayPayment, Product, GrowthCampaign

class GrowthAgent:
    """
    AI-powered revenue optimization using MongoDB analytics.
    """
    
    async def analyze_abandoned_carts(self, merchant_id: str) -> List[dict]:
        """Find abandoned carts using aggregation"""
        pipeline = [
            {"$match": {
                "merchant_id": merchant_id,
                "status": {"$in": ["created", "attempted"]},
                "created_at": {"$lte": datetime.utcnow() - timedelta(hours=1)}
            }},
            {"$lookup": {
                "from": "razorpay_payments",
                "localField": "razorpay_order_id",
                "foreignField": "order_id",
                "as": "payments"
            }},
            {"$match": {
                "payments": {"$not": {"$elemMatch": {"status": "captured"}}}
            }},
            {"$lookup": {
                "from": "products",
                "localField": "notes.product_id",
                "foreignField": "product_id",
                "as": "product"
            }},
            {"$project": {
                "order_id": "$razorpay_order_id",
                "amount": 1,
                "created_at": 1,
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "product_category": {"$arrayElemAt": ["$product.category", 0]}
            }}
        ]
        return await RazorpayOrder.aggregate(pipeline).to_list(100)
    
    async def generate_recovery_campaign(self, merchant_id: str) -> GrowthCampaign:
        """Auto-generate abandoned cart recovery campaign"""
        abandoned = await self.analyze_abandoned_carts(merchant_id)
        
        if not abandoned:
            return None
        
        # Use LLM to generate personalized messaging
        campaign = GrowthCampaign(
            merchant_id=merchant_id,
            campaign_type="abandoned_cart",
            target_segment={
                "criteria": "abandoned_carts_1h",
                "count": len(abandoned),
                "total_value": sum(a["amount"] for a in abandoned)
            },
            ai_reasoning=f"Detected {len(abandoned)} abandoned carts worth ₹{sum(a['amount'] for a in abandoned)/100:.2f}",
            status="draft"
        )
        
        # Generate payment links for each abandoned cart
        for cart in abandoned:
            link = await self.razorpay.create_payment_link(
                amount=cart["amount"],
                description=f"Complete your purchase: {cart.get('product_name', 'Your order')}",
                customer={"email": cart.get("customer_email")}
            )
            campaign.generated_payment_links.append(PaymentLinkRef(
                link_id=f"link_{uuid4().hex[:8]}",
                razorpay_link_id=link["id"],
                amount=cart["amount"],
                status="active"
            ))
        
        await campaign.insert()
        return campaign
    
    async def get_upsell_recommendations(self, merchant_id: str, product_id: str) -> List[dict]:
        """Collaborative filtering using MongoDB aggregation"""
        # Find customers who bought this product
        pipeline = [
            {"$match": {
                "merchant_id": merchant_id,
                "status": "captured",
                "notes.product_id": product_id
            }},
            {"$group": {
                "_id": "$email",
                "orders": {"$push": "$notes.product_id"}
            }},
            {"$unwind": "$orders"},
            {"$match": {"orders": {"$ne": product_id}}},
            {"$group": {
                "_id": "$orders",
                "co_purchase_count": {"$sum": 1}
            }},
            {"$sort": {"co_purchase_count": -1}},
            {"$limit": 5},
            {"$lookup": {
                "from": "products",
                "localField": "_id",
                "foreignField": "product_id",
                "as": "product"
            }},
            {"$project": {
                "product_id": "$_id",
                "co_purchase_count": 1,
                "product_name": {"$arrayElemAt": ["$product.name", 0]},
                "price": {"$arrayElemAt": ["$product.base_price_paise", 0]}
            }}
        ]
        return await RazorpayPayment.aggregate(pipeline).to_list(5)
```

---

## 6. MCP CATALOG SERVER (MongoDB-Backed)

```python
# backend/mcp/server.py
from beanie.operators import And, Eq, Gte, In
from backend.models import Product

class MCPCatalogServer:
    """
    Exposes merchant catalog via MCP protocol.
    Uses MongoDB queries for flexible product discovery.
    """
    
    async def list_products(self, merchant_id: str, filters: dict = None):
        """MCP tool: list_products"""
        query = And(
            Eq(Product.merchant_id, merchant_id),
            Eq(Product.is_active, True)
        )
        
        if filters:
            if "category" in filters:
                query = And(query, Eq(Product.category, filters["category"]))
            if "max_price" in filters:
                query = And(query, Lte(Product.base_price_paise, filters["max_price"]))
            if "in_stock" in filters and filters["in_stock"]:
                query = And(query, Gte(Product.total_stock, 1))
            if "tags" in filters:
                query = And(query, In(Product.tags, filters["tags"]))
        
        products = await Product.find(query).to_list(50)
        
        return {
            "products": [p.agent_readable for p in products],
            "count": len(products),
            "merchant_did": f"did:web:merchant-ai.dev/{merchant_id}"
        }
    
    async def get_product_details(self, product_id: str):
        """MCP tool: get_product_details"""
        product = await Product.find_one(Eq(Product.product_id, product_id))
        if not product:
            return {"error": "Product not found"}
        
        return {
            "product": product.agent_readable,
            "variants": [v.dict() for v in product.variants],
            "stock_status": "in_stock" if product.total_stock > 0 else "out_of_stock",
            "negotiable": product.agent_readable.get("agent_commerce", {}).get("negotiable", False)
        }
    
    async def check_availability(self, product_id: str, quantity: int):
        """MCP tool: check_availability"""
        product = await Product.find_one(Eq(Product.product_id, product_id))
        if not product:
            return {"available": False, "reason": "Product not found"}
        
        available = product.total_stock >= quantity
        return {
            "available": available,
            "requested": quantity,
            "in_stock": product.total_stock,
            "can_fulfill": available
        }
    
    async def negotiate_price(self, product_id: str, proposed_price: int, quantity: int):
        """MCP tool: negotiate_price — AI-powered negotiation"""
        product = await Product.find_one(Eq(Product.product_id, product_id))
        if not product:
            return {"error": "Product not found"}
        
        # AI negotiation logic
        base_price = product.base_price_paise
        bulk_discount = 0.05 if quantity >= 5 else 0.02 if quantity >= 2 else 0
        
        min_acceptable = int(base_price * (1 - bulk_discount) * 0.85)  # 15% max discount
        
        if proposed_price >= min_acceptable:
            return {
                "negotiation": "accepted",
                "final_price": proposed_price,
                "quantity": quantity,
                "total": proposed_price * quantity,
                "discount_percent": round((1 - proposed_price / base_price) * 100, 2)
            }
        else:
            counter = int(base_price * (1 - bulk_discount) * 0.90)
            return {
                "negotiation": "countered",
                "proposed_price": proposed_price,
                "counter_price": counter,
                "quantity": quantity,
                "total": counter * quantity,
                "message": f"I can offer ₹{counter/100:.2f} per unit for this quantity."
            }
```

---

## 7. UPDATED FILE STRUCTURE (MongoDB)

```
merchant-ai/
├── README.md                          # Comprehensive setup + demo instructions
├── docker-compose.yml
├── .env.example
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI app entry
│   │   ├── config.py                  # Settings, env vars, MongoDB config
│   │   ├── database.py                # Motor + Beanie initialization
│   │   ├── models/                    # Beanie Document models (MongoDB)
│   │   │   ├── __init__.py
│   │   │   ├── merchant.py
│   │   │   ├── product.py
│   │   │   ├── mandate.py            # IntentMandate + CartMandate
│   │   │   ├── transaction.py         # RazorpayOrder + RazorpayPayment
│   │   │   ├── audit.py
│   │   │   ├── campaign.py
│   │   │   └── agent_state.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── merchants.py
│   │   │   ├── products.py
│   │   │   ├── mandates.py
│   │   │   ├── checkout.py
│   │   │   ├── growth.py
│   │   │   ├── audit.py
│   │   │   ├── demo.py
│   │   │   └── webhooks.py
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py
│   │   │   ├── tools.py
│   │   │   └── schemas.py
│   │   ├── ap2/
│   │   │   ├── __init__.py
│   │   │   ├── mandates.py
│   │   │   ├── crypto.py              # JWS signing/verification
│   │   │   └── schemas.py
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── graph.py               # LangGraph state machine
│   │   │   ├── guardian.py
│   │   │   ├── growth.py
│   │   │   ├── buyer.py               # ShopBot
│   │   │   ├── catalog.py
│   │   │   ├── audit.py
│   │   │   ├── failure.py
│   │   │   └── tools.py
│   │   ├── razorpay_client/
│   │   │   ├── __init__.py
│   │   │   ├── client.py
│   │   │   ├── orders.py
│   │   │   ├── payments.py
│   │   │   ├── refunds.py
│   │   │   ├── links.py
│   │   │   ├── subscriptions.py
│   │   │   ├── smart_collect.py
│   │   │   └── route.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── analytics.py           # MongoDB aggregation pipelines
│   │       ├── campaign.py
│   │       └── websocket.py
│   └── tests/
│       ├── conftest.py
│       ├── test_razorpay.py
│       ├── test_mandates.py
│       ├── test_guardian.py
│       └── test_e2e.py
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── next.config.js
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx
│   │   ├── dashboard/
│   │   │   ├── page.tsx
│   │   │   ├── analytics/
│   │   │   ├── catalog/
│   │   │   ├── campaigns/
│   │   │   ├── mandates/
│   │   │   └── audit/
│   │   └── demo/
│   │       └── shopbot/
│   ├── components/
│   │   ├── ui/                        # shadcn components
│   │   ├── dashboard/
│   │   ├── agents/
│   │   ├── mandates/
│   │   └── audit/
│   ├── lib/
│   │   ├── api.ts
│   │   ├── websocket.ts
│   │   └── utils.ts
│   └── types/
│       └── index.ts
└── docs/
    ├── architecture.md
    ├── ap2-protocol.md
    └── api-reference.md
```

---

## 8. DOCKER COMPOSE (MongoDB + Redis)

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongo:27017
      - MONGODB_DB_NAME=merchant_ai
      - REDIS_URL=redis://redis:6379
      - RAZORPAY_KEY_ID=${RAZORPAY_KEY_ID}
      - RAZORPAY_KEY_SECRET=${RAZORPAY_KEY_SECRET}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - JWT_SECRET=${JWT_SECRET}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    volumes:
      - ./backend:/app
    depends_on:
      - mongo
      - redis
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app
    command: npm run dev

  mongo:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongo_data:/data/db
      - ./mongo-init.js:/docker-entrypoint-initdb.d/mongo-init.js:ro
    environment:
      - MONGO_INITDB_DATABASE=merchant_ai

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  mongo-express:
    image: mongo-express:1.0.2
    ports:
      - "8081:8081"
    environment:
      - ME_CONFIG_MONGODB_URL=mongodb://mongo:27017/
    depends_on:
      - mongo

volumes:
  mongo_data:
  redis_data:
```

---

## 9. MONGODB LEARNING OPPORTUNITIES IN THIS PROJECT

| MongoDB Feature | Where You'll Use It |
|-----------------|---------------------|
| **Document Modeling** | Nested mandates, embedded payment attempts, rich audit logs |
| **Indexing** | Compound indexes for merchant+status queries, TTL indexes for cart mandate expiry |
| **Aggregation Pipeline** | Revenue analytics, abandoned cart detection, upsell recommendations, fraud scoring |
| **Change Streams** | Real-time dashboard updates when payments are captured |
| **Text Search** | Product catalog search for MCP discovery |
| **Geospatial** | (Optional) Location-based merchant/agent matching |
| **Transactions** | Multi-document ACID for order+payment+audit atomic writes |
| **Schema Validation** | Enforce document structure at database level |

---

## 10. CLAUDE CODE PROMPT (Updated for MongoDB)

> "Read PRD.md and implement Phase 1: Foundation. Set up the monorepo with FastAPI backend, Next.js frontend, MongoDB 7.0, and Redis using Docker Compose. Use Beanie as the async ODM for MongoDB. Create all Document models from Section 3 with proper indexes. Set up the Razorpay test client. Follow the file structure exactly. Ensure MongoDB connection pooling and TTL indexes are configured."

---

This MongoDB version maintains all the protocol-forward depth, agent sophistication, and judging-bar compliance of the original while giving you a powerful document database to learn. The flexible schema will actually make iterating on agent states, mandates, and audit trails faster during the buildathon sprint.

**Ready to build?** 🚀