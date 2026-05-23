import Link from "next/link";
import type { ReactNode } from "react";
import { MobileNavLinks, SidebarNavLinks } from "@/components/NavLinks";

export function AppLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-80 border-r border-line/80 bg-vellum/82 px-5 py-6 shadow-[18px_0_50px_rgba(60,65,74,0.08)] backdrop-blur-xl lg:block">
        <Link href="/" className="research-card block overflow-hidden rounded-xl hover:border-blue-200">
          <div className="lab-strip h-2" />
          <div className="p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">ML Analytics</p>
            <h1 className="mt-2 text-xl font-semibold leading-6 text-ink">Churn Model Comparison</h1>
            <p className="mt-3 text-xs leading-5 text-muted">A model evaluation studio for TFT, NHiTS, and TabNet.</p>
          </div>
        </Link>

        <SidebarNavLinks />

        <div className="absolute bottom-6 left-5 right-5 overflow-hidden rounded-xl border border-apricot/40 bg-[#fff6e7]/88 shadow-soft">
          <div className="lab-strip h-2" />
          <div className="p-4">
            <p className="text-sm font-semibold text-ink">Demo dataset mode</p>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Uses a representative customer sample so the 14 GB source dataset stays outside the app runtime.
            </p>
          </div>
        </div>
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
