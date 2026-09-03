"use client";

import api from "@/lib/api";
import { useEffect, useState } from "react";
import { Store, Settings, ExternalLink } from "lucide-react";

interface Merchant {
  merchant_id: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  razorpay_account_id: string;
  is_verified: boolean;
}

export default function MerchantsPage() {
  const [merchants, setMerchants] = useState<Merchant[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadMerchants();
  }, []);

  async function loadMerchants() {
    try {
      const res = await api.get("/api/v1/merchants/");
      setMerchants(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">Merchants</h1>
        <button
          onClick={() => (window.location.href = "/dashboard/merchants/editor")}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90"
        >
          Add Merchant
        </button>
      </div>

      {loading && <div className="text-center py-8">Loading merchants...</div>}
      {!loading && merchants.length === 0 && (
        <div className="text-center py-8 text-muted-foreground">
          No merchants yet. Add your first merchant to get started.
        </div>
      )}

      <div className="space-y-4">
        {merchants.map((m) => (
          <div key={m.merchant_id} className="border rounded-lg p-4 bg-card">
            <div className="flex justify-between items-start">
              <div>
                <h3 className="font-semibold text-lg">{m.name}</h3>
                <p className="text-sm text-muted-foreground">{m.email}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => {
                    window.location.href = `/dashboard/merchants/editor?id=${m.merchant_id}`;
                  }}
                  className="p-2 border rounded hover:bg-muted"
                  title="Edit"
                >
                  <Settings className="w-4 h-4" />
                </button>
                {m.razorpay_account_id && (
                  <a
                    href={`https://dashboard.razorpay.com/${m.razorpay_account_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="p-2 border rounded hover:bg-muted"
                    title="Open Razorpay Dashboard"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <div>
                <span className="text-sm text-muted-foreground">Phone</span>
                <p className="text-sm">{m.phone || "N/A"}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Verified</span>
                <span
                  className={
                    m.is_verified
                      ? "text-green-600"
                      : "text-amber-600"
                  }
                >
                  {m.is_verified ? "Yes" : "Pending"}
                </span>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Razorpay ID</span>
                <p className="text-sm font-mono">{m.razorpay_account_id}</p>
              </div>
              <div>
                <span className="text-sm text-muted-foreground">Address</span>
                <p className="text-sm">{m.address || "N/A"}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
