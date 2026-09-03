from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie

from app.config import settings
from app.models import (
    Merchant,
    Product,
    IntentMandate,
    CartMandate,
    RazorpayOrder,
    RazorpayPayment,
    AuditLog,
    GrowthCampaign,
    AgentStateSnapshot,
)


class MongoDB:
    client: AsyncIOMotorClient | None = None

    @classmethod
    async def connect(cls) -> None:
        cls.client = AsyncIOMotorClient(
            settings.MONGODB_URL,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            retryWrites=True,
            w="majority",
        )

        await init_beanie(
            database=cls.client[settings.MONGODB_DB_NAME],
            document_models=[
                Merchant,
                Product,
                IntentMandate,
                CartMandate,
                RazorpayOrder,
                RazorpayPayment,
                AuditLog,
                GrowthCampaign,
                AgentStateSnapshot,
            ],
        )

        # TTL indexes for ephemeral data (idempotent — skip if already a TTL index)
        db = cls.client[settings.MONGODB_DB_NAME]
        try:
            await db.cart_mandates.create_index("expires_at", expireAfterSeconds=0)
        except Exception:
            pass
        try:
            await db.agent_state_snapshots.create_index(
                "created_at", expireAfterSeconds=86400
            )
        except Exception:
            pass

    @classmethod
    async def disconnect(cls) -> None:
        if cls.client:
            cls.client.close()
