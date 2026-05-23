import { LoadingIcon } from "@/components/LoadingIcon";

export function LoadingState({ label = "Loading dashboard data..." }: { label?: string }) {
  return (
    <div className="research-card rounded-2xl p-8 text-center">
      <div className="flex justify-center">
        <LoadingIcon />
      </div>
      <p className="mt-4 text-sm font-medium text-muted">{label}</p>
    </div>
  );
}
