export function LoadingIcon({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const sizeClass = {
    sm: "h-8 w-8",
    md: "h-12 w-12",
    lg: "h-16 w-16",
  }[size];

  return (
    <div className={`loading-icon relative ${sizeClass}`} aria-hidden="true">
      <span className="loading-icon-ring absolute inset-0 rounded-full" />
      <span className="loading-icon-orbit absolute inset-1 rounded-full" />
      <span className="loading-icon-core absolute left-1/2 top-1/2 rounded-full" />
    </div>
  );
}
