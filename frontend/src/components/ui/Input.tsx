import { cn } from "@/lib/utils";
import * as React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  icon?: React.ElementType;
  inputSize?: "sm" | "md" | "lg";
}

const sizeStyles: Record<string, string> = {
  sm: "px-3 py-1.5 text-xs",
  md: "px-3 py-2 text-sm",
  lg: "px-4 py-3 text-base",
};

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    { className, label, error, icon: Icon, inputSize = "md", id, ...props },
    ref,
  ) => {
    const inputId = id || label?.toLowerCase().replace(/\s+/g, "-");

    return (
      <div className="space-y-1.5">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-xs font-medium text-foreground/70 tracking-wide"
          >
            {label}
          </label>
        )}
        <div
          className={cn(
            "rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-0.5",
            "transition-all duration-300",
            "focus-within:ring-primary/40 focus-within:shadow-[0_0_0_1px_hsl(var(--primary)/0.2)]",
            error && "ring-red-500/40 focus-within:ring-red-500/60",
          )}
        >
          <div className="flex items-center gap-2">
            {Icon && (
              <Icon className="h-4 w-4 text-muted-foreground/40 ml-2 flex-shrink-0" />
            )}
            <input
              id={inputId}
              ref={ref}
              className={cn(
                "w-full bg-transparent text-foreground/80 placeholder:text-muted-foreground/40",
                "rounded-[calc(1rem-0.125rem)] focus:outline-none",
                sizeStyles[inputSize],
                className,
              )}
              {...props}
            />
          </div>
        </div>
        {error && <p className="text-[11px] text-red-400/80 pl-1">{error}</p>}
      </div>
    );
  },
);
Input.displayName = "Input";

export { Input };
export type { InputProps };
