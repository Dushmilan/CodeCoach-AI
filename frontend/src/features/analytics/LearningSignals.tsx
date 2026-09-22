"use client";
import { useCallback, useEffect, useState } from "react";
import { AnalyticsService, AnalyticsSignal } from "./analytics.service";
import { QUESTION_SOLVED_EVENT } from "@/lib/solved-event";

export default function LearningSignals() {
  const [signals, setSignals] = useState<AnalyticsSignal[] | null>(null);
  const fetchSignals = useCallback(() => {
    AnalyticsService.getSignals().then(r => setSignals(r.signals)).catch(() => setSignals([]));
  }, []);
  useEffect(() => {
    fetchSignals();
  }, [fetchSignals]);
  // A solve changes pass/fail evidence — refetch on the solved event (#277).
  useEffect(() => {
    if (typeof window === "undefined") return;
    window.addEventListener(QUESTION_SOLVED_EVENT, fetchSignals);
    return () => window.removeEventListener(QUESTION_SOLVED_EVENT, fetchSignals);
  }, [fetchSignals]);
  if (signals === null) return <div data-testid="analytics-loading">Loading signals…</div>;
  if (signals.length === 0) return <div data-testid="analytics-empty">No learning signals — keep solving!</div>;
  return (
    <div data-testid="analytics-list" className="space-y-3">
      {signals.map(s => (
        <div key={s.skill} data-testid="analytics-signal" data-skill={s.skill} className="rounded-lg border p-3">
          <div className="font-medium">{s.title}</div>
          <div className="text-sm text-muted-foreground">{s.detail}</div>
        </div>
      ))}
    </div>
  );
}
