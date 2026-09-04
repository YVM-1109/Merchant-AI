"use client";

import { useEffect, useState } from "react";
import { BarChart3, Shield, TrendingUp, Activity } from "lucide-react";
import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";

interface GuardianStats {
  approved: number;
  denied: number;
  escalated: number;
  total_actions: number;
  intervention_rate_pct: number;
  risk_distribution: { low: number; medium: number; high: number };
}

interface DailyTrend {
  date: string;
  revenue_paise: number;
  orders: number;
}

interface DashboardChartsProps {
  merchantId: string;
  days?: number;
}

export default function DashboardCharts({ merchantId, days = 30 }: DashboardChartsProps) {
  const [guardian, setGuardian] = useState<GuardianStats | null>(null);
  const [trend, setTrend] = useState<DailyTrend[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStats();
  }, [merchantId, days]);

  async function loadStats() {
    setLoading(true);
    try {
      const [guardianRes, trendRes] = await Promise.all([
        api.get(`/api/v1/analytics/guardian-stats/${merchantId}?days=${days}`),
        api.get(`/api/v1/analytics/daily-trend/${merchantId}?days=${days}`),
      ]);
      setGuardian(guardianRes.data);
      setTrend(trendRes.data);
    } catch (err) {
      console.error("Failed to load chart data:", err);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-64 bg-muted rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (!guardian) return null;

  const totalDecisions = guardian.approved + guardian.denied + guardian.escalated;
  const approvedPct = totalDecisions > 0 ? (guardian.approved / totalDecisions) * 100 : 0;
  const deniedPct = totalDecisions > 0 ? (guardian.denied / totalDecisions) * 100 : 0;
  const escalatedPct = totalDecisions > 0 ? (guardian.escalated / totalDecisions) * 100 : 0;

  const maxRisk = Math.max(guardian.risk_distribution.low, guardian.risk_distribution.medium, guardian.risk_distribution.high, 1);

  const maxRevenue = Math.max(...trend.map((d) => d.revenue_paise), 1);

  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {/* Guardian Decision Split */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield className="w-5 h-5 text-amber-500" />
          <h3 className="font-semibold">Guardian Decisions</h3>
        </div>
        <div className="space-y-3">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Approved</span>
              <span className="font-medium text-green-600">{approvedPct.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${approvedPct}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Denied</span>
              <span className="font-medium text-red-600">{deniedPct.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-red-500 transition-all"
                style={{ width: `${deniedPct}%` }}
              />
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Escalated</span>
              <span className="font-medium text-amber-600">{escalatedPct.toFixed(0)}%</span>
            </div>
            <div className="h-2 bg-muted rounded-full overflow-hidden">
              <div
                className="h-full bg-amber-500 transition-all"
                style={{ width: `${escalatedPct}%` }}
              />
            </div>
          </div>
        </div>
        <div className="mt-4 text-center text-sm text-muted-foreground">
          {totalDecisions} actions, {guardian.intervention_rate_pct}% intervention rate
        </div>
      </div>

      {/* Risk Distribution */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <Activity className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold">Risk Score Distribution</h3>
        </div>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Low risk</span>
              <span className="text-xs text-muted-foreground">{guardian.risk_distribution.low}</span>
            </div>
            <div className="h-6 bg-muted rounded-lg overflow-hidden">
              <div
                className="h-full bg-green-400 flex items-center justify-end px-2 transition-all"
                style={{ width: `${(guardian.risk_distribution.low / maxRisk) * 100}%` }}
              >
                {guardian.risk_distribution.low > 0 && (
                  <span className="text-xs font-medium text-green-900">{guardian.risk_distribution.low}</span>
                )}
              </div>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>Medium risk</span>
              <span className="text-xs text-muted-foreground">{guardian.risk_distribution.medium}</span>
            </div>
            <div className="h-6 bg-muted rounded-lg overflow-hidden">
              <div
                className="h-full bg-amber-400 flex items-center justify-end px-2 transition-all"
                style={{ width: `${(guardian.risk_distribution.medium / maxRisk) * 100}%` }}
              >
                {guardian.risk_distribution.medium > 0 && (
                  <span className="text-xs font-medium text-amber-900">{guardian.risk_distribution.medium}</span>
                )}
              </div>
            </div>
          </div>
          <div>
            <div className="flex justify-between text-sm mb-1">
              <span>High risk</span>
              <span className="text-xs text-muted-foreground">{guardian.risk_distribution.high}</span>
            </div>
            <div className="h-6 bg-muted rounded-lg overflow-hidden">
              <div
                className="h-full bg-red-400 flex items-center justify-end px-2 transition-all"
                style={{ width: `${(guardian.risk_distribution.high / maxRisk) * 100}%` }}
              >
                {guardian.risk_distribution.high > 0 && (
                  <span className="text-xs font-medium text-red-900">{guardian.risk_distribution.high}</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Daily Revenue Trend */}
      <div className="bg-card border border-border rounded-xl p-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="w-5 h-5 text-blue-500" />
          <h3 className="font-semibold">30-Day Revenue Trend</h3>
        </div>
        {trend.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No revenue data for this period
          </div>
        ) : (
          <div className="h-48 flex items-end justify-between gap-1">
            {trend.map((d) => (
              <div key={d.date} className="flex flex-col items-center flex-1 h-full justify-end">
                <div
                  className="w-full bg-indigo-500 rounded-t hover:bg-indigo-600 transition-colors relative group"
                  style={{
                    height: `${(d.revenue_paise / maxRevenue) * 100}%`,
                    minHeight: "2px",
                  }}
                >
                  <div
                    className="absolute -top-8 left-1/2 -translate-x-1/2 bg-popover border rounded px-1.5 py-0.5 text-xs opacity-0 group-hover:opacity-100 whitespace-nowrap"
                  >
                    {formatCurrency(d.revenue_paise)}
                  </div>
                </div>
                <span className="text-xs text-muted-foreground mt-1 rotate-45 origin-left">
                  {d.date.slice(5)}
                </span>
              </div>
            ))}
          </div>
        )}
        <div className="mt-4 text-center text-sm text-muted-foreground">
          {trend.reduce((sum, d) => sum + d.orders, 0)} orders across {trend.length} days
        </div>
      </div>
    </div>
  );
}
