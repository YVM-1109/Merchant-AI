"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { AP2Crypto } from "@/lib/ap2";
import { useState, useEffect } from "react";
import { ShoppingCart, Trash2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";

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
  const router = useRouter();
  const [cart, setCart] = useState<CartItem[]>([]);
  const [merchantId] = useState("m_test");
  const [buyerDid] = useState("did:example:buyer_demo");
  const [checkoutLoading, setCheckoutLoading] = useState(false);
  const [buyerKey, setBuyerKey] = useState("");

  useEffect(() => {
    const saved = localStorage.getItem("store_cart");
    if (saved) {
      setCart(JSON.parse(saved));
    }
    setBuyerKey(AP2Crypto.generatePrivateKey());
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

    setCheckoutLoading(true);
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
      url.searchParams.set("cart_mandate_id", data.cart_mandate_id);
      url.searchParams.set("guardian_decision", data.guardian_decision?.decision || "");
      url.searchParams.set("order_id", data.razorpay_order?.id || "");
      url.searchParams.set("message", data.message);

      router.push(url.toString().replace(window.location.origin, ""));
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message;
      const url = new URL("/store/thanks", window.location.origin);
      url.searchParams.set("session_id", `checkout_${Date.now()}`);
      url.searchParams.set("success", "false");
      url.searchParams.set("message", msg);
      router.push(url.toString().replace(window.location.origin, ""));
    } finally {
      setCheckoutLoading(false);
    }
  }

  if (cart.length === 0) {
    return (
      <div className="min-h-screen bg-background">
        <div className="border-b">
          <div className="container mx-auto px-4 py-4">
            <Link href="/store" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
              <ArrowLeft className="w-4 h-4" />
              Back to Store
            </Link>
          </div>
        </div>
        <div className="container mx-auto px-4 py-12 text-center">
          <ShoppingCart className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Your cart is empty</h2>
          <p className="text-muted-foreground mb-6">No items have been added to your cart yet.</p>
          <Link
            href="/store"
            className="inline-block px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
          >
            Browse Products
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/store" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-4 h-4" />
            Back to Store
          </Link>
          <Link href="/store/cart" className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5" />
            Cart
          </Link>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <h1 className="text-2xl font-bold mb-6">Shopping Cart</h1>

        <div className="border rounded-lg overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="bg-muted/20 text-left text-sm font-medium">
                <th className="px-4 py-3">Product</th>
                <th className="px-4 py-3">Price</th>
                <th className="px-4 py-3">Qty</th>
                <th className="px-4 py-3">Total</th>
                <th className="px-4 py-3 w-12"></th>
              </tr>
            </thead>
            <tbody>
              {cart.map((item) => (
                <tr key={item.product_id} className="border-t">
                  <td className="px-4 py-3">
                    <div className="font-medium">{item.name}</div>
                  </td>
                  <td className="px-4 py-3 text-sm">{formatCurrency(item.base_price_paise)}</td>
                  <td className="px-4 py-3">
                    <select
                      value={item.quantity}
                      onChange={(e) => updateQuantity(item.product_id, parseInt(e.target.value))}
                      className="border rounded px-2 py-1 w-16 text-center"
                    >
                      {[1, 2, 3, 4, 5, 6, 7, 8, 9, 10].map((n) => (
                        <option key={n} value={n}>{n}</option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3 text-sm font-medium">
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

        <div className="mt-6 space-y-3 text-right">
          <div className="flex justify-between text-lg">
            <span>Subtotal</span>
            <span>{formatCurrency(cartTotal)}</span>
          </div>
          <div className="border-t pt-3">
            <div className="flex justify-between text-xl font-bold">
              <span>Total</span>
              <span>{formatCurrency(cartTotal)}</span>
            </div>
          </div>
        </div>

        <button
          onClick={checkout}
          disabled={checkoutLoading}
          className="w-full mt-6 px-4 py-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 font-medium"
        >
          {checkoutLoading ? "Processing checkout..." : "Checkout with ShopBot"}
        </button>
      </div>
    </div>
  );
}
