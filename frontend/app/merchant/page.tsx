"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useState } from "react";
import {
  BarChart3, Package, TrendingUp, Shield, Bot,
} from "lucide-react";
import NavigationToggle from "@/components/NavigationToggle";

interface DashboardStats {
  revenue: {
    total_revenue_paise: number;
    order_count: number;
    avg_order_value_paise: number;
  };
  guardian: {
    total_actions: number;
    approved: number;
    denied: number;
    intervention_rate_pct: number;
  };
  daily_trend: Array<{ date: string; revenue_paise: number; orders: number }>;
}

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [merchantId, setMerchantId] = useState("m_test");

  useEffect(() => {
    loadDashboard();
  }, [merchantId]);

  async function loadDashboard() {
    try {
      setLoading(true);
      const res = await api.get(`/api/v1/analytics/dashboard/${merchantId}?days=30`);
      setStats(res.data);
    } catch (err) {
      console.error("Failed to load dashboard:", err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/4" />
          <div className="grid grid-cols-3 gap-4">
            {[...Array(6)].map((_, i) => (
              <div key={i} className="h-24 bg-muted rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <h3 className="text-lg font-semibold mb-2">No data yet</h3>
        <p className="text-muted-foreground">Start by adding products and processing orders.</p>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold">Dashboard</h1>
          <NavigationToggle />
        </div>
        <select
          value={merchantId}
          onChange={(e) => setMerchantId(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="m_test">m_test</option>
          <option value="m_test_electronics">m_test_electronics</option>
        </select>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <BarChart3 className="w-4 h-4" />
            Total Revenue
          </div>
          <div className="text-2xl font-bold mt-1">
            {formatCurrency(stats.revenue.total_revenue_paise || 0)}
          </div>
          <div className="text-sm text-muted-foreground">
            {stats.revenue.order_count || 0} orders
          </div>
        </div>

        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Package className="w-4 h-4" />
            Avg Order Value
          </div>
          <div className="text-2xl font-bold mt-1">
            {formatCurrency(stats.revenue.avg_order_value_paise || 0)}
          </div>
        </div>

        <div className="bg-card border rounded-lg p-4">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Shield className="w-4 h-4" />
            Guardian Interception
          </div>
          <div className="text-2xl font-bold mt-1">
            {stats.guardian.intervention_rate_pct || 0}%
          </div>
          <div className="text-sm text-muted-foreground">
            {stats.guardian.denied || 0} denied / {stats.guardian.total_actions || 0} total
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="flex gap-4">
        <button
          onClick={() => (window.location.href = "/demo/shopbot")}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          <Bot className="w-4 h-4" />
          ShopBot Demo
        </button>
        <button
          onClick={() => (window.location.href = "/merchant/catalog")}
          className="flex items-center gap-2 px-4 py-2 border rounded-lg hover:bg-muted"
        >
          <Package className="w-4 h-4" />
          Catalog
        </button>
      </div>
    </div>
  );
}
