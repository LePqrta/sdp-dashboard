"use client";

import { useEffect } from "react";
import { LoadingIcon } from "@/components/LoadingIcon";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="research-card mx-auto mt-10 max-w-3xl overflow-hidden rounded-2xl">
      <div className="lab-strip h-2" />
      <div className="p-6">
        <LoadingIcon />
        <h1 className="mt-5 text-2xl font-semibold text-ink">Dashboard view failed to load</h1>
        <p className="mt-2 text-sm leading-6 text-muted">
          This is usually a stale development cache. Try again, or restart with the clean dev command.
        </p>
        <button
          onClick={reset}
          className="mt-5 rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white hover:bg-[#256864]"
        >
          Try again
        </button>
      </div>
    </div>
  );
}
