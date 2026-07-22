"use client";

import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { AlertCircle, Home, RefreshCw } from "lucide-react";
import Link from "next/link";
import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="min-h-[100dvh] bg-background text-foreground flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, ease: [0.32, 0.72, 0, 1] }}
        className="max-w-md w-full"
      >
        <div className="p-1.5 rounded-[2rem] bg-white/[0.03] ring-1 ring-white/5">
          <div className="rounded-[calc(2rem-0.375rem)] bg-card shadow-[inset_0_1px_1px_rgba(255,255,255,0.08)] p-10 text-center">
            {/* Error icon */}
            <div className="mb-6 flex justify-center">
              <div className="relative">
                <div className="absolute inset-0 bg-red-500/20 blur-2xl rounded-full" />
                <div className="relative flex h-16 w-16 items-center justify-center rounded-full bg-red-500/10 ring-1 ring-red-500/20">
                  <AlertCircle
                    className="h-8 w-8 text-red-400"
                    strokeWidth={1.5}
                  />
                </div>
              </div>
            </div>

            {/* Error code */}
            <div className="mb-3">
              <span className="text-6xl font-bold tracking-tight text-foreground/90">
                500
              </span>
            </div>

            {/* Error message */}
            <h2 className="text-lg font-semibold text-foreground/80 mb-2">
              Something went wrong
            </h2>
            <p className="text-sm text-muted-foreground/60 mb-8 max-w-sm mx-auto">
              An unexpected error occurred. Our team has been notified and
              we&apos;re working to fix it.
            </p>

            {/* Error details (if digest exists) */}
            {error.digest && (
              <div className="mb-6 px-4 py-2 rounded-full bg-white/[0.02] ring-1 ring-white/[0.06] inline-block">
                <code className="text-xs font-mono text-muted-foreground/50">
                  Error ID: {error.digest}
                </code>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Button onClick={reset} variant="secondary" className="gap-2">
                <RefreshCw className="h-4 w-4" />
                Try again
              </Button>
              <Link href="/">
                <Button variant="ghost" className="gap-2">
                  <Home className="h-4 w-4" />
                  Go home
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
