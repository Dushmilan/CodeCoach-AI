import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
  width?: string | number;
  height?: string | number;
  variant?: "text" | "circle" | "card" | "custom";
}

const variantStyles: Record<string, string> = {
  text: "h-4 w-full rounded-full",
  circle: "rounded-full",
  card: "rounded-3xl border border-white/[0.04] bg-white/[0.01] p-8",
  custom: "",
};

export function Skeleton({
  className,
  width,
  height,
  variant = "custom",
}: SkeletonProps) {
  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === "number" ? `${width}px` : width;
  if (height)
    style.height = typeof height === "number" ? `${height}px` : height;

  return (
    <div
      className={cn(
        "animate-pulse bg-white/[0.04]",
        variantStyles[variant],
        className,
      )}
      style={style}
      aria-hidden="true"
    />
  );
}
