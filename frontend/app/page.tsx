import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <h1 className="text-5xl font-bold mb-4">Merchant-AI</h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl">
          Agentic commerce operating system for Razorpay merchants.
        </p>
        <div className="flex gap-4">
          <Link href="/merchant" className="inline-block bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors">
            Merchant Portal →
          </Link>
          <Link href="/store" className="inline-block border border-gray-300 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-muted transition-colors">
            Shop as Customer →
          </Link>
        </div>
      </div>
    </div>
  );
}