"use client";

import { useEffect, useState } from "react";

export function SlowLoadingNotice({
  delayMs = 2500,
  message = "This is taking longer than usual. The request is still running.",
}: {
  delayMs?: number;
  message?: string;
}) {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => setVisible(true), delayMs);
    return () => window.clearTimeout(timer);
  }, [delayMs]);

  if (!visible) return null;

  return (
    <div className="mt-4 rounded-xl border border-apricot/50 bg-[#fff6e7] p-4 text-sm leading-6 text-[#7a4a12]">
      {message}
    </div>
  );
}
