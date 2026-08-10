"use client";

import { motion } from "framer-motion";
import { CheckCircle2, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MissionCompleteOverlayProps {
  onStart: () => void;
  onSkip: () => void;
}

export function MissionCompleteOverlay({
  onStart,
  onSkip,
}: MissionCompleteOverlayProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
      <motion.div
        initial={{ opacity: 0, scale: 0.92, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.32, 0.72, 0, 1] }}
        className="bg-card border border-border rounded-3xl shadow-2xl max-w-md w-full mx-4 p-8 text-center space-y-6"
      >
        <motion.div
          initial={{ scale: 0.5, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ delay: 0.15, duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
          className="mx-auto w-16 h-16 rounded-full bg-emerald-500/10 flex items-center justify-center"
        >
          <CheckCircle2 className="h-8 w-8 text-emerald-400" strokeWidth={1.5} />
        </motion.div>

        <div className="space-y-1.5">
          <div className="text-[11px] font-semibold tracking-[0.25em] text-emerald-400/80 uppercase">
            Mission Complete
          </div>
          <h2 className="text-2xl font-semibold text-foreground">
            Your solution works.
          </h2>
          <p className="text-sm text-muted-foreground leading-relaxed">
            Now defend it. Your junior teammate is taking over this code
            tomorrow and has questions about how it works.
          </p>
        </div>

        <div className="space-y-2.5">
          <Button
            onClick={onStart}
            className="w-full gap-2"
            aria-label="Start debrief"
          >
            Start Debrief
            <ChevronRight className="h-4 w-4" />
          </Button>
          <Button
            onClick={onSkip}
            variant="ghost"
            className="w-full text-muted-foreground"
            aria-label="Skip debrief"
          >
            Skip for now
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
