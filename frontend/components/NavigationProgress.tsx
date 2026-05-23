"use client";

import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

export function NavigationProgress() {
  const pathname = usePathname();
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    setVisible(true);
    const timer = window.setTimeout(() => setVisible(false), 650);
    return () => window.clearTimeout(timer);
  }, [pathname]);

  return (
    <div
      className={[
        "fixed left-0 right-0 top-0 z-50 h-1 overflow-hidden bg-transparent transition-opacity duration-200",
        visible ? "opacity-100" : "opacity-0",
      ].join(" ")}
      aria-hidden="true"
    >
      <div className="navigation-progress-bar h-full rounded-r-full bg-accent" />
    </div>
  );
}
