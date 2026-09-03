import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      <div className="container mx-auto px-4 py-16">
        <h1 className="text-5xl font-bold mb-4">Merchant-AI</h1>
        <p className="text-xl text-muted-foreground mb-8 max-w-2xl">
          Agentic commerce operating system for Razorpay merchants.
        </p>
        <Link href="/dashboard" className="inline-block bg-primary text-white px-6 py-3 rounded-lg font-medium hover:bg-primary/90 transition-colors">
          Open Dashboard →
        </Link>
      </div>
    </div>
  );
}
