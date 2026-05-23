import type { ReactNode } from "react";

export function GlareCard({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`glare-card transition-transform duration-200 hover:-translate-y-1 ${className}`}>
      {children}
    </div>
  );
}
