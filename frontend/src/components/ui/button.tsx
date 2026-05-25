import * as React from "react"
import { cn } from "@/lib/utils"

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link' | 'primary-pill'
  size?: 'default' | 'sm' | 'lg' | 'icon'
}

const variantStyles: Record<string, string> = {
  'default':
    'bg-primary text-primary-foreground hover:bg-primary/90 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]',
  'primary-pill':
    'rounded-full bg-primary text-primary-foreground hover:bg-primary/90 px-6 py-3 shadow-[inset_0_1px_0_rgba(255,255,255,0.15)]',
  'destructive':
    'bg-destructive text-destructive-foreground hover:bg-destructive/90',
  'outline':
    'border border-white/10 bg-white/5 hover:bg-white/10 hover:text-accent-foreground backdrop-blur-xl',
  'secondary':
    'bg-secondary text-secondary-foreground hover:bg-secondary/80',
  'ghost':
    'hover:bg-white/5 hover:text-accent-foreground',
  'link':
    'text-primary underline-offset-4 hover:underline',
}

const sizeStyles: Record<string, string> = {
  'default': 'h-10 px-5 py-2 rounded-full',
  'sm': 'h-9 px-4 rounded-full text-xs',
  'lg': 'h-12 px-8 rounded-full text-base',
  'icon': 'h-10 w-10 rounded-full',
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = 'default', size = 'default', ...props }, ref) => {
    return (
      <button
        className={cn(
          "inline-flex items-center justify-center whitespace-nowrap text-sm font-medium ring-offset-background transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
          variantStyles[variant] || variantStyles.default,
          sizeStyles[size] || sizeStyles.default,
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button }