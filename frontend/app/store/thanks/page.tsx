"use client";

import { formatCurrency } from "@/lib/utils";
import { useSearchParams } from "next/navigation";
import { CheckCircle, AlertCircle, Shield, ShoppingCart, Package } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

export default function ThankYouPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <ThankYouContent />
    </Suspense>
  );
}

function ThankYouContent() {
  const searchParams = useSearchParams();
  const orderId = searchParams.get("order_id") || "N/A";
  const guardianDecision = searchParams.get("guardian_decision") || "approved";
  const success = searchParams.get("success") === "true";
  const message = searchParams.get("message") || "";
  const cartTotalStr = sessionStorage.getItem("checkout_total") || "0";
  const cartTotal = parseInt(cartTotalStr, 10);

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="border-b bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <Link href="/store" className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
            <Package className="w-4 h-4" />
            Back to Store
          </Link>
        </div>
      </header>

      <main className="container mx-auto px-4 py-12 max-w-2xl">
        <div className="text-center mb-8">
          {success ? (
            <>
              <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <CheckCircle className="w-10 h-10 text-green-500" />
              </div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">Order Confirmed!</h1>
              <p className="text-slate-600">
                Your purchase has been processed successfully.
              </p>
            </>
          ) : (
            <>
              <div className="w-20 h-20 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <AlertCircle className="w-10 h-10 text-amber-500" />
              </div>
              <h1 className="text-3xl font-bold text-slate-900 mb-2">
                Order Could Not Be Processed
              </h1>
              <p className="text-slate-600">
                The Guardian Agent blocked this purchase.
              </p>
            </>
          )}
        </div>

        {/* Order details */}
        <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 mb-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">Order Details</h2>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-600">Order ID</span>
              <span className="font-medium text-slate-900 font-mono text-sm">{orderId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-600">Total Amount</span>
              <span className="font-medium text-slate-900">{formatCurrency(cartTotal)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-600">Guardian Decision</span>
              <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${
                guardianDecision === "approved"
                  ? "bg-green-100 text-green-700"
                  : "bg-amber-100 text-amber-700"
              }`}>
                <Shield className="w-3 h-3" />
                {guardianDecision === "approved" ? "Approved" : "Blocked"}
              </span>
            </div>
          </div>
        </div>

        {message && (
          <div className={`rounded-lg p-4 mb-6 text-sm ${
            success
              ? "bg-green-50 text-green-800 border border-green-200"
              : "bg-amber-50 text-amber-800 border border-amber-200"
          }`}>
            {success ? (
              <CheckCircle className="w-4 h-4 inline mr-2" />
            ) : (
              <AlertCircle className="w-4 h-4 inline mr-2" />
            )}
            {message}
          </div>
        )}

        <Link
          href="/store"
          className="flex items-center justify-center gap-2 px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 mx-auto w-full"
        >
          <ShoppingCart className="w-4 h-4" />
          Continue Shopping
        </Link>
      </main>
    </div>
  );
}
