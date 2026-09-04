"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { AP2Crypto } from "@/lib/ap2";
import { useState, useEffect } from "react";
import { ShoppingCart, Trash2, ArrowLeft, Shield, CheckCircle, AlertCircle, Sparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Suspense } from "react";

interface CartItem {
  product_id: string;
  name: string;
  base_price_paise: number;
  quantity: number;
}

interface CheckoutResponse {
  success: boolean;
  cart_mandate_id: string;
  intent_mandate_id: string;
  razorpay_order?: { id: string; amount: number; status: string };
  guardian_decision?: {
    decision: string;
    reason: string;
    risk_score: number;
  };
  message: string;
}

export default function CartPage() {
  return (
    <Suspense fallback={<CartSkeleton />}>
      <CartContent />
    </Suspense>
  );
}

function CartSkeleton() {
  return (
    <div className="min-h-screen bg-slate-50">
      <div className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <div className="h-6 bg-slate-200 rounded animate-pulse w-48" />
        </div>
      </div>
      <div className="container mx-auto px-4 py-8">
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-20 bg-slate-200 rounded-lg animate-pulse" />
          ))}
        </div>
      </div>
    </div>
  );
}

function CartContent() {
  const router = useRouter();
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [merchantId] = useState("m_test");
  const [buyerDid] = useState("did:example:buyer_demo");
  const [buyerKey, setBuyerKey] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("store_cart");
    if (saved) {
      setCart(JSON.parse(saved));
    }

    let key = localStorage.getItem("store_buyer_key");
    if (!key) {
      key = AP2Crypto.generatePrivateKey();
      localStorage.setItem("store_buyer_key", key);
    }
    setBuyerKey(key);
  }, []);

  const cartTotal = cart.reduce(
    (sum, item) => sum + item.base_price_paise * item.quantity,
    0
  );

  function updateQuantity(productId: string, newQty: number) {
    if (newQty < 1) return;
    const updated = cart.map((c) =>
      c.product_id === productId ? { ...c, quantity: newQty } : c
    );
    setCart(updated);
    localStorage.setItem("store_cart", JSON.stringify(updated));
  }

  function removeItem(productId: string) {
    const updated = cart.filter((c) => c.product_id !== productId);
    setCart(updated);
    localStorage.setItem("store_cart", JSON.stringify(updated));
  }

  async function checkout() {
    if (cart.length === 0) return;

    setLoading(true);
    const savedTotal = cartTotal;
    sessionStorage.setItem("checkout_total", String(savedTotal));

    try {
      const productIds = cart.map((c) => c.product_id);
      const quantities = cart.reduce(
        (acc, c) => ({ ...acc, [c.product_id]: c.quantity }),
        {} as Record<string, number>
      );

      const res = await api.post<CheckoutResponse>("/api/v1/store/checkout", {
        merchant_id: merchantId,
        buyer_did: buyerDid,
        product_ids: productIds,
        quantities,
        buyer_private_key: buyerKey,
      });

      const data = res.data;
      const url = new URL("/store/thanks", window.location.origin);
      url.searchParams.set("session_id", `checkout_${Date.now()}`);
      url.searchParams.set("success", String(data.success));
      url.searchParams.set("cart_mandate_id", data.cart_mandate_id || "");
      url.searchParams.set("guardian_decision", data.guardian_decision?.decision || "");
      url.searchParams.set("order_id", data.razorpay_order?.id || "");
      url.searchParams.set("message", data.message || "");

      router.push(url.toString().replace(window.location.origin, ""));
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      const url = new URL("/store/thanks", window.location.origin);
      url.searchParams.set("session_id", `checkout_${Date.now()}`);
      url.searchParams.set("success", "false");
      url.searchParams.set("message", msg);
      router.push(url.toString().replace(window.location.origin, ""));
    } finally {
      setLoading(false);
    }
  }

  if (cart.length === 0) {
    return (
      <div className="min-h-screen bg-slate-50">
        <header className="border-b bg-white shadow-sm">
          <div className="container mx-auto px-4 py-4">
            <Link href="/store" className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
              <ArrowLeft className="w-4 h-4" />
              Back to Store
            </Link>
          </div>
        </header>
        <div className="container mx-auto px-4 py-16 text-center">
          <ShoppingCart className="w-16 h-16 text-slate-300 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Your cart is empty</h2>
          <p className="text-slate-500 mb-6">No items have been added to your cart yet.</p>
          <Link
            href="/store"
            className="inline-flex items-center gap-2 px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700"
          >
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/store" className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
            <ArrowLeft className="w-4 h-4" />
            Back to Store
          </Link>
          <Link href="/store/cart" className="flex items-center gap-2 text-slate-900">
            <ShoppingCart className="w-5 h-5" />
            Cart
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-3xl">
        <h1 className="text-2xl font-bold text-slate-900 mb-6">Your Cart</h1>

        <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-slate-50 border-b">
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-700">Product</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-700">Price</th>
                <th className="text-center px-4 py-3 text-sm font-medium text-slate-700">Qty</th>
                <th className="text-right px-4 py-3 text-sm font-medium text-slate-700">Total</th>
                <th className="w-12 px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((item) => (
                <tr key={item.product_id} className="border-t">
                  <td className="px-4 py-3">
                    <span className="font-medium text-slate-900">{item.name}</span>
                  </td>
                  <td className="px-4 py-3 text-right text-sm text-slate-600">
                    {formatCurrency(item.base_price_paise)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <select
                      value={item.quantity}
                      onChange={(e) => updateQuantity(item.product_id, parseInt(e.target.value))}
                      className="w-14 px-2 py-1 border border-slate-200 rounded text-center text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-right text-sm font-medium text-slate-900">
                    {formatCurrency(item.base_price_paise * item.quantity)}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <button
                      onClick={() => removeItem(item.product_id)}
                      className="text-red-500 hover:text-red-700"
                      aria-label="Remove item"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Total + checkout */}
        <div className="mt-6 space-y-4">
          <div className="flex justify-between items-center py-4 border-t">
            <span className="text-sm text-slate-600">Subtotal</span>
            <span className="text-xl font-bold text-slate-900">{formatCurrency(cartTotal)}</span>
          </div>

          <button
            onClick={checkout}
            disabled={loading}
            className="w-full py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg font-medium hover:opacity-95 disabled:opacity-50 transition-opacity flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Processing checkout...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4" />
                Checkout with ShopBot (AP2)
              </>
            )}
          </button>
        </div>

        {/* Security note */}
        <div className="mt-4 flex items-center gap-2 text-xs text-slate-500">
          <Shield className="w-3 h-3" />
          <span>Your purchase will be validated by the Guardian Agent before payment is processed.</span>
        </div>
      </main>
    </div>
  );
}
