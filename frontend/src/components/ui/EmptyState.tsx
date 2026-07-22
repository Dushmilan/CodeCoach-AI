"use client";

import { cn } from "@/lib/utils";
import { Button } from "./button";

interface EmptyStateProps {
  icon?: React.ElementType;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center p-8",
        className,
      )}
    >
      {Icon && (
        <Icon
          className="h-10 w-10 text-muted-foreground/20 mb-3"
          strokeWidth={1}
        />
      )}
      <h3 className="text-sm font-medium text-foreground/60 tracking-wide">
        {title}
      </h3>
      {description && (
        <p className="text-xs text-muted-foreground/40 mt-1 max-w-xs leading-relaxed">
          {description}
        </p>
      )}
      {actionLabel && onAction && (
        <Button variant="outline" size="sm" className="mt-4" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
