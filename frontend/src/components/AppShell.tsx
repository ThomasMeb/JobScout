"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import Logo from "@/components/Logo";
import { HomeIcon, SettingsIcon, CreditCardIcon, ShieldIcon, MenuIcon, CrossIcon, LogOutIcon } from "@/components/Icons";
import { createClient } from "@/lib/supabase-browser";

const NAV_LINKS = [
  { href: "/dashboard", label: "Tableau de bord", icon: HomeIcon },
  { href: "/dashboard/billing", label: "Abonnement", icon: CreditCardIcon },
  { href: "/dashboard/admin", label: "Admin", icon: ShieldIcon },
  { href: "/settings", label: "Paramètres", icon: SettingsIcon },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const pathname = usePathname();
  const supabase = createClient();

  async function handleLogout() {
    await supabase.auth.signOut();
    window.location.href = "/";
  }

  function isActive(href: string) {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href);
  }

  const navContent = (
    <>
      <div className="p-6">
        <Link href="/dashboard"><Logo size="md" /></Link>
      </div>
      <nav className="flex-1 px-3">
        {NAV_LINKS.map((link) => {
          const active = isActive(link.href);
          const IconComponent = link.icon;
          return (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setDrawerOpen(false)}
              className={`flex items-center gap-3 rounded px-3 py-2.5 text-sm font-medium transition-colors mb-1 ${
                active
                  ? "bg-amber/10 text-amber border-l-2 border-amber -ml-px"
                  : "text-text-secondary hover:text-text-primary hover:bg-surface-3"
              }`}
            >
              <IconComponent size={18} />
              {link.label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded px-3 py-2.5 text-sm text-text-muted hover:text-negative hover:bg-surface-3 transition-colors"
        >
          <LogOutIcon size={18} />
          Déconnexion
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen bg-surface-0">
      {/* Desktop sidebar */}
      <aside className="hidden md:flex md:w-60 md:flex-col md:fixed md:inset-y-0 bg-surface-2 border-r border-border">
        {navContent}
      </aside>

      {/* Mobile header */}
      <div className="fixed top-0 left-0 right-0 z-40 flex items-center justify-between border-b border-border bg-surface-1/80 backdrop-blur-lg px-4 py-3 md:hidden">
        <Link href="/dashboard"><Logo size="sm" /></Link>
        <button
          onClick={() => setDrawerOpen(!drawerOpen)}
          className="rounded p-2 text-text-secondary hover:text-text-primary hover:bg-surface-3 transition-colors"
          aria-label="Menu"
        >
          {drawerOpen ? <CrossIcon size={20} /> : <MenuIcon size={20} />}
        </button>
      </div>

      {/* Mobile drawer overlay */}
      {drawerOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/50 md:hidden" onClick={() => setDrawerOpen(false)} />
          <aside className="fixed inset-y-0 left-0 z-50 w-60 flex flex-col bg-surface-2 border-r border-border md:hidden" style={{ animation: "slide-in-left 0.2s ease-out" }}>
            {navContent}
          </aside>
        </>
      )}

      {/* Main content */}
      <main className="flex-1 md:ml-60 pt-16 md:pt-0">
        {children}
      </main>
    </div>
  );
}
