import { SlowLoadingNotice } from "@/components/SlowLoadingNotice";
import { LoadingIcon } from "@/components/LoadingIcon";

export function AppLoading({ label = "Preparing dashboard..." }: { label?: string }) {
  return (
    <div className="research-card mx-auto mt-10 max-w-3xl overflow-hidden rounded-2xl">
      <div className="lab-strip h-2" />
      <div className="p-6">
        <div className="flex items-center gap-4">
          <LoadingIcon />
          <div>
            <p className="text-sm font-semibold text-ink">{label}</p>
            <p className="mt-1 text-sm leading-6 text-muted">
              Loading the smallest possible page bundle first, then attaching charts and API data.
            </p>
          </div>
        </div>
        <div className="mt-5 h-2 overflow-hidden rounded-full bg-vellum">
          <div className="loading-bar h-full rounded-full bg-accent" />
        </div>
        <SlowLoadingNotice delayMs={1800} />
      </div>
    </div>
  );
}
