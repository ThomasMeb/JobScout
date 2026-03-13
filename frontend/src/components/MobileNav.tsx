"use client";

import { useState } from "react";
import Link from "next/link";
import Logo from "@/components/Logo";
import { MenuIcon, CrossIcon } from "@/components/Icons";

const NAV_LINKS = [
  { href: "/dashboard", label: "Tableau de bord" },
  { href: "/dashboard/admin", label: "Admin" },
  { href: "/dashboard/billing", label: "Abonnement" },
  { href: "/settings", label: "Paramètres" },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="border-b border-border bg-surface-1">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/dashboard"><Logo size="sm" /></Link>

        {/* Desktop links */}
        <div className="hidden items-center gap-4 md:flex">
          {NAV_LINKS.filter((l) => l.href !== "/dashboard").map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Hamburger button */}
        <button
          onClick={() => setOpen(!open)}
          className="inline-flex items-center justify-center rounded p-2 text-text-secondary hover:bg-surface-3 hover:text-text-primary md:hidden transition-colors"
          aria-label="Menu"
        >
          {open ? <CrossIcon size={20} /> : <MenuIcon size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="border-t border-border px-4 pb-3 pt-2 md:hidden">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className="block rounded px-3 py-2 text-sm text-text-secondary hover:bg-surface-3 hover:text-text-primary transition-colors"
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
