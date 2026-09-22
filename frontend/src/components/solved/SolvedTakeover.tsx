"use client";

import { motion, useReducedMotion } from "framer-motion";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/Skeleton";
import { cn } from "@/lib/utils";

export type SolvedReplay =
  | { status: "loading" }
  | { status: "ready"; beats: string[] }
  | { status: "empty"; message?: string }
  | { status: "error"; message?: string };

interface SolvedTakeoverProps {
  open: boolean;
  onClose: () => void;
  questionTitle: string;
  difficulty: "easy" | "medium" | "hard";
  passed: number;
  total: number;
  replay: SolvedReplay;
  onNext: () => void;
  onRetry?: () => void;
}

export function SolvedTakeover({
  open,
  onClose,
  questionTitle,
  difficulty,
  passed,
  total,
  replay,
  onNext,
  onRetry,
}: SolvedTakeoverProps) {
  const reduce = useReducedMotion();

  return (
    <Dialog open={open} onOpenChange={(next) => { if (!next) onClose(); }}>
      <DialogContent className="w-[calc(100vw-2rem)] max-w-2xl rounded-xl">
        <motion.div
          initial={reduce ? false : { opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ type: "spring", stiffness: 120, damping: 20 }}
        >
          <DialogHeader>
            <div className="flex items-center gap-2">
              <Badge variant="success" size="sm">
                Solved
              </Badge>
              <Badge variant={difficulty} size="sm">
                {difficulty}
              </Badge>
            </div>
            <DialogTitle className="pt-2 text-xl font-semibold tracking-tight">
              {questionTitle}
            </DialogTitle>
            <DialogDescription>
              {`${passed} of ${total} passed. Nice work on the optimal path.`}
            </DialogDescription>
          </DialogHeader>

          <div className="mt-4 rounded-xl border border-border bg-white/[0.02] p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground/70">
              Optimal replay
            </p>
            {replay.status === "loading" && (
              <div role="status" aria-live="polite" className="mt-3 space-y-2">
                <Skeleton className="h-4 w-full rounded-full" />
                <Skeleton className="h-4 w-5/6 rounded-full" />
                <Skeleton className="h-4 w-4/6 rounded-full" />
              </div>
            )}
            {replay.status === "ready" && (
              <ol className="mt-3 space-y-2">
                {replay.beats.map((beat, i) => (
                  <li
                    key={`${i}-${beat}`}
                    className="rounded-xl bg-emerald-500/5 px-3 py-2 text-sm text-foreground/80 ring-1 ring-emerald-500/15"
                  >
                    {beat}
                  </li>
                ))}
              </ol>
            )}
            {replay.status === "empty" && (
              <p className="mt-3 text-sm text-muted-foreground">
                {replay.message || "Replay is not available for this one yet."}
              </p>
            )}
            {replay.status === "error" && (
              <div
                role="alert"
                className={cn(
                  "mt-3 flex items-center justify-between gap-2 rounded-xl",
                  "border border-destructive/25 bg-destructive/5 px-3 py-2.5",
                )}
              >
                <span className="text-xs text-destructive/90">
                  {replay.message || "Replay failed"}
                </span>
                <Button size="sm" variant="outline" onClick={onRetry}>
                  Try again
                </Button>
              </div>
            )}
          </div>

          <div className="mt-4 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
            <Button variant="ghost" onClick={onClose}>
              Stay here
            </Button>
            <Button onClick={onNext}>Next question</Button>
          </div>
        </motion.div>
      </DialogContent>
    </Dialog>
  );
}
