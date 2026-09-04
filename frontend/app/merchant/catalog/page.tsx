"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Package, Search, Plus } from "lucide-react";

interface Product {
  product_id: string;
  name: string;
  description: string;
  category: string;
  base_price_paise: number;
  currency: string;
  total_stock: number;
  sales_velocity: number;
}

interface Merchant {
  merchant_id: string;
  name: string;
  email: string;
}

export default function CatalogPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [selectedMerchant, setSelectedMerchant] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMerchants();
  }, []);

  useEffect(() => {
    if (selectedMerchant) {
      loadProducts();
    }
  }, [selectedMerchant, searchTerm]);

  async function loadMerchants() {
    try {
      const res = await api.get("/api/v1/merchants/");
      setMerchants(res.data);
      if (res.data.length > 0) setSelectedMerchant(res.data[0].merchant_id);
      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
    }
  }

  async function loadProducts() {
    if (!selectedMerchant) return;
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (searchTerm) params.set("search", searchTerm);
      const res = await api.get(`/api/v1/products/?merchant_id=${selectedMerchant}&${params}`);
      setProducts(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-4">
        <h1 className="text-2xl font-bold">Catalog</h1>
        <button
          onClick={() => (window.location.href = `/merchant/products/editor`)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          <Plus className="w-4 h-4" />
          Add Product
        </button>
      </div>

      <div className="mb-4">
        <select
          value={selectedMerchant}
          onChange={(e) => setSelectedMerchant(e.target.value)}
          className="border rounded px-3 py-1 mb-2"
        >
          <option value="">Select Merchant</option>
          {merchants.map((m) => (
            <option key={m.merchant_id} value={m.merchant_id}>
              {m.name}
            </option>
          ))}
        </select>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <input
            type="text"
            placeholder="Search products..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-3 py-2 border rounded-lg"
          />
        </div>
      </div>

      {loading && <div className="text-center py-8">Loading products...</div>}
      {!loading && products.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No products found. Add your first product to get started.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {products.map((p) => (
          <div key={p.product_id} className="border rounded-lg p-4 bg-card">
            <div className="flex justify-between items-start">
              <h3 className="font-semibold">{p.name}</h3>
              <Package className="w-4 h-4 text-muted-foreground" />
            </div>
            <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
              {p.description}
            </p>
            <div className="mt-3 space-y-1">
              <div className="flex justify-between">
                <span className="text-sm">Price</span>
                <span className="font-medium">{formatCurrency(p.base_price_paise)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Stock</span>
                <span>{p.total_stock > 0 ? `${p.total_stock} units` : "Out of stock"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Sales Velocity</span>
                <span className="text-muted-foreground">{p.sales_velocity.toFixed(1)}/day</span>
              </div>
            </div>
            <button
              onClick={() => {
                window.location.href = `/merchant/products/editor?id=${p.product_id}`;
              }}
              className="w-full mt-3 px-3 py-1 text-sm border rounded hover:bg-muted"
            >
              Edit
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
