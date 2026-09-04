# Customer Storefront Implementation Plan

## Overview
Add Amazon-style browsing + cart flow for customers while preserving the existing merchant portal and ShopBot chat. Checkout reuses the AP2 protocol (IntentMandate → CartMandate → GuardianAgent → Razorpay).

## Tasks

### 1. Backend: `/api/v1/store` endpoints
**File:** `backend/app/api/store.py` (NEW, ~80 lines)

- **GET `/api/v1/store/products`** — query `Product.find(Product.merchant_id == merchant_id, Product.is_active == True)`, return list
- **POST `/api/v1/store/checkout`** — same flow as `checkout.py::create_checkout`, but accepts explicit `product_ids` + `quantities` from frontend cart

**Depends on:** Read `backend/app/api/checkout.py` (already read — lines 42-208), `backend/app/ap2/mandates.py`, `backend/app/agents/guardian.py`

**Tests:** `pytest tests/` (backend test suite should still pass — this is additive, no model changes)

---

### 2. Wire router into main
**File:** `backend/app/main.py` (EDIT)

- Add `from app.api.store import router as store_router`
- Add `app.include_router(store_router)` after existing `app.include_router(growth_router)`

**Estimated: 2 lines added**

---

### 3. Frontend: Product listing page
**File:** `frontend/app/store/page.tsx` (NEW, ~70 lines)

- Fetch products from `/api/v1/store/products?merchant_id=m_test` on mount
- Render responsive grid: product image (placeholder), name, description, price, "Add to Cart" button
- Cart badge showing item count (top-right corner)
- Cart state persisted in localStorage (key: `store_cart`)
- "View Cart" button to navigate to `/store/cart`

**Uses:** `api` from `frontend/lib/api.ts`, `formatCurrency` from `frontend/lib/utils.ts`

---

### 4. Frontend: Cart page
**File:** `frontend/app/store/cart/page.tsx` (NEW, ~85 lines)

- Load cart from localStorage on mount
- Cart table: product name, qty dropdown (1-9), unit price, line total, remove × button
- Live subtotal at bottom
- "Checkout with ShopBot" button → POST `/api/v1/store/checkout` with cart contents + buyer key (from `AP2Crypto.generatePrivateKey()`)
- On response: if `success=true` → redirect to `/store/thanks?session_id=<xxx>`
- On response: if Guardian denied → show error with Guardian reason
- "Continue Shopping" button → `/store`

**Uses:** `api`, `formatCurrency`, `AP2Crypto` from `frontend/lib/ap2.ts`

---

### 5. Frontend: Thank you page
**File:** `frontend/app/store/thanks/page.tsx` (NEW, ~40 lines)

- Read `session_id` from URL params
- Display: order confirmed header, Guardian decision badge (green check / amber shield), Razorpay order ID, product summary
- "Continue Shopping" button → `/store`

---

### 6. Update landing page
**File:** `frontend/app/page.tsx` (EDIT)

- Change "Shop as Customer →" link from `/demo/shopbot` to `/store`

**Estimated: 1 line**

---

## Verification

1. `docker compose down && docker compose up --build -d`
2. `curl -s http://localhost:8000/health` → `{"status":"ok"}`
3. Visit `http://localhost:3000/store` → see product grid
4. Add 2 items → go to `/store/cart` → see cart summary
5. Click "Checkout with ShopBot" → Guardian validates → redirect to `/store/thanks`
6. `pytest tests/` → all 21+ backend tests still pass