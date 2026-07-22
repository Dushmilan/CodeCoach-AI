import { cn } from "@/lib/utils";

interface BadgeProps {
  children: React.ReactNode;
  variant?:
    "easy" | "medium" | "hard" | "default" | "outline" | "success" | "warning";
  size?: "sm" | "md";
  className?: string;
}

const variantStyles: Record<string, string> = {
  easy: "text-green-400 bg-green-500/10 ring-green-500/20",
  medium: "text-yellow-400 bg-yellow-500/10 ring-yellow-500/20",
  hard: "text-red-400 bg-red-500/10 ring-red-500/20",
  default: "text-foreground/70 bg-white/[0.04] ring-white/[0.08]",
  outline:
    "text-muted-foreground/60 bg-transparent ring-white/[0.06] border border-white/[0.06]",
  success: "text-green-400 bg-green-500/10 ring-green-500/20",
  warning: "text-amber-400 bg-amber-500/10 ring-amber-500/20",
};

const sizeStyles: Record<string, string> = {
  sm: "text-[9px] px-1.5 py-0.5",
  md: "text-[10px] px-2 py-0.5",
};

export function Badge({
  children,
  variant = "default",
  size = "md",
  className,
}: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full font-medium uppercase tracking-wide ring-1",
        variantStyles[variant],
        sizeStyles[size],
        className,
      )}
    >
      {children}
    </span>
  );
}
