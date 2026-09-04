"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import api from "@/lib/api";

interface Product {
  product_id?: string;
  name: string;
  description: string;
  base_price_paise: number;
  category: string;
  merchant_id: string;
  is_active: boolean;
}

export default function ProductEditorPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProductEditorContent />
    </Suspense>
  );
}

function ProductEditorContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const productId = searchParams.get("id");

  const [product, setProduct] = useState<Product>({
    name: "",
    description: "",
    base_price_paise: 0,
    category: "",
    merchant_id: "m_test",
    is_active: true,
  });

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (productId) {
      loadProduct(productId);
    }
  }, [productId]);

  async function loadProduct(id: string) {
    setLoading(true);
    try {
      const res = await api.get(`/api/v1/products/${id}`);
      setProduct(res.data);
    } catch (err) {
      console.error("Failed to load product:", err);
    } finally {
      setLoading(false);
    }
  }

  async function saveProduct() {
    setSaving(true);
    try {
      if (productId) {
        await api.put(`/api/v1/products/${productId}`, product);
      } else {
        await api.post(`/api/v1/products`, product);
      }
      router.push("/merchant/catalog");
    } catch (err) {
      console.error("Failed to save product:", err);
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="space-y-2">
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded" />
            <div className="h-10 bg-muted rounded w-3/4" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-2xl">
      <h1 className="text-2xl font-bold mb-6">
        {productId ? "Edit Product" : "New Product"}
      </h1>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium mb-1">Product Name</label>
          <input
            type="text"
            value={product.name}
            onChange={(e) => setProduct({ ...product, name: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder="Enter product name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Description</label>
          <textarea
            value={product.description}
            onChange={(e) => setProduct({ ...product, description: e.target.value })}
            className="w-full border rounded px-3 py-2"
            rows={3}
            placeholder="Enter product description"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Price (paise)</label>
          <input
            type="number"
            value={product.base_price_paise}
            onChange={(e) =>
              setProduct({ ...product, base_price_paise: parseInt(e.target.value) || 0 })
            }
            className="w-full border rounded px-3 py-2"
            placeholder="e.g., 9999 (₹99.99)"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Category</label>
          <input
            type="text"
            value={product.category}
            onChange={(e) => setProduct({ ...product, category: e.target.value })}
            className="w-full border rounded px-3 py-2"
            placeholder="e.g., electronics, books, clothing"
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-1">Merchant ID</label>
          <input
            type="text"
            value={product.merchant_id}
            onChange={(e) => setProduct({ ...product, merchant_id: e.target.value })}
            className="w-full border rounded px-3 py-2"
          />
        </div>

        <label className="flex items-center gap-2">
          <input
            type="checkbox"
            checked={product.is_active}
            onChange={(e) => setProduct({ ...product, is_active: e.target.checked })}
          />
          <span className="text-sm">Active</span>
        </label>
      </div>

      <div className="flex gap-4 mt-6">
        <button
          onClick={saveProduct}
          disabled={saving}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Product"}
        </button>
        <button
          onClick={() => router.push("/merchant/catalog")}
          className="px-4 py-2 border rounded-lg hover:bg-muted"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}