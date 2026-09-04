"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Package, ShoppingCart, Star, Filter } from "lucide-react";
import Link from "next/link";
import NavigationToggle from "@/components/NavigationToggle";
import ShopBotWidget from "@/components/ShopBotWidget";

interface Product {
  product_id: string;
  name: string;
  description: string;
  base_price_paise: number;
  category: string;
  total_stock: number;
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
  const [showShopBotPrompt, setShowShopBotPrompt] = useState(false);

  useEffect(() => {
    loadProducts();
    const saved = localStorage.getItem("store_cart");
    if (saved) setCart(JSON.parse(saved));
  }, []);

  // Cart abandonment detection: trigger ShopBot after 30s idle with items in cart
  useEffect(() => {
    if (cart.length > 0) {
      const timer = setTimeout(() => {
        setShowShopBotPrompt(true);
      }, 30000);
      return () => clearTimeout(timer);
    }
  }, [cart]);

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
    const newItem: CartItem = {
      product_id: product.product_id,
      name: product.name,
      base_price_paise: product.base_price_paise,
      quantity: 1,
    };

    setCart((prev) => {
      const existing = prev.find((c) => c.product_id === product.product_id);
      const updated = existing
        ? prev.map((c) => c.product_id === product.product_id
            ? { ...c, quantity: c.quantity + 1 }
            : c)
        : [...prev, newItem];
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
      <div className="min-h-screen bg-slate-50">
        <header className="border-b bg-white">
          <div className="container mx-auto px-4 py-4 flex justify-between items-center">
            <div className="h-8 bg-muted rounded animate-pulse w-48" />
            <div className="h-10 bg-muted rounded animate-pulse w-24" />
          </div>
        </header>
        <main className="container mx-auto px-4 py-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {[...Array(8)].map((_, i) => (
              <div key={i} className="h-80 bg-muted rounded-xl animate-pulse" />
            ))}
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Link href="/" className="text-2xl font-bold text-slate-900">
              Merchant Store
            </Link>
            <nav className="hidden md:flex gap-6 text-sm text-slate-600">
              <Link href="/store" className="hover:text-slate-900">Home</Link>
              <button className="hover:text-slate-900">Categories</button>
            </nav>
          </div>

          {/* Portal navigation toggle */}
          <div className="hidden md:block">
            <NavigationToggle />
          </div>

          <Link href="/store/cart" className="relative">
            <div className="flex items-center gap-2 bg-slate-100 hover:bg-slate-200 text-slate-700 px-4 py-2 rounded-lg transition-colors">
              <ShoppingCart className="w-5 h-5" />
              <span>Cart</span>
              {cartItemCount > 0 && (
                <span className="absolute -top-2 -right-2 bg-indigo-600 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center">
                  {cartItemCount}
                </span>
              )}
            </div>
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="bg-gradient-to-br from-indigo-50 via-white to-slate-50 py-12">
        <div className="container mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 mb-4">
            Discover. Click. Checkout.
          </h1>
          <p className="text-slate-600 max-w-2xl mx-auto">
            Browse our curated catalog. Add items to your cart and let ShopBot handle the AP2 secure checkout.
          </p>
        </div>
      </section>

      {/* Cart summary */}
      {cart.length > 0 && (
        <div className="bg-white border-b py-3">
          <div className="container mx-auto px-4 text-sm text-slate-600">
            Cart total: <strong className="text-slate-900">{formatCurrency(cartTotal)}</strong>
            {" "}•{" "}
            <Link href="/store/cart" className="text-indigo-600 hover:text-indigo-700">
              View cart ({cartItemCount} {cartItemCount === 1 ? "item" : "items"})
            </Link>
          </div>
        </div>
      )}

      {/* Product grid */}
      <main className="container mx-auto px-4 py-12">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-slate-900">Products</h2>
          <button className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900">
            <Filter className="w-4 h-4" />
            Filter
          </button>
        </div>

        {products.length === 0 ? (
          <div className="text-center py-16">
            <Package className="w-12 h-12 text-slate-300 mx-auto mb-4" />
            <p className="text-slate-500">No products available at the moment.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {products.map((p) => (
              <div
                key={p.product_id}
                className="group bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                <div className="aspect-square bg-slate-100 flex items-center justify-center">
                  <Package className="w-10 h-10 text-slate-400 group-hover:scale-105 transition-transform" />
                </div>

                <div className="p-4">
                  <div className="flex items-start justify-between">
                    <h3 className="font-semibold text-slate-900">{p.name}</h3>
                    <div className="flex items-center gap-1 text-xs text-amber-500">
                      <Star className="w-3 h-3 fill-current" />
                      4.5
                    </div>
                  </div>

                  <p className="text-sm text-slate-500 mt-1 line-clamp-2">
                    {p.description}
                  </p>

                  <div className="mt-3 flex items-center justify-between">
                    <span className="font-bold text-lg text-slate-900">
                      {formatCurrency(p.base_price_paise)}
                    </span>
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      p.total_stock > 0
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}>
                      {p.total_stock > 0 ? `${p.total_stock} in stock` : "Out of stock"}
                    </span>
                  </div>

                  <button
                    onClick={() => addToCart(p)}
                    disabled={p.total_stock === 0}
                    className={`w-full mt-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      p.total_stock > 0
                        ? "bg-indigo-600 text-white hover:bg-indigo-700"
                        : "bg-slate-200 text-slate-400 cursor-not-allowed"
                    }`}
                  >
                    {p.total_stock > 0 ? "Add to Cart" : "Out of Stock"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* ShopBot floating widget with abandonment detection */}
      <ShopBotWidget
        merchantId={merchantId}
        buyerDid="did:example:buyer_demo"
        initialMessage={cart.length > 0 ? `I have ${cart.length} items in my cart. Can you help me check out?` : undefined}
        autoOpen={showShopBotPrompt}
      />
    </div>
  );
}
