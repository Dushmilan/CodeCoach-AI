"use client";

import { motion } from "framer-motion";
import {
  Check,
  Flag,
  Lightbulb,
  Loader2,
  MessageSquare,
  Trophy,
  X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { DebriefReport } from "@/features/debrief/debrief.types";

interface DebriefReportViewProps {
  report: DebriefReport;
  loading: boolean;
  onClose: () => void;
}

type Exchange = DebriefReport["exchanges"][number];
type ExchangeStatus = "strong" | "mixed" | "needs-work" | "unassessed";

function hasAiFeedback(ex: Exchange): boolean {
  return (
    (ex.strengths?.length ?? 0) > 0 ||
    (ex.improvements?.length ?? 0) > 0 ||
    (ex.strongerAnswer?.length ?? 0) > 0
  );
}

function getExchangeStatus(ex: Exchange): ExchangeStatus {
  if (!hasAiFeedback(ex)) return "unassessed";
  const hasStrengths = (ex.strengths?.length ?? 0) > 0;
  const hasCritique =
    (ex.improvements?.length ?? 0) > 0 ||
    (ex.strongerAnswer?.length ?? 0) > 0;
  if (hasStrengths && hasCritique) return "mixed";
  if (hasStrengths) return "strong";
  return "needs-work";
}

const STATUS_BADGE: Record<ExchangeStatus, string> = {
  strong: "bg-emerald-400/10 text-emerald-400",
  mixed: "bg-sky-400/10 text-sky-400",
  "needs-work": "bg-amber-400/10 text-amber-400",
  unassessed: "bg-white/5 text-muted-foreground/60",
};

const STATUS_LABEL: Record<ExchangeStatus, string> = {
  strong: "Solid",
  mixed: "Good start",
  "needs-work": "Needs work",
  unassessed: "Not assessed",
};

function FeedbackList({
  items,
  dotClass,
}: {
  items: string[];
  dotClass: string;
}) {
  return (
    <ul className="space-y-1">
      {items.map((item) => (
        <li
          key={item}
          className="text-sm text-foreground/80 flex items-start gap-2"
        >
          <span
            className={`mt-1.5 w-1 h-1 rounded-full flex-shrink-0 ${dotClass}`}
          />
          {item}
        </li>
      ))}
    </ul>
  );
}

function AiFeedbackBlock({ ex }: { ex: Exchange }) {
  const heading = (
    <div className="flex items-center justify-between gap-2">
      <h4 className="text-[11px] font-semibold tracking-wider text-primary/70 uppercase flex items-center gap-1.5">
        <MessageSquare className="h-3.5 w-3.5" /> Milo&apos;s Feedback
      </h4>
      <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[9px] font-medium uppercase tracking-wider text-primary">
        AI review
      </span>
    </div>
  );

  if (!hasAiFeedback(ex)) {
    return (
      <div className="rounded-xl bg-white/[0.02] ring-1 ring-white/10 px-3 py-2.5 space-y-1.5">
        {heading}
        <p className="text-sm text-muted-foreground/60 italic">
          Milo couldn&apos;t assess this answer — add more detail next time to
          get specific coaching.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {heading}
      {ex.strengths?.length > 0 && (
        <div className="space-y-1.5">
          <h5 className="text-[11px] font-semibold tracking-wider text-emerald-400/80 uppercase flex items-center gap-1.5">
            <Check className="h-3.5 w-3.5" /> Answered well
          </h5>
          <FeedbackList items={ex.strengths} dotClass="bg-emerald-400/70" />
        </div>
      )}

      {ex.improvements?.length > 0 && (
        <div className="space-y-1.5">
          <h5 className="text-[11px] font-semibold tracking-wider text-amber-400/80 uppercase flex items-center gap-1.5">
            <Flag className="h-3.5 w-3.5" /> What to improve
          </h5>
          <FeedbackList items={ex.improvements} dotClass="bg-amber-400/70" />
        </div>
      )}

      {ex.strongerAnswer?.length > 0 && (
        <div className="rounded-xl bg-primary/5 ring-1 ring-primary/10 px-3 py-2.5 space-y-1.5">
          <h5 className="text-[11px] font-semibold tracking-wider text-primary/70 uppercase">
            A stronger answer would include
          </h5>
          <FeedbackList items={ex.strongerAnswer} dotClass="bg-primary/70" />
        </div>
      )}
    </div>
  );
}

function ExchangeCard({ ex, index }: { ex: Exchange; index: number }) {
  const status = getExchangeStatus(ex);

  return (
    <section
      id={`debrief-exchange-${index}`}
      className="rounded-2xl bg-white/[0.03] ring-1 ring-white/5 p-4 space-y-4 scroll-mt-2"
    >
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-[11px] font-semibold tracking-wider text-primary/70 uppercase">
          Q{index + 1} — Your response
        </h3>
        <span
          className={`rounded-full px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${STATUS_BADGE[status]}`}
        >
          {STATUS_LABEL[status]}
        </span>
      </div>

      <div className="rounded-xl bg-white/[0.02] ring-1 ring-white/5 px-3 py-2.5 space-y-1">
        <p className="text-[10px] font-semibold tracking-wider text-muted-foreground/60 uppercase">
          Question
        </p>
        <p
          data-testid="debrief-question"
          className="text-sm text-foreground/90"
        >
          {ex.question}
        </p>
        <p className="text-sm text-muted-foreground/70 italic">
          &ldquo;{ex.answer}&rdquo;
        </p>
      </div>

      <AiFeedbackBlock ex={ex} />
    </section>
  );
}

export function DebriefReportView({
  report,
  loading,
  onClose,
}: DebriefReportViewProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const bodyRef = useRef<HTMLDivElement>(null);
  const [reviewIndex, setReviewIndex] = useState(1);

  const exchangeCount = report.exchanges.length;
  const totalForSkeleton = Math.max(exchangeCount, 3);

  useEffect(() => {
    const previousActive = document.activeElement as HTMLElement | null;
    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";
    panelRef.current?.focus();

    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !loading) onClose();
    };
    document.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
      previousActive?.focus();
    };
  }, [loading, onClose]);

  useEffect(() => {
    if (!loading) return;
    const id = setInterval(() => {
      setReviewIndex((prev) => (prev >= totalForSkeleton ? 1 : prev + 1));
    }, 1200);
    return () => clearInterval(id);
  }, [loading, totalForSkeleton]);

  const scrollToExchange = (index: number) => {
    document
      .getElementById(`debrief-exchange-${index}`)
      ?.scrollIntoView?.({ behavior: "smooth", block: "start" });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm p-4">
      <motion.div
        ref={panelRef}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-labelledby="debrief-report-title"
        initial={{ opacity: 0, scale: 0.95, y: 12 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.32, 0.72, 0, 1] }}
        className="bg-card border border-border rounded-3xl shadow-2xl w-full max-w-2xl max-h-[calc(100dvh-2rem)] sm:max-h-[85vh] flex flex-col overflow-hidden outline-none"
      >
        <div className="p-6 pb-4 border-b border-white/5 space-y-4">
          <div className="flex items-start justify-between gap-4">
            <div className="flex items-start gap-3">
              <motion.div
                initial={{ scale: 0.5, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{
                  delay: 0.1,
                  duration: 0.4,
                  ease: [0.32, 0.72, 0, 1],
                }}
                className="w-11 h-11 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0"
              >
                {loading ? (
                  <Loader2
                    className="h-5 w-5 text-primary animate-spin"
                    strokeWidth={1.5}
                  />
                ) : (
                  <Trophy
                    className="h-5 w-5 text-primary"
                    strokeWidth={1.5}
                  />
                )}
              </motion.div>
              <div>
                <div className="text-[11px] font-semibold tracking-[0.25em] text-primary/70 uppercase">
                  Mission Debrief
                </div>
                <h2
                  id="debrief-report-title"
                  className="text-xl font-semibold text-foreground mt-1"
                >
                  {loading ? "Assessing your answers…" : report.summary}
                </h2>
                {!loading && (
                  <p className="text-xs text-muted-foreground/60 mt-0.5">
                    {exchangeCount === 1
                      ? "1 exchange reviewed"
                      : `${exchangeCount} exchanges reviewed`}
                  </p>
                )}
              </div>
            </div>

            <button
              onClick={onClose}
              disabled={loading}
              className="p-1.5 hover:bg-white/5 rounded-full transition-colors disabled:opacity-40"
              aria-label="Close report"
            >
              <X className="h-4 w-4 text-muted-foreground/60" />
            </button>
          </div>

          {!loading && exchangeCount > 0 && (
            <div className="flex items-center gap-2 overflow-x-auto pb-1">
              <button
                onClick={() =>
                  bodyRef.current?.scrollTo?.({ top: 0, behavior: "smooth" })
                }
                className="rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-wider bg-white/[0.03] ring-1 ring-white/5 text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors flex-shrink-0"
              >
                Overview
              </button>
              {report.exchanges.map((_, idx) => (
                <button
                  key={idx}
                  onClick={() => scrollToExchange(idx)}
                  className="rounded-full px-3 py-1 text-[11px] font-medium uppercase tracking-wider bg-white/[0.03] ring-1 ring-white/5 text-muted-foreground hover:text-foreground hover:bg-white/5 transition-colors flex-shrink-0"
                >
                  Q{idx + 1}
                </button>
              ))}
            </div>
          )}
        </div>

        <div
          ref={bodyRef}
          className="flex-1 overflow-y-auto px-6 py-4 space-y-4"
        >
          {loading ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground/60">
                <Loader2 className="h-3.5 w-3.5 text-primary animate-spin" />
                <span>
                  Reviewing exchange {reviewIndex} of {totalForSkeleton}
                </span>
              </div>
              {[0, 1, 2].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="h-3 w-32 rounded bg-white/5 animate-pulse" />
                  <div className="h-24 rounded-2xl bg-white/[0.03] ring-1 ring-white/5 animate-pulse" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              {report.exchanges.map((ex, idx) => (
                <ExchangeCard key={idx} ex={ex} index={idx} />
              ))}
            </div>
          )}
        </div>

        <div className="p-6 pt-4 border-t border-white/5 space-y-4">
          {!loading && (
            <div className="rounded-2xl bg-primary/5 ring-1 ring-primary/10 px-4 py-3 flex items-start gap-2.5">
              <Lightbulb
                className="h-4 w-4 text-primary mt-0.5 flex-shrink-0"
                strokeWidth={1.5}
              />
              <p className="text-sm text-foreground/80 leading-relaxed">
                {report.takeaway}
              </p>
            </div>
          )}
          <Button
            onClick={onClose}
            className="w-full"
            aria-label="Continue learning"
            disabled={loading}
          >
            {loading ? "Generating…" : "Continue Learning"}
          </Button>
        </div>
      </motion.div>
    </div>
  );
}
