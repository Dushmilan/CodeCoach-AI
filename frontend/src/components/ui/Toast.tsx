"use client";

import { cn } from "@/lib/utils";
import { CheckCircle, Info, X, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";

export type ToastVariant = "success" | "error" | "info";

interface ToastData {
  id: string;
  message: string;
  variant: ToastVariant;
}

const VARIANT_ICONS: Record<ToastVariant, typeof CheckCircle> = {
  success: CheckCircle,
  error: XCircle,
  info: Info,
};

const VARIANT_STYLES: Record<ToastVariant, string> = {
  success:
    "bg-green-500/10 text-green-400 ring-1 ring-green-500/20 shadow-[inset_0_1px_1px_rgba(34,197,94,0.15)]",
  error:
    "bg-destructive/10 text-red-400 ring-1 ring-destructive/20 shadow-[inset_0_1px_1px_rgba(239,68,68,0.15)]",
  info: "bg-white/[0.04] text-foreground/90 ring-1 ring-white/10 shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)]",
};

let toastListeners: Array<(toast: ToastData) => void> = [];
let toastId = 0;

export function showToast(message: string, variant: ToastVariant = "info") {
  const toast: ToastData = { id: `toast-${++toastId}`, message, variant };
  toastListeners.forEach((fn) => fn(toast));
}

export function useToast() {
  return { showToast };
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastData[]>([]);

  useEffect(() => {
    const listener = (toast: ToastData) => {
      setToasts((prev) => [...prev, toast]);
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== toast.id));
      }, 4000);
    };
    toastListeners.push(listener);
    return () => {
      toastListeners = toastListeners.filter((fn) => fn !== listener);
    };
  }, []);

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
      {toasts.map((toast) => {
        const Icon = VARIANT_ICONS[toast.variant];
        return (
          <div
            key={toast.id}
            className={cn(
              "flex items-center gap-2.5 px-4 py-3 rounded-2xl backdrop-blur-2xl shadow-lg animate-slide-in-right",
              VARIANT_STYLES[toast.variant],
            )}
          >
            <Icon className="h-4 w-4 shrink-0 opacity-80" />
            <span className="flex-1 text-sm font-medium tracking-tight">
              {toast.message}
            </span>
            <button
              onClick={() => dismiss(toast.id)}
              className="p-1 -mr-1 opacity-40 hover:opacity-100 hover:bg-white/5 rounded-full transition-all duration-500 ease-[cubic-bezier(0.32,0.72,0,1)]"
            >
              <X className="h-3 w-3" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
