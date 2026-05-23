export function ShimmerText({ children, className = "" }: { children: string; className?: string }) {
  return <span className={`shimmer-text ${className}`}>{children}</span>;
}
