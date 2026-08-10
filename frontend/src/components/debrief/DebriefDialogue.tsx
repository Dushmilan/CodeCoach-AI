"use client";

import { motion } from "framer-motion";
import { GraduationCap, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { DebriefContext } from "@/features/debrief/debrief.types";

interface DebriefDialogueProps {
  context: DebriefContext;
  currentQuestion: string;
  isTyping: boolean;
  round: number;
  totalRounds: number;
  isLastRound: boolean;
  onSubmitExplanation: (text: string) => Promise<void>;
  onNotSure: () => Promise<void>;
  onFinish: () => void | Promise<void>;
  onClose: () => void;
}

export function DebriefDialogue({
  context,
  currentQuestion,
  isTyping,
  round,
  totalRounds,
  isLastRound,
  onSubmitExplanation,
  onNotSure,
  onFinish,
  onClose,
}: DebriefDialogueProps) {
  const [answer, setAnswer] = useState("");
  const [sending, setSending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [currentQuestion, isTyping]);

  const handleSubmit = async () => {
    if (sending || isTyping || !answer.trim()) return;
    setSending(true);
    try {
      await onSubmitExplanation(answer);
      setAnswer("");
    } finally {
      setSending(false);
    }
  };

  const handleNotSure = async () => {
    if (sending || isTyping) return;
    setSending(true);
    try {
      await onNotSure();
      setAnswer("");
    } finally {
      setSending(false);
    }
  };

  const canAnswer = !isTyping && !sending;

  return (
    <div className="fixed inset-0 z-50 bg-background/90 backdrop-blur-sm overflow-y-auto">
      <div className="min-h-full flex flex-col max-w-3xl mx-auto px-4 py-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <div className="text-[11px] font-semibold tracking-[0.25em] text-primary/70 uppercase">
              Post-solve debrief
            </div>
            <h2 className="text-sm text-foreground/80 font-medium mt-0.5 truncate max-w-[70vw]">
              {context.problem}
            </h2>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-[11px] text-muted-foreground/60 tracking-wide">
              Question {Math.min(round + 1, totalRounds)} of {totalRounds}
            </span>
            <button
              onClick={onClose}
              className="p-1.5 hover:bg-white/5 rounded-full transition-colors"
              aria-label="Close debrief"
            >
              <X className="h-4 w-4 text-muted-foreground/60" />
            </button>
          </div>
        </div>

        {/* Progress rail */}
        <div className="h-1 bg-white/5 rounded-full overflow-hidden mb-6">
          <motion.div
            className="h-full bg-primary rounded-full"
            initial={{ width: 0 }}
            animate={{ width: `${(round / totalRounds) * 100}%` }}
            transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
          />
        </div>

        {/* Code panel */}
        <div className="rounded-2xl bg-[#0f172a] ring-1 ring-white/5 overflow-hidden mb-5">
          <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-400/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400/70" />
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400/70" />
            <span className="ml-2 text-[11px] text-slate-400/70 font-mono">
              {context.language} — your solution
            </span>
          </div>
          <pre className="px-4 py-3 text-[12px] leading-relaxed text-slate-300 font-mono overflow-x-auto max-h-48 overflow-y-auto whitespace-pre">
            {context.code || "// no code yet"}
          </pre>
        </div>

        {/* Dialogue stage */}
        <div className="flex-1 space-y-3">
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0 w-9 h-9 rounded-full bg-primary/10 flex items-center justify-center">
              <GraduationCap className="h-4 w-4 text-primary" strokeWidth={1.5} />
            </div>
            <div className="flex-1">
              <div className="flex items-baseline gap-2 mb-1">
                <span className="text-xs font-semibold text-foreground/80">
                  Milo, Junior Dev
                </span>
                {isTyping && (
                  <span className="text-[10px] text-muted-foreground/50 italic">
                    thinking…
                  </span>
                )}
              </div>
              <div className="bg-white/[0.04] ring-1 ring-white/5 rounded-2xl rounded-tl-sm px-4 py-3 text-sm text-foreground/80 leading-relaxed">
                {isTyping && !currentQuestion ? (
                  <span className="text-muted-foreground/60">
                    Give me a second to look over your code…
                  </span>
                ) : (
                  currentQuestion
                )}
              </div>
            </div>
          </div>

          <div ref={bottomRef} />
        </div>

        {/* Answer area */}
        <div className="mt-5 border-t border-white/5 pt-4 space-y-3">
          {isLastRound && !isTyping ? (
            <Button
              onClick={onFinish}
              className="w-full"
              aria-label="View debrief report"
            >
              View Debrief Report
            </Button>
          ) : (
            <>
              <textarea
                value={answer}
                onChange={(e) => setAnswer(e.target.value)}
                placeholder="Explain your approach to Milo — why did you write it this way?"
                disabled={!canAnswer}
                rows={3}
                className="w-full bg-white/[0.03] ring-1 ring-white/5 rounded-xl px-4 py-3 text-sm text-foreground/80 placeholder:text-muted-foreground/40 focus:outline-none focus:ring-white/[0.08] resize-none disabled:opacity-40 disabled:pointer-events-none transition-all"
              />
              <div className="flex gap-2">
                <Button
                  onClick={handleSubmit}
                  disabled={!canAnswer || !answer.trim()}
                  className="flex-1"
                >
                  Submit Explanation
                </Button>
                <Button
                  onClick={handleNotSure}
                  disabled={!canAnswer}
                  variant="ghost"
                  className="text-muted-foreground"
                >
                  I&apos;m not sure
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
