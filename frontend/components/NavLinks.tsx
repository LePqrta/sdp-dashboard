"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

export const navItems = [
  { href: "/", label: "Overview", marker: "00" },
  { href: "/models", label: "Models", marker: "01" },
  { href: "/customers", label: "Cohort Desk", marker: "02" },
];

export function SidebarNavLinks({ collapsed = false }: { collapsed?: boolean }) {
  const pathname = usePathname();

  return (
    <nav className="mt-8 space-y-3">
      {navItems.map((item) => {
        const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
        return (
          <Link
            key={item.href}
            href={item.href}
            title={collapsed ? item.label : undefined}
            className={[
              "group flex items-center rounded-lg border px-3 py-3 text-sm font-semibold",
              collapsed ? "justify-center gap-0" : "gap-3",
              active
                ? "border-mint/60 bg-panel text-ink shadow-[0_14px_30px_rgba(47,125,120,0.13)]"
                : "border-transparent text-slate-600 hover:border-line hover:bg-panel/70 hover:text-ink",
            ].join(" ")}
          >
            <span
              className={[
                "grid h-9 w-9 place-items-center rounded-md text-xs",
                active
                  ? "bg-accent text-white"
                  : "bg-vellum text-slate-500 group-hover:bg-mint/20 group-hover:text-accent",
              ].join(" ")}
            >
              {item.marker}
            </span>
            <span className={collapsed ? "sr-only" : ""}>{item.label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function MobileNavLinks() {
  return (
    <nav className="flex gap-1">
      {navItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="rounded-md px-3 py-2 text-xs font-semibold text-slate-600 hover:bg-mint/10"
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}
