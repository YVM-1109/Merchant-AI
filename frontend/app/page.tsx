import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-24">
        <div className="max-w-3xl">
          <h1 className="text-5xl font-bold text-slate-900 mb-4">
            Merchant-AI
          </h1>
          <p className="text-xl text-slate-600 mb-8 max-w-2xl">
            Agentic commerce operating system for Razorpay merchants.
            Browse products as a customer or manage your store as a merchant.
          </p>
          <div className="flex flex-col sm:flex-row gap-4">
            <Link href="/merchant" className="inline-flex items-center justify-center px-6 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition-colors">
              Merchant Portal →
            </Link>
            <Link href="/store" className="inline-flex items-center justify-center px-6 py-3 border border-slate-300 text-slate-700 rounded-lg font-medium hover:bg-slate-100 transition-colors">
              Shop as Customer →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}