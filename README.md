# Merchant-AI — Agentic Commerce Operating System

An agentic commerce platform for **Razorpay merchants**, built around the **AP2 buyer protocol** (Agent Buyer Protocol v2). Features **AI Growth Co-pilot**, **JWS-signed mandates**, **Guardian fraud protection**, **Redis pub/sub event streaming**, and a **multi-agent LangGraph architecture**. Backend: **FastAPI + Beanie + MongoDB 7.0 + Redis**. Frontend: **Next.js 14 + shadcn/ui + Tailwind + Recharts**.

---

## ✨ Key Features

| Feature | Description |
|---|---|
| **AI Growth Co-pilot** | Analyzes abandoned carts & mandrates, generates recovery campaigns, upsell recommendations, and automated payment links via LangGraph agents |
| **AP2 Protocol** | JWS-signed Cart Mandates — buyers sign off-chain mandates with their private key; Guardian agent validates scope before any payment is created |
| **Guardian Agent** | Real-time fraud & bounds-checking: daily spend limits, category whitelisting, velocity scoring, merchant DIDs verification |
| **Agentic Buyer Flow** | ShopBot agent discovers products, presents CartMandate, gets Guardian approval, and settles via Razorpay — fully auditable |
| **Razorpay Integration** | Orders, Payments, Refunds, and Webhook signature verification with HMAC-SHA256 |
| **Multi-Agent Architecture** | LangGraph StateGraph with 4 specialized agents: GrowthAgent, BuyerAgent, GuardianAgent, CatalogAgent, FailureAgent |
| **Real-time Events** | Redis pub/sub for Razorpay webhook events — async processing by FailureAgent on payment failures |
| **Audit Trail** | Immutable audit log with HMAC signatures — every money action chained and verifiable |
| **MCP Catalog Server** | Exposes product catalog as MCP tools for agent discovery |

---

## 🏗 Architecture

```
merchant-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI app bootstrap, CORS, lifespan
│   │   ├── config.py               # Pydantic Settings — all secrets via env
│   │   ├── database.py             # Beanie async init + TTL indexes
│   │   ├── models/                 # Beanie Document models (9 schemas)
│   │   │   ├── merchant.py
│   │   │   ├── product.py
│   │   │   ├── intent_mandate.py
│   │   │   ├── cart_mandate.py
│   │   │   ├── transaction.py
│   │   │   ├── audit.py
│   │   │   └── ...
│   │   ├── api/                    # FastAPI routers
│   │   │   ├── merchants.py
│   │   │   ├── products.py
│   │   │   ├── checkout.py         # AP2 cart-mandate checkout flow
│   │   │   ├── webhooks.py         # Razorpay webhook + HMAC verification
│   │   │   ├── growth.py           # Trigger GrowthAgent campaigns
│   │   │   ├── analytics.py        # Mongo aggregation pipelines
│   │   │   └── audit.py            # Audit log queries
│   │   ├── agents/                 # LangGraph multi-agent system
│   │   │   ├── graph.py            # Compiled StateGraph
│   │   │   ├── guardian.py         # Money-action bounds checking
│   │   │   ├── growth.py           # AI growth co-pilot
│   │   │   ├── buyer.py           # ShopBot / BuyerAgent
│   │   │   ├── catalog.py          # Product discovery
│   │   │   ├── failure.py          # Error recovery & retry logic
│   │   │   └── tools.py            # Shared agent tool scaffold
│   │   ├── ap2/                    # AP2 protocol core
│   │   │   ├── crypto.py           # JWS sign/verify (trust boundary)
│   │   │   ├── mandates.py         # IntentMandate + CartMandate creation
│   │   │   └── schemas.py          # JSON-LD mandate structure
│   │   ├── mcp/
│   │   │   └── server.py           # MCP Catalog Server
│   │   └── razorpay_client/        # Razorpay SDK wrapper
│   │       ├── client.py
│   │       └── webhooks.py
│   └── requirements.txt
│
├── frontend/
│   ├── app/
│   │   ├── dashboard/              # Merchant dashboard
│   │   ├── demo/shopbot/          # ShopBot buyer flow demo
│   │   └── ...
│   ├── components/                 # shadcn/ui + custom components
│   └── lib/api.ts                 # Axios instance + token management
│
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔄 Core Flows

### AP2 Buyer Checkout Flow

```
1. BUYER presents signed CartMandate (JWS)
   → POST /api/v1/checkout
   → Buyer signs mandate with private key off-chain

2. GUARDIAN validation
   → GuardianAgent validates IntentMandate scope:
     - Daily spend ≤ max_amount_daily
     - Transaction ≤ max_amount_per_txn
     - Category ∈ allowed_categories
     - Merchant DID ∈ merchant_dids whitelist
     - Within duration_hours window

3. CART MANDATE stored
   → Status: signed_pending_payment
   → Nonce + expiry (7 days) for replay protection

4. RAZORPAY ORDER created
   → receipt = cart_mandate_id
   → notes: { cart_mandate_id, merchant_id, buyer_did }

5. FRONTEND collects payment
   → Razorpay Checkout button

6. WEBHOOK confirmation (trusted path only)
   → POST /api/v1/webhooks/razorpay
   → HMAC-SHA256 signature verification
   → payment.captured → CartMandate.status = "paid"
   → Order.paid → CartMandate.status = "settled"
   → Event published to Redis → FailureAgent processes

7. AUDIT LOG entry
   → Immutable, HMAC-signed chain
   → action_type: CAPTURE_PAYMENT / REFUND
   → hmac_signature links to previous entry
```

### AI Growth Co-pilot Flow

```
1. AGENT analyzes abandoned carts
   → Queries CartMandate with status = signed_pending_payment
   → Identifies stale (>24h, not settled)

2. CAMPAIGN generation
   → GrowthAgent uses LLM to generate recovery campaign
   → Creates Razorpay Payment Link via API

3. DISPATCH
   → Email/SMS via campaign config
   → Tracks click-through + payment

4. FAILURE handling
   → FailureAgent catches failed webhooks
   → Queues retry with exponential backoff
   → Redis pub/sub triggers reprocessing
```

---

## 🛡 Security Highlights

| Layer | Implementation |
|---|---|
| **Authentication** | JWT (HS256) — access tokens with configurable expiry |
| **Password Security** | N/A (API-first — auth handled by integration layer) |
| **Webhooks** | HMAC-SHA256 verification of `X-Razorpay-Signature` against `RAZORPAY_WEBHOOK_SECRET` |
| **JWS Mandates** | Cart Mandates signed with buyer's ES256 private key; verified against buyer's public key |
| **Guardian Agent** | Enforces spend limits, category whitelist, merchant whitelist, time window — on-chain validation before any Razorpay order creation |
| **Nonce & Expiry** | Each CartMandate has a UUID nonce + 7-day expiry; prevents replay attacks |
| **CORS** | Hardened — origins parsed from `ALLOWED_ORIGINS` env, stripped, wildcard handled separately from credentials |
| **Secrets** | All secrets in environment variables — never hardcoded; `.env` + `.env.local` in `.gitignore` |
| **Audit Trail** | Immutable log entries with HMAC-SHA256 signatures chained to previous entry — tamper-evident |
| **Redis** | Webhook → Redis → async processing; try/finally ensures connection cleanup |

---

## 🚀 Quick Start

### Prerequisites

| Component | Status |
|---|---|
| Docker Desktop | ✅ v29+ recommended |
| Python | ✅ 3.11+ (for local dev) |
| Node.js | ✅ 24+ (for local dev) |
| Razorpay Account | ✅ Test mode keys required |

---

### 1. Clone & Configure

```bash
git clone https://github.com/YVM-1109/Merchant-AI.git
cd merchant-ai
cp .env.example .env
```

Edit `.env` with your values:

```bash
# ── Backend ──
MONGODB_URL=mongodb://admin:password@mongo:27017/merchant_ai?authSource=admin
MONGODB_DB_NAME=merchant_ai
REDIS_URL=redis://redis:6379/0

# Razorpay (test mode — get from https://dashboard.razorpay.com/)
RAZORPAY_KEY_ID=rzp_test_xxxxx
RAZORPAY_KEY_SECRET=xxxxxxxx
RAZORPAY_WEBHOOK_SECRET=whsec_xxxxx

# JWT (generate with: openssl rand -base64 32)
JWT_SECRET=YOUR_BASE64_ENCODED_256_BIT_SECRET

# CORS (comma-separated origins)
ALLOWED_ORIGINS=http://localhost:3000
```

---

### 2. Start Everything

```bash
docker compose up --build
```

| Service | URL |
|---|---|
| Backend API | http://localhost:8000 |
| Swagger UI | http://localhost:8000/docs |
| Frontend | http://localhost:3000 |
| Mongo Express | http://localhost:8081 |
| Redis Commander | http://localhost:8082 |

---

### 3. Razorpay Webhook (Local Testing)

For webhooks to reach your local backend, use a tunnel:

```bash
# Option 1: ngrok
ngrok http 8000
# → copy the https URL, e.g. https://abcd-1234.ngrok-free.app

# Option 2: Cloudflare Tunnel
cloudflared tunnel --url http://localhost:8000
```

In **Razorpay Dashboard → Settings → Webhooks**:

- **URL**: `https://your-tunnel-url/api/v1/webhooks/razorpay`
- **Secret**: same as `RAZORPAY_WEBHOOK_SECRET` in `.env`
- **Events**: `payment.captured`, `payment.failed`, `order.paid`, `refund.processed`

---

## 🧪 Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

**37 tests** covering:

- AP2 cryptography (JWS sign/verify, tamper detection)
- GuardianAgent bounds checking (approval + denial paths)
- Checkout flow (IntentMandate reuse, CartMandate signing)
- Webhook handler (signature verification, Redis pub/sub)
- Razorpay client wrapper (order creation, webhook verification)

Frontend E2E tests:

```bash
cd frontend
npx playwright test
```

---

## 📦 Production Build

### Backend

```bash
cd backend
docker compose up --build -d
```

### Frontend

```bash
cd frontend
npm run build
# Output: .next/ → deploy to Vercel, nginx, or static host
```

---

## 🐳 Docker

```yaml
# docker-compose.yml (key services)
services:
  mongo:
    image: mongo:7.0
    volumes:
      - mongo_data:/data/db
    ports: ["27017:27017"]

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build: ./backend
    env_file: ./backend/.env
    ports: ["8000:8000"]
    depends_on: [mongo, redis]

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    env_file: ./frontend/.env
    depends_on: [backend]

  mongo-express:
    image: mongo-express:latest
    ports: ["8081:8081"]
    depends_on: [mongo]
```

---

## 📁 API Reference

### Auth & Merchants

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| POST | `/api/v1/merchants` | Register new merchant |
| GET | `/api/v1/merchants/{id}` | Get merchant |

### Products

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/products/merchant/{merchant_id}` | List all products for merchant |
| POST | `/api/v1/products` | Create product |
| GET | `/api/v1/products/{id}` | Get single product |

### Checkout (AP2)

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/checkout` | AP2 checkout flow — creates IntentMandate, signs CartMandate, Guardian validates |

### Webhooks

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/v1/webhooks/razorpay` | Public (HMAC) | Receive Razorpay events — signature verified via HMAC-SHA256 |

### Growth Agent

| Method | Path | Description |
|---|---|---|
| POST | `/api/v1/growth/campaigns` | Trigger AI GrowthAgent campaign generation |

### Analytics

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/analytics/dashboard/{merchant_id}` | Mongo aggregation: revenue, mandate volume, failure rate |

---

## 🔧 Configuration Reference

### Backend Environment Variables

| Variable | Required | Description |
|---|---|---|
| `MONGODB_URL` | ✅ | MongoDB connection string |
| `MONGODB_DB_NAME` | ✅ | Database name (default: `merchant_ai`) |
| `REDIS_URL` | ✅ | Redis connection URL |
| `RAZORPAY_KEY_ID` | ✅ | Razorpay test/live key ID |
| `RAZORPAY_KEY_SECRET` | ✅ | Razorpay test/live key secret |
| `RAZORPAY_WEBHOOK_SECRET` | ✅ | Webhook signature secret (HMAC-SHA256) |
| `JWT_SECRET` | ✅ | Base64-encoded 256-bit secret for JWT signing |
| `ALLOWED_ORIGINS` | ❌ | Comma-separated CORS origins (default: `http://localhost:3000`) |

---

## 🌱 Seeded Data

The backend auto-seeds on first run if MongoDB is empty:

| Document | Count | Content |
|---|---|---|
| Merchant | 1 | `demo-merchant` — for quick testing |
| Products | 3 | Wireless mouse, mechanical keyboard, USB-C hub |
| IntentMandate | 0 | Created on-demand per buyer |

---

## 🐛 Known Limitations

1. **Single-instance Redis** — Redis pub/sub uses single-node in Docker Compose. For multi-instance deployments, ensure a shared Redis cluster.
2. **No email delivery** — GrowthAgent generates campaigns and payment links, but email/SMS dispatch is not yet integrated.
3. **Webhook idempotency** — Currently relies on CartMandate status transitions. For high-throughput, add explicit idempotency key tracking.
4. **Agent persistence** — LangGraph checkpoints are persisted to MongoDB, but long-running conversations may need archive strategy.

---

## 🗺 Roadmap

- Email/SMS campaign dispatch integration
- Multi-tenant agent isolation (per-merchant agent instances)
- Real-time dashboard with WebSocket/SSE updates
- x402 protocol integration (Pay-to-use-agent APIs)
- Solana integration via x402 for on-chain settlements
- Advanced fraud scoring (LLM-based anomaly detection)
- White-label merchant portal builder

---

## 🤝 Contributing

1. Fork the repo
2. Create feature branch: `git checkout -b feat/amazing-feature`
3. Install deps: `pip install -r backend/requirements.txt`
4. Commit: `feat: add amazing feature`
5. Push and open PR

**Code style**:

- Backend: PEP 8, type hints on all function signatures, async/await throughout
- Frontend: ESLint + Prettier, TypeScript strict mode

---

> **Built for learning & demonstration.** A solid foundation for an agentic commerce operating system. Not a production-ready financial platform — but a faithful implementation of AP2-style buyer protocol with real Razorpay integration.
