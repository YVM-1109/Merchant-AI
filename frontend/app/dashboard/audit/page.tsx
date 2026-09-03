"use client";

import api from "@/lib/api";
import { formatCurrency } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Shield, CheckCircle, AlertCircle, Clock } from "lucide-react";

interface AuditEntry {
  audit_id: string;
  action_type: string;
  amount: number;
  currency: string;
  status: string;
  reasoning: string;
  timestamp: string;
}

interface Summary {
  total_actions: number;
  approved: number;
  denied: number;
  by_action_type: Array<{
    _id: string;
    count: number;
    total_amount: number;
    approved: number;
    denied: number;
  }>;
}

export default function AuditPage() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [loading, setLoading] = useState(true);
  const [merchantId, setMerchantId] = useState("m_test");

  useEffect(() => {
    loadAuditTrail();
  }, [merchantId]);

  async function loadAuditTrail() {
    try {
      setLoading(true);
      const [entriesRes, summaryRes] = await Promise.all([
        api.get(`/api/v1/audit/recent/${merchantId}?limit=50`),
        api.get(`/api/v1/analytics/guardian-rate/${merchantId}?days=7`),
      ]);
      setEntries(entriesRes.data);
      setSummary({
        total_actions: summaryRes.data.total_actions,
        approved: summaryRes.data.approved,
        denied: summaryRes.data.denied,
        by_action_type: summaryRes.data.by_action_type || [],
      });
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2lx font-bold">Audit Trail</h1>
        <select
          value={merchantId}
          onChange={(e) => setMerchantId(e.target.value)}
          className="border rounded px-2 py-1"
        >
          <option value="m_test">m_test</option>
          <option value="m_test_electronics">m_test_electronics</option>
        </select>
      </div>

      {summary && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-card border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">{summary.total_actions}</div>
            <div className="text-sm text-muted-foreground">Total Actions</div>
          </div>
          <div className="bg-card border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-green-600">{summary.approved}</div>
            <div className="text-sm text-muted-foreground">Approved</div>
          </div>
          <div className="bg-card border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold text-red-600">{summary.denied}</div>
            <div className="text-sm text-muted-foreground">Denied</div>
          </div>
          <div className="bg-card border rounded-lg p-4 text-center">
            <div className="text-2xl font-bold">
              {summary.total_actions > 0
                ? `${((summary.denied / summary.total_actions) * 100).toFixed(1)}%`
                : "0%"}
            </div>
            <div className="text-sm text-muted-foreground">Guardian Rate</div>
          </div>
        </div>
      )}

      {loading && <div className="text-center py-8">Loading audit trail...</div>}
      {!loading && entries.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No audit entries yet.
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b">
              <th className="text-left py-2">Time</th>
              <th className="text-left py-2">Action</th>
              <th className="text-left py-2">Amount</th>
              <th className="text-left py-2">Status</th>
              <th className="text-left py-2">Reasoning</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.audit_id} className="border-b">
                <td className="py-2">
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="w-3 h-3" />
                    {new Date(entry.timestamp).toLocaleString()}
                  </div>
                </td>
                <td className="py-2 font-mono text-xs">
                  {entry.action_type}
                </td>
                <td className="py-2">
                  {formatCurrency(entry.amount)}
                </td>
                <td className="py-2">
                  {entry.status === "SUCCESS" ? (
                    <span className="flex items-center gap-1 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      {entry.status}
                    </span>
                  ) : (
                    <span className="flex items-center gap-1 text-red-600">
                      <AlertCircle className="w-4 h-4" />
                      {entry.status}
                    </span>
                  )}
                </td>
                <td className="py-2 text-xs text-muted-foreground max-w-xs truncate">
                  {entry.reasoning || "N/A"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
