"use client";

import Link from "next/link";
import type { ReactNode } from "react";
import { MobileNavLinks, SidebarNavLinks } from "@/components/NavLinks";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-80 border-r border-line/80 bg-vellum/82 px-5 py-6 shadow-[18px_0_50px_rgba(60,65,74,0.08)] backdrop-blur-xl lg:block">
        <Link
          href="/"
          className="research-card block overflow-hidden rounded-xl hover:border-blue-200"
          title="Churn Prediction"
        >
          <div className="lab-strip h-2" />
          <div className="p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">
              Churn Prediction
            </p>
          </div>
        </Link>

        <SidebarNavLinks />
      </aside>

      <div className="lg:pl-80">
        <header className="sticky top-0 z-10 border-b border-white/70 bg-vellum/86 px-4 py-3 backdrop-blur-xl lg:hidden">
          <div className="flex items-center justify-between gap-3">
            <Link href="/" className="text-sm font-semibold text-ink">
              Churn Dashboard
            </Link>
            <MobileNavLinks />
          </div>
        </header>

        <main className="mx-auto min-h-screen max-w-7xl px-4 py-8 sm:px-6 lg:px-8">{children}</main>
      </div>
    </div>
  );
}
