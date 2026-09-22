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
  md: "px-4 py-2 text-sm",
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
            className="block text-xs font-medium text-foreground tracking-wide"
          >
            {label}
          </label>
        )}
        <div
          className={cn(
            "rounded-full bg-muted/50 ring-1 ring-border transition-all duration-300",
            "focus-within:ring-ring/60",
            error && "ring-destructive/60",
          )}
        >
          <div className="flex items-center gap-2">
            {Icon && (
              <Icon
                className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0"
                aria-hidden="true"
              />
            )}
            <input
              id={inputId}
              ref={ref}
              className={cn(
                "w-full bg-transparent text-foreground placeholder:text-muted-foreground",
                "rounded-full focus:outline-none",
                sizeStyles[inputSize],
                className,
              )}
              {...props}
            />
          </div>
        </div>
        {error && <p className="text-[11px] text-destructive pl-1">{error}</p>}
      </div>
    );
  },
);
Input.displayName = "Input";

export { Input };
export type { InputProps };
