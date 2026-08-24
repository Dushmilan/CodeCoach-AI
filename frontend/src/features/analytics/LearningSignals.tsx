"use client";
import { useEffect, useState } from "react";
import { AnalyticsService, AnalyticsSignal } from "./analytics.service";

export default function LearningSignals() {
  const [signals, setSignals] = useState<AnalyticsSignal[] | null>(null);
  useEffect(() => {
    AnalyticsService.getSignals().then(r => setSignals(r.signals)).catch(() => setSignals([]));
  }, []);
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
