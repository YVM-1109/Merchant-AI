<!-- mermaid:agentic-commerce -->
<div align="center">

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                   MERCHANT–AI  ·  AGENTIC COMMERCE OS                        ║
║                                                                              ║
║           AP2 Protocol  ·  Guardian Agent  ·  LangGraph Multi-Agent          ║
║                                                                              ║
║    < buyer> ──JWS─> < guardian> ──validated─> < razorpay order> ──settle   ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

**Agentic Commerce Operating System for Razorpay Merchants**

Precision-engineered agent infrastructure: cryptographic purchase commitments (AP2), real-time fraud validation (Guardian), and autonomous cart-recovery agents (LangGraph).

[Documentation](https://github.com/YVM-1109/Merchant-AI) · [API Reference](#-api-reference) · [Architecture](#-architecture) · [Deployment](#-deployment)

</div>

---

## Overview

Merchant–AI is an **agentic commerce operating system** that sits between a buyer and the Razorpay payment stack. It replaces static checkout flows with a **multi-agent protocol**: buyers interact with a ShopBot agent, the Guardian Agent cryptographically validates purchase intent, and a signed purchase order is settled on Razorpay.

```
buyer agent      ──→ intent_mandate (buyer's key) ──→
guardian agent   ──→ verifies scope & fraud bounds ──→
cart_mandate     ──→ JWS signed cart (buyer + guardian) ──→
razorpay         ──→ order.created → payment.captured ──→
audit_log        ──→ immutable HMAC-chained record
```

### What you get

| Component         | Responsibility                                           |
|---|---|
| **AP2 Protocol**  | JWS-signed purchase mandates — off-chain intent, on-chain settlement |
| **Guardian Agent**| Real-time fraud bounds: spend caps, category whitelist, velocity scoring |
| **ShopBot Agent** | Natural-language product discovery → signed checkout → payment |
| **Growth Agent**  | Abandoned-cart analysis → automated recovery campaigns (agentic) |
| **Failure Agent** | Webhook retry with exponential backoff via Redis pub/sub |

---

## Architecture

### Service map

```
merchant-ai/
├── backend/                    # FastAPI + Beanie + MongoDB + Redis + LangGraph
│   │
│   ├── app/
│   │   ├── main.py              → FastAPI bootstrap, CORS, lifespan hooks
│   │   ├── config.py            → Pydantic Settings, all secrets via env
│   │   ├── database.py          → Beanie async init + TTL indexes
│   │   ├── models/              → Beanie Document models (9 schemas)
│   │   ├── api/                 → FastAPI routers
│   │   ├── agents/              → LangGraph multi-agent system
│   │   ├── ap2/                 → AP2 protocol core (crypto, mandates, schemas)
│   │   ├── razorpay_client/     → Razorpay SDK wrapper
│   │   └── mcp/                 → MCP Catalog Server
│   │
│   └── tests/                   → 21 tests — AP2 crypto, Guardian, checkout
│
├── frontend/                    # Next.js 14 + Tailwind + shadcn/ui
│   ├── app/
│   │   ├── store/               → Customer portal (browsing + ShopBot widget)
│   │   └── merchant/            → Merchant portal (dashboard, catalog, analytics)
│   ├── components/              → Shared UI components
│   └── lib/                     → API client, AP2 hooks, utilities
│
├── docker-compose.yml
├── .env.example
└── README.md
```

### AP2 Protocol

```
┌──────────┐  1. INTEN T_MANDATE                          ┌───────────┐
│  Buyer   │     buyer_did → agent_did                    │  Guardian │
│  Agent   │────┬───────────────────────────────────────→│  Agent    │
│          │     │ max_amount_daily, category_whitelist   │           │
└──────────┘     │                                      └───────────┘
                 │  2. CART_MANDATE (JWS)
                 │  merchant_id + cart_items + signature
                 │
                 ▼  3. VALIDATION
               ┌──────────┐                               ┌──────────────┐
               │  Guardian│── approved ──→                 │  AuditLog    │
               │  Agent   │                               │  (HMAC chain)│
               └──────────┘◄─ denied ────                └──────────────┘
                 │
                 ▼
              ┌────────┐    4. RAZORPAY ORDER
              │ Razorpay│──── create_order(amount, currency, receipt=cart_id)
              └────────┘
                 │
              ┌────────┐    5. WEBHOOK (HMAC-SHA256)
              │ Webhook│──── payment.captured → PurchaseOrder.paid = true
              └────────┘
```

### Guardian Validation Rules

```
guardian.validate_action(MoneyAction):

  ├── max_amount_per_txn  ←  per-transaction ceiling
  ├── max_amount_daily    ←  rolling 24h spend cap
  ├── allowed_categories  ←  merchant category whitelist
  ├── merchant_dids       ←  authorized merchant set
  ├── duration_hours      ←  mandate expiry window
  ├── velocity_score      ←  actions/min threshold
  └── risk_score          ←  LLM-based anomaly baseline

  decision ∈ {approved, denied, escalated}
```

---

## Deployment

### Local development

```bash
# 1. Configure
git clone https://github.com/YVM-1109/Merchant-AI.git
cd merchant-ai
cp .env.example .env
# Edit .env — see Configuration Reference below

# 2. Start services
docker compose up --build

# 3. Verify
curl http://localhost:8000/health
# → {"status":"ok"}

# Services
# Backend API:    http://localhost:8000
# Swagger UI:     http://localhost:8000/docs
# Frontend:       http://localhost:3000
# Mongo Express:  http://localhost:8081
# Redis Admin:    http://localhost:8082
```

### Razorpay webhook (local)

For webhook delivery during local development, tunnel your backend:

```bash
ngrok http 8000
# → https://abcd-1234.ngrok-free.app
```

In Razorpay Dashboard → Settings → Webhooks:

| Field    | Value                                         |
|---|---|
| URL      | `https://<your-tunnel>/api/v1/webhooks/razorpay` |
| Secret   | Same as `RAZORPAY_WEBHOOK_SECRET` in `.env`        |
| Events   | `payment.captured`, `payment.failed`, `order.paid`, `refund.processed` |

---

## API Reference

### Healthcheck

`GET /health`

### Merchants

`POST /api/v1/merchants` — Register a new merchant
`GET /api/v1/merchants/{id}` — Retrieve merchant details

### Products

`GET /api/v1/products/merchant/{merchant_id}` — List products
`POST /api/v1/products` — Create a product
`GET /api/v1/products/{id}` — Get single product
`PATCH /api/v1/products/{id}` — Update product (partial)

### Checkout (AP2)

`POST /api/v1/checkout` — Full AP2 flow: intent mandate → cart mandate → Guardian validation → Razorpay order

### Analytics

`GET /api/v1/analytics/dashboard/{merchant_id}?days=30` — Merchant dashboard metrics
`GET /api/v1/analytics/guardian-stats/{merchant_id}?days=30` — Guardian intervention + risk distribution
`GET /api/v1/analytics/daily-trend/{merchant_id}?days=30` — Daily revenue trend

### Webhooks

`POST /api/v1/webhooks/razorpay` — Razorpay webhook endpoint (public, HMAC-verified)

---

## Configuration

### Backend environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `MONGODB_URL` | ✅ | — | MongoDB connection string |
| `MONGODB_DB_NAME` | ✅ | `merchant_ai` | Database name |
| `REDIS_URL` | ✅ | `redis://redis:6379/0` | Redis connection URL |
| `RAZORPAY_KEY_ID` | ✅ | — | Razorpay key ID (test or live) |
| `RAZORPAY_KEY_SECRET` | ✅ | — | Razorpay key secret |
| `RAZORPAY_WEBHOOK_SECRET` | ✅ | — | Webhook HMAC secret |
| `JWT_SECRET` | ✅ | — | Base64-encoded 256-bit JWT signing key |
| `ALLOWED_ORIGINS` | ❌ | `http://localhost:3000` | Comma-separated CORS origins |

Generate a JWT secret:

```bash
openssl rand -base64 32
```

---

## Development

### Backend tests

```bash
cd backend
python -m pytest tests/ -v
```

**21 tests** cover:

- AP2 cryptography — JWS signing/verification, tamper detection
- Guardian Agent — approval + denial paths, bounds checking
- Checkout flow — intent reuse, signed cart mandate creation
- Webhook handler — HMAC verification, Redis pub/sub
- Razorpay client — order creation, signature validation

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

```bash
# E2E tests (Playwright)
npx playwright test
```

---

## Security

| Layer | Implementation |
|---|---|
| **Transport** | HTTPS everywhere (Nginx terminates TLS in prod) |
| **Auth** | JWT (HS256) access tokens — configurable expiry |
| **Webhooks** | HMAC-SHA256 verification of `X-Razorpay-Signature` |
| **Purchase Orders** | ES256 signatures on JWS-encoded mandates |
| **Fraud** | Guardian Agent validates spend, category, velocity before payment creation |
| **Replay Protection** | UUID nonce + 7-day expiry on every mandate |
| **CORS** | Strict origin allowlist via `ALLOWED_ORIGINS` |
| **Audit Trail** | Immutable HMAC-chained log — tamper-evident |
| **Secrets** | Environment variables only — `.env` in `.gitignore` |

---

## Known Limitations

1. **Redis pub/sub** uses single-node in Docker Compose — switch to Redis Cluster for HA
2. **Email/SMS dispatch** — campaigns are generated but not yet sent (Growth Agent stops at link creation)
3. **Webhook idempotency** — relies on PO status transitions; add explicit key tracking for high throughput
4. **Agent persistence** — LangGraph checkpoints stored in MongoDB; long conversations may need archival

---

## Roadmap

- Email/SMS campaign dispatch via SendGrid/Twilio
- Multi-tenant agent isolation (per-merchant agent instances)
- Real-time dashboard with WebSocket/SSE updates
- x402 protocol integration (pay-to-use agent APIs)
- Solana integration for on-chain settlements
- LLM-based anomaly detection for Guardian scoring
- White-label merchant portal builder

---

## Contributing

```bash
git checkout -b feat/amazing-feature
pip install -r backend/requirements.txt
cd frontend && npm install

git commit -m "feat: add amazing feature"
git push
```

**Code style:**

- Backend: PEP 8, type hints required, async/await throughout
- Frontend: ESLint + Prettier, TypeScript strict mode

---

> **Reference implementation — not certified for production financial workloads.**