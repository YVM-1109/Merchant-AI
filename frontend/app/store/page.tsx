"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Package, ShoppingCart } from "lucide-react";
import Link from "next/link";

interface Product {
  product_id: string;
  name: string;
  description: string;
  base_price_paise: number;
  category: string;
  currency: string;
  total_stock: number;
  sales_velocity: number;
  is_active: boolean;
}

interface CartItem {
  product_id: string;
  name: string;
  base_price_paise: number;
  quantity: number;
}

export default function StorePage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<CartItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [merchantId] = useState("m_test");

  useEffect(() => {
    loadProducts();
    // Load persisted cart
    const saved = localStorage.getItem("store_cart");
    if (saved) setCart(JSON.parse(saved));
  }, []);

  async function loadProducts() {
    try {
      const res = await api.get(`/api/v1/store/products?merchant_id=${merchantId}`);
      setProducts(res.data);
    } catch (err) {
      console.error("Failed to load products:", err);
    } finally {
      setLoading(false);
    }
  }

  function addToCart(product: Product) {
    setCart((prev) => {
      const existing = prev.find((c) => c.product_id === product.product_id);
      let updated;
      if (existing) {
        updated = prev.map((c) =>
          c.product_id === product.product_id
            ? { ...c, quantity: c.quantity + 1 }
            : c
        );
      } else {
        updated = [...prev, {
          product_id: product.product_id,
          name: product.name,
          base_price_paise: product.base_price_paise,
          quantity: 1,
        }];
      }
      localStorage.setItem("store_cart", JSON.stringify(updated));
      return updated;
    });
  }

  const cartTotal = cart.reduce(
    (sum, item) => sum + item.base_price_paise * item.quantity,
    0
  );

  const cartItemCount = cart.reduce((sum, item) => sum + item.quantity, 0);

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="animate-pulse space-y-6">
          <div className="h-8 bg-muted rounded w-1/3" />
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-60 bg-muted rounded-lg" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold">Merchant Store</h1>
          <Link href="/store/cart" className="relative flex items-center gap-2">
            <ShoppingCart className="w-5 h-5" />
            <span className="hidden sm:inline">Cart ({cartItemCount})</span>
            {cartItemCount > 0 && (
              <span className="absolute -top-2 -right-2 bg-primary text-primary-foreground text-xs rounded-full w-5 h-5 flex items-center justify-center">
                {cartItemCount}
              </span>
            )}
          </Link>
        </div>
      </div>

      {/* Cart summary (compact) */}
      {cart.length > 0 && (
        <div className="bg-muted/20 border-b">
          <div className="container mx-auto px-4 py-2 text-sm">
            Cart total: <strong>{formatCurrency(cartTotal)}</strong> •{" "}
            <Link href="/store/cart" className="underline text-primary">
              View cart ({cartItemCount} items)
            </Link>
          </div>
        </div>
      )}

      {/* Product grid */}
      <div className="container mx-auto px-4 py-8">
        <h2 className="text-xl font-semibold mb-4">Products</h2>

        {products.length === 0 ? (
          <p className="text-muted-foreground">No products available.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((p) => (
              <div
                key={p.product_id}
                className="border rounded-lg p-4 bg-card hover:shadow-md transition-shadow"
              >
                <div className="aspect-square bg-muted rounded mb-3 flex items-center justify-center">
                  <Package className="w-8 h-8 text-muted-foreground" />
                </div>

                <h3 className="font-semibold">{p.name}</h3>
                <p className="text-sm text-muted-foreground line-clamp-2 mt-1">
                  {p.description}
                </p>

                <div className="mt-3 space-y-1">
                  <div className="flex justify-between text-sm">
                    <span>Price</span>
                    <span>{formatCurrency(p.base_price_paise)}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span>Stock</span>
                    <span>{p.total_stock > 0 ? `${p.total_stock} in stock` : "Out of stock"}</span>
                  </div>
                </div>

                <button
                  onClick={() => addToCart(p)}
                  disabled={p.total_stock === 0}
                  className="w-full mt-3 px-3 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 disabled:opacity-50 text-sm"
                >
                  Add to Cart
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
