# Merchant-AI

Agentic Commerce Operating System for Razorpay Merchants.

## Quick Start

```bash
# 1. Copy env and fill in real keys
cp .env.example .env

# 2. Start everything
docker compose up --build
```

Backend: http://localhost:8000
Frontend: http://localhost:3000
Swagger UI: http://localhost:8000/docs
Mongo Express: http://localhost:8081

## Prerequisites

- Docker Desktop (v29+ recommended)
- Python 3.11 (for local dev)
- Node 24+ (for local dev)

## Structure

```
merchant-ai/
├── docker-compose.yml
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/          # Beanie Document models
│   │   ├── api/             # FastAPI routers
│   │   ├── agents/          # LangGraph multi-agent system
│   │   ├── ap2/             # AP2 protocol (JWS + JSON-LD mandates)
│   │   ├── mcp/             # MCP catalog server
│   │   └── razorpay_client/ # Razorpay SDK wrapper
└── frontend/
    ├── app/
    ├── components/
    └── lib/
```
