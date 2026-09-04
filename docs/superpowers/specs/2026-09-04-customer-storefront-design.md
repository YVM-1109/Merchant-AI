# Customer Storefront Browsing Flow — Design Spec

## Context

Add an Amazon-style product browsing + cart flow for **customers** (separate from the existing ShopBot chat flow and the merchant portal). Customers should be able to browse products, add to cart, and checkout — all flowing through the existing AP2 protocol (IntentMandate → CartMandate → GuardianAgent → Razorpay order).

**Why:** The current ShopBot demo only lets customers chat with an AI buyer. Real e-commerce needs visual browsing + cart management. The checkout still goes through the same Guardian + Razorpay flow.

**Outcome:** Customer-facing `/store`, `/store/cart`, `/store/thanks` pages + `/api/v1/store` backend endpoints. Merchant portal (`/merchant/*`) is unchanged.

---

## Architecture

### New Frontend Pages

| Route | Component | Lines |
|---|---|---|
| `/store` | `ProductListingPage` — grid of active products with "Add to Cart" buttons | ~70 |
| `/store/cart` | `CartPage` — cart table, quantity adjust, checkout button | ~85 |
| `/store/thanks` | `ThankYouPage` — order confirmation with Guardian/Razorpay details | ~40 |

### New Backend Router

| File | Endpoints |
|---|---|
| `backend/app/api/store.py` | `GET /api/v1/store/products` + `POST /api/v1/store/checkout` |

Register in `backend/app/main.py`:
```python
from app.api.store import router as store_router
app.include_router(store_router)
```

### Reused Components (no changes needed)

| Component | File | Used For |
|---|---|---|
| `AP2Crypto` | `frontend/lib/ap2.ts` | Client-side buyer key generation |
| `formatCurrency` | `frontend/lib/utils.ts` | Price formatting |
| `api` (axios) | `frontend/lib/api.ts` | API calls with JWT/token support |
| `GuardianAgent` | `backend/app/agents/guardian.py` | MoneyAction validation |
| `RazorpayClient` | `backend/app/razorpay_client/client.py` | Order creation |
| `CartItem` / `CartMandate` / `IntentMandate` | `backend/app/models/mandate.py` | Data models |
| `CheckoutRequest` / `CheckoutResponse` | `backend/app/api/checkout.py` | Existing request/response schema (reused) |

---

## Data Flow

```
1. Customer visits /store
   → Frontend calls GET /api/v1/store/products?merchant_id=m_test
   → Backend returns active products

2. Customer adds items to cart
   → Cart state lives in React state + localStorage (no backend writes)

3. Customer clicks "Checkout with ShopBot"
   → Frontend POSTs /api/v1/store/checkout with:
      { merchant_id, buyer_did, product_ids, quantities, buyer_private_key }
   → Backend runs same flow as /api/v1/checkout:
      a. Lookup-or-create IntentMandate for buyer + merchant
      b. Build CartItems from selected products
      c. sign_cart_mandate() → CartMandate + buyer signature
      d. GuardianAgent.validate_action(MoneyAction)
      e. RazorpayClient.create_order() on approval
      f. Save CartMandate + AuditLog
   → Returns CheckoutResponse with razorpay_order + guardian_decision

4. Redirect to /store/thanks
   → Show order ID, Guardian decision, product summary
```

---

## API Spec

### `GET /api/v1/store/products`

**Query params:**
- `merchant_id` (required)

**Response:**
```json
[
  {
    "product_id": "p_abc123",
    "name": "Wireless Mouse",
    "description": "2.4GHz USB receiver",
    "base_price_paise": 9999,
    "category": "electronics",
    "currency": "INR",
    "total_stock": 50,
    "sales_velocity": 12.5,
    "is_active": true
  }
]
```

### `POST /api/v1/store/checkout`

Reuses `CheckoutRequest` from `checkout.py` (no new Pydantic model needed):

```json
{
  "merchant_id": "m_test",
  "buyer_did": "did:example:buyer123",
  "product_ids": ["p_abc123", "p_def456"],
  "quantities": {"p_abc123": 1, "p_def456": 2},
  "buyer_private_key": "-----BEGIN EC PRIVATE KEY-----\n..."
}
```

Returns `CheckoutResponse` (same shape as `/api/v1/checkout`).

---

## Implementation Plan

### Phase 1: Backend (`backend/app/api/store.py`)
- Create store router with two endpoints
- `GET /products` — query `Product.find(Product.merchant_id == merchant_id, Product.is_active == True)`
- `POST /checkout` — copy flow from `checkout.py::create_checkout` (lines 42-208), but accept explicit `product_ids` + `quantities` instead of auto-selecting

**Estimated: 80 lines**

### Phase 2: Frontend Pages

#### `/store/page.tsx`
- Fetch products on mount via `api.get('/api/v1/store/products?merchant_id=m_test')`
- Render grid: image placeholder + name + price + "Add to Cart" button
- Cart icon in header with item count
- Cart state: `useState<CartItem[]>` + `useEffect` persist to `localStorage`

**Estimated: 70 lines**

#### `/store/cart/page.tsx`
- Read cart from `localStorage` on mount
- Table: product name, qty input, unit price, line total, remove button
- Live subtotal at bottom
- "Checkout with ShopBot" button → POST `/api/v1/store/checkout`
- On success → redirect to `/store/thanks?session_id=xxx`

**Estimated: 85 lines**

#### `/store/thanks/page.tsx`
- Read `session_id` from URL params
- Display: "Order confirmed" header, Guardian decision badge (green approved / amber denied), Razorpay order ID, product summary
- "Continue Shopping" button → `/store`

**Estimated: 40 lines**

### Phase 3: Wiring
- Add `app.include_router(store_router)` to `backend/app/main.py`
- Add "Shop as Customer →" button on landing page (`frontend/app/page.tsx`) pointing to `/store`

**Total: 4 new files, ~285 lines of code**

---

## Verification

1. `docker compose up --build -d` — both containers rebuild with new routes
2. Visit `http://localhost:3000/store` → see product grid
3. Add items → visit `/store/cart` → see cart contents
4. Click "Checkout with ShopBot" → Guardian validation runs
5. Redirect to `/store/thanks` → order confirmation shows
6. Guard against duplicate: `GET /api/v1/store/products` returns only `is_active=True` products
7. No breaking changes to existing `/api/v1/checkout` (unchanged)

---

## Scope Exclusions

- **Merchant portal** (`/merchant/*`) — unchanged
- **ShopBot chat** (`/demo/shopbot`) — unchanged (still available as alternative flow)
- **User accounts / auth** — not needed for demo; cart is client-side only
- **Product search** — basic listing only (no search bar in v1)
- **Product detail page** — not needed; info shown on cart line items
- **Payment integration on frontend** — demo flow simulates payment capture; real Razorpay checkout.js can be added later
