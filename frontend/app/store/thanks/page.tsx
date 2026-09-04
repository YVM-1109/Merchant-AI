"use client";

import { formatCurrency } from "@/lib/utils";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle, Shield, Package, ShoppingCart } from "lucide-react";
import Link from "next/link";
import { Suspense } from "react";

export default function ThankYouPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ThankYouContent />
    </Suspense>
  );
}

function ThankYouContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderId = searchParams.get("order_id") || "N/A";
  const guardianDecision = searchParams.get("guardian_decision") || "approved";
  const success = searchParams.get("success") === "true";
  const message = searchParams.get("message") || "";
  const cartTotal = 0;

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto px-4 py-16 text-center max-w-2xl">
        {success ? (
          <>
            <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold mb-2">Order Confirmed!</h1>
            <p className="text-muted-foreground mb-6">
              Your purchase has been processed successfully.
            </p>
          </>
        ) : (
          <>
            <Package className="w-16 h-16 text-amber-500 mx-auto mb-4" />
            <h1 className="text-3xl font-bold mb-2">Order Could Not Be Processed</h1>
            <p className="text-muted-foreground mb-6">
              The Guardian Agent blocked this purchase. See the details below.
            </p>
          </>
        )}

        <div className="bg-card border rounded-lg p-6 mb-6">
          <div className="space-y-3 text-left">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Order ID</span>
              <span className="font-medium">{orderId}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total Amount</span>
              <span className="font-medium">{formatCurrency(cartTotal)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-muted-foreground">Guardian Decision</span>
              <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-sm font-medium ${
                guardianDecision === "approved"
                  ? "bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400"
                  : "bg-amber-100 text-amber-800 dark:bg-amber-900/20 dark:text-amber-400"
              }`}>
                <Shield className="w-3 h-3" />
                {guardianDecision}
              </span>
            </div>
          </div>
        </div>

        {message && (
          <div className="bg-muted/20 rounded-lg p-4 mb-6 text-sm">
            {message}
          </div>
        )}

        <Link
          href="/store"
          className="inline-flex items-center gap-2 px-6 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
        >
          <ShoppingCart className="w-4 h-4" />
          Continue Shopping
        </Link>
      </div>
    </div>
  );
}
