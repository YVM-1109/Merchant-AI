from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.merchants import router as merchants_router
from app.api.products import router as products_router
from app.api.checkout import router as checkout_router
from app.api.webhooks import router as webhooks_router
from app.api.analytics import router as analytics_router
from app.api.demo import router as demo_router
from app.api.audit import router as audit_router
from app.api.growth import router as growth_router
from app.database import MongoDB


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await MongoDB.connect()
    yield
    # Shutdown
    await MongoDB.disconnect()


app = FastAPI(
    title="Merchant-AI",
    version="0.1.0",
    redirect_slashes=False,
    lifespan=lifespan,
)

from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

_origins = [o.strip() for o in settings.ALLOWED_ORIGINS.split(",")] if settings.ALLOWED_ORIGINS else ["http://localhost:3000"]
if "*" in _origins:
    _origins = ["*"]  # Wildcard explicitly, no credentials
    _allow_credentials = False
else:
    _allow_credentials = True
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchants_router)
app.include_router(products_router)
app.include_router(checkout_router)
app.include_router(webhooks_router)
app.include_router(analytics_router)
app.include_router(demo_router)
app.include_router(audit_router)
app.include_router(growth_router)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}
