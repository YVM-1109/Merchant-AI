import { ReactNode } from "react";
import Link from "next/link";
import { BarChart3, ShoppingCart, Package, Shield, Bot, Menu } from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Overview", icon: BarChart3 },
  { href: "/dashboard/catalog", label: "Catalog", icon: Package },
  { href: "/dashboard/merchants", label: "Merchants", icon: ShoppingCart },
  { href: "/dashboard/audit", label: "Audit", icon: Shield },
  { href: "/demo/shopbot", label: "ShopBot", icon: Bot },
];

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card p-4 space-y-2">
        <h2 className="text-xl font-bold mb-4">Merchant-AI</h2>
        <nav className="space-y-1">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="flex items-center gap-3 px-3 py-2 text-sm rounded-lg hover:bg-muted transition-colors">
              <item.icon className="w-4 h-4" />
              {item.label}
            </Link>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-auto">
        {children}
      </main>
    </div>
  );
}
