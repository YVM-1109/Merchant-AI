"use client";

import Link from "next/link";
import { Store, BarChart3 } from "lucide-react";

export default function NavigationToggle() {
  return (
    <div className="nav-toggle flex gap-2">
      <Link
        href="/store"
        className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-card hover:bg-muted transition-colors border border-border"
      >
        <Store className="w-4 h-4" />
        Customer View
      </Link>
      <Link
        href="/merchant"
        className="flex items-center gap-2 px-3 py-1.5 text-sm rounded-lg bg-card hover:bg-muted transition-colors border border-border"
      >
        <BarChart3 className="w-4 h-4" />
        Merchant View
      </Link>
    </div>
  );
}
